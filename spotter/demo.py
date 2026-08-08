"""Симулированный источник телеметрии для отладки без игры.

Проигрывает примерно минуту "жизни" гонщика, чтобы триггернуть все
стартовые ивенты: старт сессии, круги, топливо, пит-лимитер, разворот,
удар. Запуск: python main.py --demo
"""

from __future__ import annotations

import math
import time

from .snapshot import TelemetrySnapshot

TRACK_LENGTH_M = 2000.0


class DemoSource:
    def __init__(self, hz: int = 60) -> None:
        self.hz = hz
        self.dt = 1.0 / hz
        self.t0 = time.monotonic()
        self._tick = 0
        self._lap_index = 0
        self._last_lap_ms = 90_000
        self._best_lap_ms = 90_000

    def next(self) -> TelemetrySnapshot:
        t = self._tick * self.dt
        self._tick += 1

        speed = 150.0 + 60.0 * math.sin(t / 25.0)
        speed = max(0.0, speed)
        dist = speed / 3.6 * self.dt
        km = (t * (speed / 3.6) / 1000.0) % (TRACK_LENGTH_M / 1000.0)
        lap_ms = int(((t * (speed / 3.6) / 1000.0) % (TRACK_LENGTH_M / 1000.0))
                     / (TRACK_LENGTH_M / 1000.0) * 95_000)

        laps = (t * (speed / 3.6)) / TRACK_LENGTH_M
        if int(laps) > self._lap_index:
            self._lap_index = int(laps)
            self._last_lap_ms = 88_000 + (self._lap_index % 6) * 1_500
            if self._last_lap_ms < self._best_lap_ms:
                self._best_lap_ms = self._last_lap_ms
        is_valid_lap = self._lap_index != 3

        fuel = max(0.0, 50.0 - t * 2.0)
        fuel_percent = fuel / 50.0 * 100.0
        laps_fuel = fuel / 2.5

        pit_limiter = 20.0 <= (t % 30.0) < 27.0
        wrong_way = 30.0 <= t < 40.0

        yaw_rate = 0.0
        if 45.0 <= t < 48.0:
            yaw_rate = 2.5 * math.sin((t - 45.0) * 6.0)

        acc_long = 0.2
        if 55.0 <= t < 55.2:
            acc_long = -18.0
            speed = 30.0

        damage_front = 45.0 if t >= 55.0 else 0.0
        damage_left = 30.0 if t >= 55.0 else 0.0
        damage_suspension = 40.0 if t >= 55.0 else 0.0

        race_cut_gained_time_ms = 0
        if 62.0 <= t < 66.0:
            race_cut_gained_time_ms = int(120 + (t - 62.0) * 250)

        delta_time_ms = int(2500 * math.sin(t / 8.0))

        return TelemetrySnapshot(
            ts=t,
            packet_id=self._tick,
            status=1,
            speed_kmh=round(speed, 1),
            gear=4 if not wrong_way else 2,
            rpms=int(4200 + speed * 20),
            gas=0.7 if acc_long > -1.0 else 0.0,
            brake=0.1,
            pit_limiter=pit_limiter,
            wrong_way=wrong_way,
            current_km=km,
            lap_time_ms=lap_ms,
            last_lap_ms=self._last_lap_ms,
            best_lap_ms=self._best_lap_ms,
            fuel_l=round(fuel, 1),
            fuel_percent=round(fuel_percent, 1),
            delta_time_ms=delta_time_ms,
            laps_possible_with_fuel=round(laps_fuel, 1),
            race_cut_gained_time_ms=race_cut_gained_time_ms,
            position=5,
            total_drivers=12,
            yaw_rate=yaw_rate,
            acc_long=acc_long,
            acc_vert=0.0,
            track_length_m=TRACK_LENGTH_M,
            car="demo_car",
            driver="Test Driver",
            air_temp=24.0,
            road_temp=28.0,
            track="Demo Circuit",
            grip=95,
            wiper=0,
            is_valid_lap=is_valid_lap,
            damage_front=damage_front,
            damage_left=damage_left,
            damage_suspension=damage_suspension,
        )
