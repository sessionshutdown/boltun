"""Entry point of the spotter.

Examples:
    python main.py            - live telemetry from Assetto Corsa Evo
    python main.py --demo     - simulation without the game (event checks)
    python main.py --dump     - print raw telemetry snapshot once per second
    python main.py --hz 120   - loop rate
"""

from __future__ import annotations

import argparse
import time

from spotter.announcer import AudioAnnouncer, ConsoleAnnouncer
from spotter.demo import DemoSource
from spotter.engine import SpotterEngine
from spotter.events import default_detectors
from spotter.live import SharedMemorySource
from spotter.snapshot import TelemetrySnapshot


class DumpLogger:
    def __init__(self) -> None:
        self._last = 0.0

    def __call__(self, snap: TelemetrySnapshot) -> None:
        now = time.monotonic()
        if now - self._last >= 1.0:
            self._last = now
            print("[dump]", snap.format_debug())


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="vibespotter",
        description="Spotter for Assetto Corsa Evo based on shared memory",
    )
    parser.add_argument("--demo", action="store_true",
                        help="use simulated telemetry instead of the game")
    parser.add_argument("--hz", type=int, default=60,
                        help="telemetry loop rate in Hz")
    parser.add_argument("--cooldown", type=float, default=3.0,
                        help="fallback cooldown in seconds for events without "
                             "their own value")
    parser.add_argument("--dump", action="store_true",
                        help="print raw telemetry snapshot once per second")
    parser.add_argument("--audio", action="store_true",
                        help="play sound files from --audio-dir instead of "
                             "plain text (text is still printed)")
    parser.add_argument("--audio-dir", default="audio",
                        help="folder with event sound files")
    parser.add_argument("--verbose", action="store_true",
                        help="log detector fires and cooldown suppressions")
    args = parser.parse_args()

    source = DemoSource(hz=args.hz) if args.demo else SharedMemorySource()
    announcer = (AudioAnnouncer(audio_dir=args.audio_dir)
                 if args.audio else ConsoleAnnouncer())
    engine = SpotterEngine(
        source=source,
        announcer=announcer,
        detectors=default_detectors(),
        hz=args.hz,
        cooldown=args.cooldown,
        on_snapshot=DumpLogger() if args.dump else None,
        verbose=args.verbose,
    )
    engine.run()


if __name__ == "__main__":
    main()
