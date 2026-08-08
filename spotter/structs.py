"""ctypes-структуры трёх блоков shared memory AC Evo.

Раскладка транскрибирована из официального Shared Memory API документа
(Kunos, Steam guide #3707421508) и сверена с проектом live-telemetry-evo.

Соглашения:
    - порядок колёс в массивах физики: [FL, FR, RL, RR]
    - gear: 0 = R, 1 = N, 2.. = вперёд (отображаемый = gear - 1)
    - педали gas/brake/clutch: 0..1
    - booleans: в graphics/static это c_bool (1 байт), в physics - c_int32
    - строки: char[N] null-padded ASCII
    - _pack_ = 4
"""

from __future__ import annotations

import ctypes
from ctypes import (
    c_bool, c_byte, c_char, c_float, c_int8, c_int16, c_int32,
    c_uint8, c_uint16, c_uint32, c_uint64,
)


class SPageFilePhysics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId", c_int32),
        ("gas", c_float),
        ("brake", c_float),
        ("fuel", c_float),
        ("gear", c_int32),
        ("rpms", c_int32),
        ("steerAngle", c_float),
        ("speedKmh", c_float),
        ("velocity", c_float * 3),
        ("accG", c_float * 3),
        ("wheelSlip", c_float * 4),
        ("wheelLoad", c_float * 4),
        ("wheelsPressure", c_float * 4),
        ("wheelAngularSpeed", c_float * 4),
        ("tyreWear", c_float * 4),
        ("tyreDirtyLevel", c_float * 4),
        ("tyreCoreTemperature", c_float * 4),
        ("camberRAD", c_float * 4),
        ("suspensionTravel", c_float * 4),
        ("drs", c_float),
        ("tc", c_float),
        ("heading", c_float),
        ("pitch", c_float),
        ("roll", c_float),
        ("cgHeight", c_float),
        ("carDamage", c_float * 5),
        ("numberOfTyresOut", c_int32),
        ("pitLimiterOn", c_int32),
        ("abs", c_float),
        ("kersCharge", c_float),
        ("kersInput", c_float),
        ("autoShifterOn", c_int32),
        ("rideHeight", c_float * 2),
        ("turboBoost", c_float),
        ("ballast", c_float),
        ("airDensity", c_float),
        ("airTemp", c_float),
        ("roadTemp", c_float),
        ("localAngularVel", c_float * 3),
        ("finalFF", c_float),
        ("performanceMeter", c_float),
        ("engineBrake", c_int32),
        ("ersRecoveryLevel", c_int32),
        ("ersPowerLevel", c_int32),
        ("ersHeatCharging", c_int32),
        ("ersIsCharging", c_int32),
        ("kersCurrentKJ", c_float),
        ("drsAvailable", c_int32),
        ("drsEnabled", c_int32),
        ("brakeTemp", c_float * 4),
        ("clutch", c_float),
        ("tyreTempI", c_float * 4),
        ("tyreTempM", c_float * 4),
        ("tyreTempO", c_float * 4),
        ("isAIControlled", c_int32),
        ("tyreContactPoint", (c_float * 3) * 4),
        ("tyreContactNormal", (c_float * 3) * 4),
        ("tyreContactHeading", (c_float * 3) * 4),
        ("brakeBias", c_float),
        ("localVelocity", c_float * 3),
        ("P2PActivations", c_int32),
        ("P2PStatus", c_int32),
        ("currentMaxRpm", c_int32),
        ("mz", c_float * 4),
        ("fx", c_float * 4),
        ("fy", c_float * 4),
        ("slipRatio", c_float * 4),
        ("slipAngle", c_float * 4),
        ("tcInAction", c_int32),
        ("absInAction", c_int32),
        ("suspensionDamage", c_float * 4),
        ("tyreTemp", c_float * 4),
        ("waterTemp", c_float),
        ("brakeTorque", c_float * 4),
        ("frontBrakeCompound", c_int32),
        ("rearBrakeCompound", c_int32),
        ("padLife", c_float * 4),
        ("discLife", c_float * 4),
        ("ignitionOn", c_int32),
        ("starterEngineOn", c_int32),
        ("isEngineRunning", c_int32),
        ("kerbVibration", c_float),
        ("slipVibrations", c_float),
        ("roadVibrations", c_float),
        ("absVibrations", c_float),
    ]


