"""Нормализованный слепок телеметрии для детекторов ивентов.

Детекторы работают только с этим плоским срезом - им не нужно знать
про ctypes-структуры и сырые блоки памяти.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .structs import (
    SPageFileGraphic,
    SPageFilePhysics,
    SPageFileStatic,
    decode_cstr,
)


@dataclass
class TelemetrySnapshot:
    ts: float = 0.0
    packet_id: int = 0
    status: int = 0
    speed_kmh: float = 0.0
    gear: int = 0
    rpms: int = 0
    gas: float = 0.0
    brake: float = 0.0
    pit_limiter: bool = False
    wrong_way: bool = False
    current_km: float = 0.0
    lap_time_ms: int = 0
    last_lap_ms: int = 0
    best_lap_ms: int = 0
    fuel_l: float = 0.0
    fuel_percent: float = 0.0
    position: int = 0
    total_drivers: int = 0
    yaw_rate: float = 0.0
    acc_long: float = 0.0
    acc_vert: float = 0.0
    track_length_m: float = 5000.0
    car: str = ""
    driver: str = ""
    air_temp: float = 20.0
    road_temp: float = 25.0
    track: str = ""
    grip: int = 100
    wiper: int = 0
    is_valid_lap: bool = True
    damage_front: float = 0.0
    damage_rear: float = 0.0
    damage_left: float = 0.0
    damage_right: float = 0.0
    damage_center: float = 0.0
    damage_suspension: float = 0.0
    delta_time_ms: int = 0
    laps_possible_with_fuel: float = 0.0
    race_cut_gained_time_ms: int = 0
    race_cut_current_delta: float = 0.0

    @property
    def lap_km(self) -> float:
        return max(self.track_length_m, 1.0) / 1000.0

    @property
    def moving(self) -> bool:
        return self.speed_kmh > 1.0 or self.rpms > 500

    def format_debug(self) -> str:
        if self.gear <= 0:
            gear = "R"
        elif self.gear == 1:
            gear = "N"
        else:
            gear = str(self.gear - 1)
        return (
            f"t={self.ts:6.1f} spd={self.speed_kmh:6.1f} gear={gear} "
            f"rpm={self.rpms:5d} gas={self.gas:.2f} brk={self.brake:.2f} "
            f"pit={int(self.pit_limiter)} ww={int(self.wrong_way)} "
            f"km={self.current_km:5.2f} fuel={self.fuel_percent:5.1f}% "
            f"pos={self.position}/{self.total_drivers} yaw={self.yaw_rate:+.2f} "
            f"accL={self.acc_long:+.1f} air={self.air_temp:.0f}C "
            f"road={self.road_temp:.0f}C dmgF={self.damage_front:.0f} "
            f"delta={self.delta_time_ms:+d} fuelLaps={self.laps_possible_with_fuel:.1f} "
            f"cut={self.race_cut_gained_time_ms:+d} {self.car}"
        )


def snapshot_from_shm(
    phys: SPageFilePhysics,
    gr: SPageFileGraphic,
    st: SPageFileStatic | None,
    ts: float,
) -> TelemetrySnapshot:
    track_length = st.track_length_m if st and st.track_length_m > 1.0 else 5000.0
    name = decode_cstr(bytes(gr.driver_name))
    surname = decode_cstr(bytes(gr.driver_surname))
    return TelemetrySnapshot(
        ts=ts,
        packet_id=gr.packetId,
        status=gr.status,
        speed_kmh=float(phys.speedKmh),
        gear=int(phys.gear),
        rpms=int(phys.rpms),
        gas=float(phys.gas),
        brake=float(phys.brake),
        pit_limiter=bool(phys.pitLimiterOn),
        wrong_way=bool(gr.is_wrong_way),
        current_km=float(gr.current_km),
        lap_time_ms=int(gr.current_lap_time_ms),
        last_lap_ms=int(gr.last_laptime_ms),
        best_lap_ms=int(gr.best_laptime_ms),
        fuel_l=float(gr.fuel_liter_current_quantity),
        fuel_percent=float(gr.fuel_liter_current_quantity_percent) * 100.0,
        position=int(gr.current_pos),
        total_drivers=int(gr.total_drivers),
        yaw_rate=float(phys.localAngularVel[2]),
        acc_long=float(phys.accG[2]),
        acc_vert=float(phys.accG[1]),
        track_length_m=track_length,
        car=decode_cstr(bytes(gr.car_model)),
        driver=f"{name} {surname}".strip(),
        air_temp=float(phys.airTemp),
        road_temp=float(phys.roadTemp),
        track=decode_cstr(bytes(st.track)) if st else "",
        grip=int(st.starting_grip) if st else 100,
        wiper=int(gr.instrumentation.wiper_level),
        is_valid_lap=bool(gr.is_valid_lap),
        damage_front=float(gr.car_damage.damage_front),
        damage_rear=float(gr.car_damage.damage_rear),
        damage_left=float(gr.car_damage.damage_left),
        damage_right=float(gr.car_damage.damage_right),
        damage_center=float(gr.car_damage.damage_center),
        damage_suspension=max(
            float(gr.car_damage.damage_suspension_lf),
            float(gr.car_damage.damage_suspension_rf),
            float(gr.car_damage.damage_suspension_lr),
            float(gr.car_damage.damage_suspension_rr),
        ),
        delta_time_ms=int(gr.delta_time_ms),
        laps_possible_with_fuel=float(gr.laps_possible_with_fuel),
        race_cut_gained_time_ms=int(gr.race_cut_gained_time_ms),
        race_cut_current_delta=float(gr.race_cut_current_delta),
    )
