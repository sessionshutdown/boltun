"""Движок споттера: цикл чтение -> детекторы -> вывод.

Схема:
    source.next() -> TelemetrySnapshot | None
    для каждого детектора: det.check(snap, prev) -> list[SpotterEvent]
    announcer.say(event) для каждого события (с учётом cooldown)
"""

from __future__ import annotations

import ctypes
import sys
import time

from .announcer import Announcer
from .events import (
    EVENT_COOLDOWNS,
    EVENT_PRIORITIES,
    Detector,
    SpotterEvent,
    default_detectors,
)
from .snapshot import TelemetrySnapshot


def _raise_timer_resolution() -> None:
    if sys.platform != "win32":
        return
    try:
        winmm = ctypes.WinDLL("winmm", use_last_error=True)
        winmm.timeBeginPeriod(1)
    except OSError:
        pass


class SpotterEngine:
    def __init__(
        self,
        source,
        announcer: Announcer,
        detectors: list[Detector] | None = None,
        hz: int = 60,
        cooldown: float = 3.0,
        event_cooldowns: dict[str, float] | None = None,
        on_snapshot=None,
        verbose: bool = False,
    ) -> None:
        self.source = source
        self.announcer = announcer
        self.detectors = detectors or default_detectors()
        self.hz = max(1, int(hz))
        self.cooldown = cooldown
        self.verbose = verbose
        self._cooldowns = dict(EVENT_COOLDOWNS)
        if event_cooldowns:
            self._cooldowns.update(event_cooldowns)
        self._on_snapshot = on_snapshot
        self._last_fire: dict[str, float] = {}
        self._prev: TelemetrySnapshot | None = None
        self._last_missing_msg = 0.0

    def run(self) -> None:
        _raise_timer_resolution()
        period = 1.0 / self.hz
        try:
            while True:
                started = time.monotonic()
                snap = self.source.next()
                if snap is None:
                    self._prev = None
                    now = time.monotonic()
                    if now - self._last_missing_msg > 2.0:
                        self._last_missing_msg = now
                        print("[spotter] waiting for Assetto Corsa Evo... "
                              "start the game (shared memory appears when "
                              "a session begins)")
                    time.sleep(0.5)
                    continue
                self._process(snap)
                elapsed = time.monotonic() - started
                time.sleep(max(0.0, period - elapsed))
        except KeyboardInterrupt:
            print("\n[spotter] stopped.")
        finally:
            close = getattr(self.source, "close", None)
            if close:
                close()

    def _process(self, snap: TelemetrySnapshot) -> None:
        prev = self._prev
        for det in self.detectors:
            for event in det.check(snap, prev):
                event.priority = EVENT_PRIORITIES.get(event.event_id, 0)
                if self.verbose:
                    remaining = self._cooldown_remaining(event.event_id)
                    if remaining > 0.0:
                        print(f"[verbose] {det.name} fired '{event.message}' "
                              f"but suppressed by cooldown "
                              f"({remaining:.1f}s left)")
                    else:
                        print(f"[verbose] {det.name} fired: {event}")
                if self._cooldown_ok(event):
                    self.announcer.say(event)
        if self._on_snapshot is not None:
            self._on_snapshot(snap)
        self._prev = snap

    def _cooldown_remaining(self, event_id: str) -> float:
        cooldown = self._cooldowns.get(event_id, self.cooldown)
        last = self._last_fire.get(event_id, 0.0)
        return cooldown - (time.monotonic() - last)

    def _cooldown_ok(self, event: SpotterEvent) -> bool:
        now = time.monotonic()
        cooldown = self._cooldowns.get(event.event_id, self.cooldown)
        last = self._last_fire.get(event.event_id, 0.0)
        if now - last < cooldown:
            return False
        self._last_fire[event.event_id] = now
        return True