class SPageFileStatic(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("sm_version", c_char * 15),
        ("ac_evo_version", c_char * 15),
        ("session", c_int32),
        ("session_name", c_char * 33),
        ("event_id", c_uint8),
        ("session_id", c_uint8),
        ("starting_grip", c_int32),
        ("starting_ambient_temperature_c", c_float),
        ("starting_ground_temperature_c", c_float),
        ("is_static_weather", c_bool),
        ("is_timed_race", c_bool),
        ("is_online", c_bool),
        ("number_of_sessions", c_int32),
        ("nation", c_char * 33),
        ("longitude", c_float),
        ("latitude", c_float),
        ("track", c_char * 33),
        ("track_configuration", c_char * 33),
        ("track_length_m", c_float),
    ]


class SMEvoTyreState(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("slip", c_float),
        ("lock", c_bool),
        ("tyre_pressure", c_float),
        ("tyre_temperature_c", c_float),
        ("brake_temperature_c", c_float),
        ("brake_pressure", c_float),
        ("tyre_temperature_left", c_float),
        ("tyre_temperature_center", c_float),
        ("tyre_temperature_right", c_float),
        ("tyre_compound_front", c_char * 33),
        ("tyre_compound_rear", c_char * 33),
        ("tyre_normalized_pressure", c_float),
        ("tyre_normalized_temperature_left", c_float),
        ("tyre_normalized_temperature_center", c_float),
        ("tyre_normalized_temperature_right", c_float),
        ("brake_normalized_temperature", c_float),
        ("tyre_normalized_temperature_core", c_float),
        ("_reserved", c_byte * 128),
    ]


class SMEvoDamageState(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("damage_front", c_float),
        ("damage_rear", c_float),
        ("damage_left", c_float),
        ("damage_right", c_float),
        ("damage_center", c_float),
        ("damage_suspension_lf", c_float),
        ("damage_suspension_rf", c_float),
        ("damage_suspension_lr", c_float),
        ("damage_suspension_rr", c_float),
        ("_reserved", c_byte * 92),
    ]


class SMEvoPitInfo(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("damage", c_int8),
        ("fuel", c_int8),
        ("tyres_lf", c_int8),
        ("tyres_rf", c_int8),
        ("tyres_lr", c_int8),
        ("tyres_rr", c_int8),
        ("_reserved", c_byte * 58),
    ]


class SMEvoElectronics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("tc_level", c_int8),
        ("tc_cut_level", c_int8),
        ("abs_level", c_int8),
        ("esc_level", c_int8),
        ("ebb_level", c_int8),
        ("brake_bias", c_float),
        ("engine_map_level", c_int8),
        ("turbo_level", c_float),
        ("ers_deployment_map", c_int8),
        ("ers_recharge_map", c_float),
        ("is_ers_heat_charging_on", c_bool),
        ("is_ers_overtake_mode_on", c_bool),
        ("is_drs_open", c_bool),
        ("diff_power_level", c_int8),
        ("diff_coast_level", c_int8),
        ("front_bump_damper_level", c_int8),
        ("front_rebound_damper_level", c_int8),
        ("rear_bump_damper_level", c_int8),
        ("rear_rebound_damper_level", c_int8),
        ("is_ignition_on", c_bool),
        ("is_pitlimiter_on", c_bool),
        ("active_performance_mode", c_int8),
        ("_reserved", c_byte * 88),
    ]


class SMEvoInstrumentation(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("main_light_stage", c_int8),
        ("special_light_stage", c_int8),
        ("cockpit_light_stage", c_int8),
        ("wiper_level", c_int8),
        ("rain_lights", c_bool),
        ("direction_light_left", c_bool),
        ("direction_light_right", c_bool),
        ("flashing_lights", c_bool),
        ("warning_lights", c_bool),
        ("selected_display_index", c_int8),
        ("display_current_page_index", c_int8 * 16),
        ("are_headlights_visible", c_bool),
        ("_reserved", c_byte * 101),
    ]


