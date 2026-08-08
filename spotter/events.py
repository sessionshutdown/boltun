"""Детекторы ивентов.

Каждый детектор на вход получает текущий и предыдущий слепок телеметрии
и возвращает список событий. Состояние (взводы, предыдущие значения)
хранится внутри экземпляра детектора.

Новые ивенты добавляются: класс-детектор + варианты фраз в phrases.py +
регистрация в default_detectors().
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .phrases import format_phrase
from .snapshot import TelemetrySnapshot


@dataclass
class SpotterEvent:
    event_id: str
    message: str
    ts: float = 0.0
    priority: int = 0
    params: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.event_id}] {self.message}"


class Detector:
    name = "base"

    def check(self, snap: TelemetrySnapshot,
              prev: TelemetrySnapshot | None) -> list[SpotterEvent]:
        return []

    def _event(self, snap: TelemetrySnapshot, params: dict | None = None) -> SpotterEvent:
        return SpotterEvent(
            event_id=self.name,
            message=format_phrase(self.name, params),
            ts=snap.ts,
            params=params or {},
        )


class _BoolEdgeDetector(Detector):
    def __init__(self) -> None:
        self._prev: bool | None = None

    def _value(self, snap: TelemetrySnapshot) -> bool:
        raise NotImplementedError

    def _edge(self, snap: TelemetrySnapshot) -> str:
        value = self._value(snap)
        if self._prev is None:
            self._prev = value
            return ""
        edge = ""
        if value and not self._prev:
            edge = "on"
        elif not value and self._prev:
            edge = "off"
        self._prev = value
        return edge


class _SustainedStateDetector(Detector):
    """Срабатывает только когда состояние держится on_min_s секунд подряд
    и "отпускает" после off_min_s секунд нормального состояния.

    Защита от транзитных блупов (доля секунды езды не туда): alert не
    выскакивает и тут же не сменяется "всё ок", если проблема была
    мгновенной.
    """

    on_min_s = 1.0
    off_min_s = 1.0

    def __init__(self) -> None:
        self._on_time = 0.0
        self._off_time = 0.0
        self._announced = False

    def _value(self, snap: TelemetrySnapshot) -> bool:
        raise NotImplementedError

    def _on_event(self, snap: TelemetrySnapshot) -> SpotterEvent | None:
        return self._event(snap)

    def _off_event(self, snap: TelemetrySnapshot) -> SpotterEvent | None:
        return None

    def _dt(self, snap, prev) -> float:
        if prev is None or snap.ts <= prev.ts:
            return 1.0 / 60.0
        return snap.ts - prev.ts

    def check(self, snap, prev):
        dt = self._dt(snap, prev)
        out = []
        if self._value(snap):
            self._off_time = 0.0
            if not self._announced:
                self._on_time += dt
                if self._on_time >= self.on_min_s:
                    self._announced = True
                    event = self._on_event(snap)
                    if event is not None:
                        out.append(event)
        else:
            self._on_time = 0.0
            if self._announced:
                self._off_time += dt
                if self._off_time >= self.off_min_s:
                    self._announced = False
                    self._off_time = 0.0
                    event = self._off_event(snap)
                    if event is not None:
                        out.append(event)
        return out


class SessionStartDetector(Detector):
    name = "session_start"

    def __init__(self) -> None:
        self._fired = False

    def check(self, snap, prev):
        if self._fired:
            return []
        if snap.packet_id > 0:
            self._fired = True
            return [self._event(snap)]
        return []


class WeatherDetector(Detector):
    name = "weather"

    def __init__(self) -> None:
        self._fired = False

    def check(self, snap, prev):
        if self._fired or snap.packet_id <= 0:
            return []
        self._fired = True
        if snap.wiper > 0:
            event_id = "weather_wet"
        elif snap.air_temp >= 30.0:
            event_id = "weather_hot"
        elif snap.air_temp <= 10.0:
            event_id = "weather_cold"
        else:
            event_id = "weather_clear"
        return [SpotterEvent(
            event_id=event_id,
            message=format_phrase(event_id),
            ts=snap.ts,
        )]


class WrongWayDetector(_SustainedStateDetector):
    name = "wrong_way"
    on_min_s = 2.0    # ехать не туда минимум 2 секунды подряд
    off_min_s = 1.5   # нормально минимум 1.5 секунды, чтобы объявить "всё ок"

    def _value(self, snap):
        return snap.wrong_way

    def _off_event(self, snap):
        return SpotterEvent(
            event_id="wrong_way_clear",
            message=format_phrase("wrong_way_clear"),
            ts=snap.ts,
        )


class TrackLimitsDetector(_SustainedStateDetector):
    """Живой срез трассы: race_cut_gained_time_ms > 0, пока игрок не отдал
    выигранное время (500 м после среза) или не получил штраф. Срабатывает
    с удержанием, повторный срез объявляется заново после off_min_s чистой
    езды. Явного "всё ок" не говорим - тихое снятие тоже важный сигнал.
    """

    name = "track_limits"
    on_min_s = 1.0    # срез минимум 1 секунду, чтобы объявить
    off_min_s = 1.5   # чисто минимум 1.5 секунды, чтобы перевзвести

    def _value(self, snap):
        return snap.race_cut_gained_time_ms > 0


class PitLimiterDetector(_BoolEdgeDetector):
    name = "pit_limiter_on"

    def _value(self, snap):
        return snap.pit_limiter

    def check(self, snap, prev):
        edge = self._edge(snap)
        if edge == "on":
            return [self._event(snap)]
        if edge == "off":
            return [SpotterEvent(
                event_id="pit_limiter_off",
                message=format_phrase("pit_limiter_off"),
                ts=snap.ts,
            )]
        return []


class FuelDetector(Detector):
    name = "fuel_low"
    low_threshold = 15.0
    critical_threshold = 5.0

    def __init__(self) -> None:
        self._low_fired = False
        self._crit_fired = False

    def check(self, snap, prev):
        out = []
        if not self._low_fired and snap.fuel_percent < self.low_threshold:
            self._low_fired = True
            out.append(self._event(snap))
        if not self._crit_fired and snap.fuel_percent < self.critical_threshold:
            self._crit_fired = True
            out.append(SpotterEvent(
                event_id="fuel_critical",
                message=format_phrase("fuel_critical"),
                ts=snap.ts,
            ))
        return out


class FuelLapsDetector(Detector):
    """Информация о том, на сколько кругов хватит топлива.

    Срабатывает при пересечении отметок 10/5/3/2/1 круг (laps_possible_
    with_fuel из телеметрии). Каждая отметка - один раз. Если за один
    тик проскочено несколько отметок (скачок значения), озвучивается
    только самая поздняя, остальные помечаются озвученными - без спама.
    """

    name = "fuel_laps"
    thresholds = (10.0, 5.0, 3.0, 2.0, 1.0)

    def __init__(self) -> None:
        self._announced: set[float] = set()

    def check(self, snap, prev):
        laps = float(snap.laps_possible_with_fuel)
        if not (laps > 0.0) or laps > 1000.0:
            return []
        crossed = [th for th in self.thresholds
                   if laps < th and th not in self._announced]
        if not crossed:
            return []
        target = min(crossed)
        self._announced.add(target)
        self._announced.update(th for th in crossed if th > target)
        event_id = f"fuel_laps_{int(target)}"
        return [SpotterEvent(
            event_id=event_id,
            message=format_phrase(event_id),
            ts=snap.ts,
        )]


class CrashDetector(Detector):
    name = "crash"
    accel_threshold = -14.0

    def check(self, snap, prev):
        if prev is None:
            return []
        if snap.acc_long < self.accel_threshold and snap.brake < 0.5:
            return [self._event(snap)]
        return []


class DamageReportDetector(Detector):
    """Сообщает о новых повреждениях кузова/подвески.

    Срабатывает на прирост повреждений по зонам (порог на зону):
    front/rear/left/right/center/suspension. Каждая зона сообщается
    один раз за "инцидент" - повторное сообщение только при новом
    заметном приросте урона.
    """

    name = "damage_report"
    zones = ("front", "rear", "left", "right", "center", "suspension")
    min_delta = {
        "front": 20.0,
        "rear": 20.0,
        "left": 20.0,
        "right": 20.0,
        "center": 20.0,
        "suspension": 15.0,
    }

    def __init__(self) -> None:
        self._reported: dict[str, float] = {}

    def check(self, snap, prev):
        out = []
        for zone in self.zones:
            value = float(getattr(snap, f"damage_{zone}"))
            reported = self._reported.get(zone)
            if reported is None:
                self._reported[zone] = value
                continue
            if value - reported >= self.min_delta[zone]:
                self._reported[zone] = value
                event_id = f"damage_{zone}"
                out.append(SpotterEvent(
                    event_id=event_id,
                    message=format_phrase(event_id),
                    ts=snap.ts,
                ))
        return out


class SpinDetector(_SustainedStateDetector):
    name = "spin"
    yaw_threshold = 1.5
    on_min_s = 0.8    # крутиться минимум 0.8 сек, чтобы объявить разворот
    off_min_s = 1.0

    def _value(self, snap):
        return abs(snap.yaw_rate) > self.yaw_threshold


class LapCompletedDetector(Detector):
    """Фиксирует завершение круга по смене last_laptime_ms.

    Старая эвристика (обёртка current_km) давала ложные "Nice lap" при
    выходе из заезда, когда километраж сбрасывался/перескакивал.
    last_laptime_ms меняется только при реальном пересечении финишной
    черты, а is_valid_lap говорит о валидности круга.
    """

    name = "lap_completed"

    def __init__(self) -> None:
        self._prev_last_lap_ms: int | None = None

    def check(self, snap, prev):
        last = int(snap.last_lap_ms)
        if self._prev_last_lap_ms is None:
            self._prev_last_lap_ms = last
            return []
        if last == self._prev_last_lap_ms:
            return []
        previous = self._prev_last_lap_ms
        self._prev_last_lap_ms = last
        if last <= 0 or previous <= 0:
            return []
        if snap.is_valid_lap:
            return [SpotterEvent(
                event_id="lap_completed",
                message=format_phrase("lap_completed"),
                ts=snap.ts,
            )]
        return [SpotterEvent(
            event_id="lap_invalidated",
            message=format_phrase("lap_invalidated"),
            ts=snap.ts,
        )]


class PaceDetector(Detector):
    """Темп по завершённому кругу: срабатывает на смену last_laptime_ms.

    Мёртвая зона ±1.5 с - пока круг в её пределах, ничего не говорим
    (не спамим). За её пределами:
        last == best          -> new_best_lap
        last заметно медленнее -> lap_pace_loss
        last заметно быстрее   -> lap_pace_gain
    """

    name = "pace"
    off_ms = 1500

    def __init__(self) -> None:
        self._prev_last_lap_ms: int | None = None

    def check(self, snap, prev):
        last = int(snap.last_lap_ms)
        if self._prev_last_lap_ms is None:
            self._prev_last_lap_ms = last
            return []
        if last == self._prev_last_lap_ms:
            return []
        self._prev_last_lap_ms = last
        best = int(snap.best_lap_ms)
        if last <= 0 or best <= 0:
            return []
        if last == best:
            return [SpotterEvent(
                event_id="new_best_lap",
                message=format_phrase("new_best_lap"),
                ts=snap.ts,
            )]
        delta = last - best
        if delta > self.off_ms:
            event_id = "lap_pace_loss"
        elif delta < -self.off_ms:
            event_id = "lap_pace_gain"
        else:
            return []
        return [SpotterEvent(
            event_id=event_id,
            message=format_phrase(event_id),
            ts=snap.ts,
        )]


class _LiveDeltaDetector(_SustainedStateDetector):
    """Живая дельта vs референс (delta_time_ms, + = теряешь, - = набираешь).

    Требует, чтобы дельта держалась за пределами мёртвой зоны on_min_s
    секунд подряд (иначе мгновенные всплески не озвучиваются), плюс
    длинный cooldown в EVENT_COOLDOWNS - чтобы не сыпать каждую секунду.
    """

    off_ms = 1500
    on_min_s = 2.0
    off_min_s = 1.5


class LiveDeltaGainDetector(_LiveDeltaDetector):
    name = "pace_gain_live"

    def _value(self, snap):
        return snap.delta_time_ms < -self.off_ms


class LiveDeltaLossDetector(_LiveDeltaDetector):
    name = "pace_loss_live"

    def _value(self, snap):
        return snap.delta_time_ms > self.off_ms


def default_detectors() -> list[Detector]:
    return [
        SessionStartDetector(),
        WeatherDetector(),
        WrongWayDetector(),
        TrackLimitsDetector(),
        PitLimiterDetector(),
        FuelDetector(),
        FuelLapsDetector(),
        CrashDetector(),
        DamageReportDetector(),
        SpinDetector(),
        LiveDeltaGainDetector(),
        LiveDeltaLossDetector(),
        LapCompletedDetector(),
        PaceDetector(),
    ]


# Per-event cooldown in seconds: how long the same event is silenced after
# firing. Events that legitimately can (and should) fire repeatedly get a
# short or zero cooldown; events with noisy signals (crash/spin) get a
# longer one so a single incident doesn't spam.
# Engine falls back to the CLI --cooldown value for events not listed here.
EVENT_COOLDOWNS: dict[str, float] = {
    "session_start": 0.0,
    "weather_clear": 0.0,
    "weather_hot": 0.0,
    "weather_cold": 0.0,
    "weather_wet": 0.0,
    "wrong_way": 5.0,
    "wrong_way_clear": 0.0,
    "track_limits": 5.0,
    "pit_limiter_on": 2.0,
    "pit_limiter_off": 2.0,
    "fuel_low": 0.0,
    "fuel_critical": 0.0,
    "crash": 8.0,
    "spin": 8.0,
    "lap_completed": 0.0,
    "lap_invalidated": 0.0,
    "damage_front": 20.0,
    "damage_rear": 20.0,
    "damage_left": 20.0,
    "damage_right": 20.0,
    "damage_center": 20.0,
    "damage_suspension": 20.0,
    "fuel_laps_10": 0.0,
    "fuel_laps_5": 0.0,
    "fuel_laps_3": 0.0,
    "fuel_laps_2": 0.0,
    "fuel_laps_1": 0.0,
    "new_best_lap": 0.0,
    "lap_pace_gain": 0.0,
    "lap_pace_loss": 0.0,
    "pace_gain_live": 20.0,
    "pace_loss_live": 20.0,
}

# Priority for the audio queue: a higher-priority event interrupts the
# currently playing sound, lower/equal ones wait in line. Informational
# stuff (session start, weather, lap) is 0 and never interrupts anything.
EVENT_PRIORITIES: dict[str, int] = {
    "session_start": 0,
    "weather_clear": 0,
    "weather_hot": 0,
    "weather_cold": 0,
    "weather_wet": 0,
    "lap_completed": 0,
    "wrong_way_clear": 1,
    "pit_limiter_on": 1,
    "pit_limiter_off": 1,
    "fuel_low": 1,
    "lap_invalidated": 1,
    "wrong_way": 2,
    "fuel_critical": 2,
    "track_limits": 2,
    "fuel_laps_1": 2,
    "fuel_laps_2": 1,
    "fuel_laps_3": 1,
    "pace_gain_live": 1,
    "pace_loss_live": 1,
    "damage_front": 2,
    "damage_rear": 2,
    "damage_left": 2,
    "damage_right": 2,
    "damage_center": 2,
    "damage_suspension": 2,
    "crash": 3,
    "spin": 3,
}
