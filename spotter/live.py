"""Живой источник телеметрии: читает три блока shared memory AC Evo
и превращает их в TelemetrySnapshot.

Если игра не запущена, next() возвращает None - движок ждёт и
периодически переподключается.
"""

from __future__ import annotations

import time

from .shmem import AcevoReader
from .snapshot import TelemetrySnapshot, snapshot_from_shm
from .structs import SPageFileGraphic, SPageFilePhysics, SPageFileStatic


class SharedMemorySource:
    def __init__(self) -> None:
        self.reader = AcevoReader()
        self._static: SPageFileStatic | None = None
        self._missing_reported_at = 0.0

    def close(self) -> None:
        self.reader.close()

    def next(self) -> TelemetrySnapshot | None:
        try:
            if not self.reader.is_open:
                self.reader.open()
                self._static = None
            phys = SPageFilePhysics.from_buffer_copy(self.reader.read_physics())
            gr = SPageFileGraphic.from_buffer_copy(self.reader.read_graphics())
            if self._static is None:
                self._static = SPageFileStatic.from_buffer_copy(
                    self.reader.read_static()
                )
            return snapshot_from_shm(phys, gr, self._static, time.time())
        except FileNotFoundError:
            self.reader.close()
            return None
        except OSError as exc:
            print(f"[source] shared memory read error: {exc}")
            self.reader.close()
            return None