class SMEvoSessionState(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("phase_name", c_char * 33),
        ("time_left", c_char * 15),
        ("time_left_ms", c_int32),
        ("wait_time", c_char * 15),
        ("total_lap", c_int32),
        ("current_lap", c_int32),
        ("lights_on", c_int32),
        ("lights_mode", c_int32),
        ("lap_length_km", c_float),
        ("end_session_flag", c_int32),
        ("time_to_next_session", c_char * 15),
        ("disconnected_from_server", c_bool),
        ("restart_season_enabled", c_bool),
        ("ui_enable_drive", c_bool),
        ("ui_enable_setup", c_bool),
        ("is_ready_to_next_blinking", c_bool),
        ("show_waiting_for_players", c_bool),
        ("_reserved", c_byte * 143),
    ]


class SMEvoTimingState(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("current_laptime", c_char * 15),
        ("delta_current", c_char * 15),
        ("delta_current_p", c_int32),
        ("last_laptime", c_char * 15),
        ("delta_last", c_char * 15),
        ("delta_last_p", c_int32),
        ("best_laptime", c_char * 15),
        ("ideal_laptime", c_char * 15),
        ("total_time", c_char * 15),
        ("is_invalid", c_bool),
        ("_reserved", c_byte * 138),
    ]


class SMEvoAssistsState(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("auto_gear", c_uint8),
        ("auto_blip", c_uint8),
        ("auto_clutch", c_uint8),
        ("auto_clutch_on_start", c_uint8),
        ("manual_ignition_e_start", c_uint8),
        ("auto_pit_limiter", c_uint8),
        ("standing_start_assist", c_uint8),
        ("auto_steer", c_float),
        ("arcade_stability_control", c_float),
        ("_reserved", c_byte * 48),
    ]


class SPageFileGraphic(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId", c_int32),
        ("status", c_int32),
        ("focused_car_id_a", c_uint64),
        ("focused_car_id_b", c_uint64),
        ("player_car_id_a", c_uint64),
        ("player_car_id_b", c_uint64),
        ("rpm", c_uint16),
        ("is_rpm_limiter_on", c_bool),
        ("is_change_up_rpm", c_bool),
        ("is_change_down_rpm", c_bool),
        ("tc_active", c_bool),
        ("abs_active", c_bool),
        ("esc_active", c_bool),
        ("launch_active", c_bool),
        ("is_ignition_on", c_bool),
        ("is_engine_running", c_bool),
        ("kers_is_charging", c_bool),
        ("is_wrong_way", c_bool),
        ("is_drs_available", c_bool),
        ("battery_is_charging", c_bool),
        ("is_max_kj_per_lap_reached", c_bool),
        ("is_max_charge_kj_per_lap_reached", c_bool),
        ("display_speed_kmh", c_int16),
        ("display_speed_mph", c_int16),
        ("display_speed_ms", c_int16),
        ("pitspeeding_delta", c_float),
        ("gear_int", c_int16),
        ("rpm_percent", c_float),
        ("gas_percent", c_float),
        ("brake_percent", c_float),
        ("handbrake_percent", c_float),
        ("clutch_percent", c_float),
        ("steering_percent", c_float),
        ("ffb_strength", c_float),
        ("car_ffb_multiplier", c_float),
        ("water_temperature_percent", c_float),
        ("water_pressure_bar", c_float),
        ("fuel_pressure_bar", c_float),
        ("water_temperature_c", c_int8),
        ("air_temperature_c", c_int8),
        ("oil_temperature_c", c_float),
        ("oil_pressure_bar", c_float),
        ("exhaust_temperature_c", c_float),
        ("g_forces_x", c_float),
        ("g_forces_y", c_float),
        ("g_forces_z", c_float),
        ("turbo_boost", c_float),
        ("turbo_boost_level", c_float),
        ("turbo_boost_perc", c_float),
        ("steer_degrees", c_int32),
        ("current_km", c_float),
        ("total_km", c_uint32),
        ("total_driving_time_s", c_uint32),
        ("time_of_day_hours", c_int32),
        ("time_of_day_minutes", c_int32),
        ("time_of_day_seconds", c_int32),
        ("delta_time_ms", c_int32),
        ("current_lap_time_ms", c_int32),
        ("predicted_lap_time_ms", c_int32),
        ("fuel_liter_current_quantity", c_float),
        ("fuel_liter_current_quantity_percent", c_float),
        ("fuel_liter_per_km", c_float),
        ("km_per_fuel_liter", c_float),
        ("current_torque", c_float),
        ("current_bhp", c_int32),
        ("tyre_lf", SMEvoTyreState),
        ("tyre_rf", SMEvoTyreState),
        ("tyre_lr", SMEvoTyreState),
        ("tyre_rr", SMEvoTyreState),
        ("npos", c_float),
        ("kers_charge_perc", c_float),
        ("kers_current_perc", c_float),
        ("control_lock_time", c_float),
        ("car_damage", SMEvoDamageState),
        ("car_location", c_int32),
        ("pit_info", SMEvoPitInfo),
        ("fuel_liter_used", c_float),
        ("fuel_liter_per_lap", c_float),
        ("laps_possible_with_fuel", c_float),
        ("battery_temperature", c_float),
        ("battery_voltage", c_float),
        ("instantaneous_fuel_liter_per_km", c_float),
        ("instantaneous_km_per_fuel_liter", c_float),
        ("gear_rpm_window", c_float),
        ("instrumentation", SMEvoInstrumentation),
        ("instrumentation_min_limit", SMEvoInstrumentation),
        ("instrumentation_max_limit", SMEvoInstrumentation),
        ("electronics", SMEvoElectronics),
        ("electronics_min_limit", SMEvoElectronics),
        ("electronics_max_limit", SMEvoElectronics),
        ("electronics_is_modifiable", SMEvoElectronics),
        ("total_lap_count", c_int32),
        ("current_pos", c_uint32),
        ("total_drivers", c_uint32),
        ("last_laptime_ms", c_int32),
        ("best_laptime_ms", c_int32),
        ("flag", c_int32),
        ("global_flag", c_int32),
        ("max_gears", c_uint32),
        ("engine_type", c_int32),
        ("has_kers", c_bool),
        ("is_last_lap", c_bool),
        ("performance_mode_name", c_char * 33),
        ("diff_coast_raw_value", c_float),
        ("diff_power_raw_value", c_float),
        ("race_cut_gained_time_ms", c_int32),
        ("distance_to_deadline", c_int32),
        ("race_cut_current_delta", c_float),
        ("session_state", SMEvoSessionState),
        ("timing_state", SMEvoTimingState),
        ("player_ping", c_int32),
        ("player_latency", c_int32),
        ("player_cpu_usage", c_int32),
        ("player_cpu_usage_avg", c_int32),
        ("player_qos", c_int32),
        ("player_qos_avg", c_int32),
        ("player_fps", c_int32),
        ("player_fps_avg", c_int32),
        ("driver_name", c_char * 33),
        ("driver_surname", c_char * 33),
        ("car_model", c_char * 33),
        ("is_in_pit_box", c_bool),
        ("is_in_pit_lane", c_bool),
        ("is_valid_lap", c_bool),
        ("car_coordinates", (c_float * 3) * 60),
        ("gap_ahead", c_float),
        ("gap_behind", c_float),
        ("active_cars", c_uint8),
        ("fuel_per_lap", c_float),
        ("fuel_estimated_laps", c_float),
        ("assists_state", SMEvoAssistsState),
        ("max_fuel", c_float),
        ("max_turbo_boost", c_float),
        ("use_single_compound", c_bool),
        ("car_ids", (c_uint64 * 2) * 60),
    ]


assert ctypes.sizeof(SPageFilePhysics) == 800, ctypes.sizeof(SPageFilePhysics)
assert ctypes.sizeof(SMEvoTyreState) == 256
assert ctypes.sizeof(SMEvoDamageState) == 128
assert ctypes.sizeof(SMEvoPitInfo) == 64
assert ctypes.sizeof(SMEvoElectronics) == 128
assert ctypes.sizeof(SMEvoInstrumentation) == 128
assert ctypes.sizeof(SMEvoSessionState) == 256
assert ctypes.sizeof(SMEvoTimingState) == 256
assert ctypes.sizeof(SMEvoAssistsState) == 64
assert ctypes.sizeof(SPageFileStatic) >= 200, ctypes.sizeof(SPageFileStatic)
assert ctypes.sizeof(SPageFileGraphic) <= 8192, ctypes.sizeof(SPageFileGraphic)


def decode_cstr(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("ascii", errors="ignore")
