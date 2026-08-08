"""Generate spotter voice lines with Piper TTS.

Phrases are taken from spotter.phrases (PHRASES) - the single source of
truth - so there is no separate phrases.txt to keep in sync. The script
writes one file per phrase variant to audio/<event_id>_<n>.wav, and
AudioAnnouncer picks a random variant at runtime.

Usage:
    pip install -r requirements.txt
    python generate_voice.py --model en_US-lessac-high.onnx
    python generate_voice.py --model en_US-ryan-high.onnx --output-dir audio

Where to get a model:
    https://rhasspy.github.io/piper-samples/   (listening previews)
    download the .onnx (+ matching .onnx.json) for the voice you like,
    e.g. en_US-lessac-high or en_US-ryan-high.

After synthesis every generated WAV is passed through an FFmpeg filter
chain that makes it sound like a race radio (band-pass ~350-2800 Hz,
mid boost, light crushing, mono 22.05 kHz). Disable with --no-radio.
FFmpeg must be installed and in PATH for this step.

Phrases containing {placeholders} (e.g. the lap time in "lap_completed")
cannot be pre-generated - they need runtime text. They are skipped with
a warning.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path

from spotter.phrases import PHRASES

RADIO_FILTER_CHAIN = (
    "highpass=f=350,"
    "lowpass=f=2800,"
    "equalizer=f=1200:width_type=h:width=800:g=3,"
    "acrusher=level_in=1:level_out=1:bits=10:mode=lin:aa=0.5,"
    "volume=1.4"
)


def _find_model() -> Path | None:
    models_dir = Path(__file__).parent / "models"
    if not models_dir.is_dir():
        return None
    onnx_files = sorted(models_dir.glob("*.onnx"))
    return onnx_files[0] if onnx_files else None


def _find_ffmpeg() -> str | None:
    which = shutil.which("ffmpeg")
    if which:
        return which
    candidates = [
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\MOZA Pit House\bin\ffmpeg.exe",
        r"C:\Program Files\BlueStacks_nxt\ffmpeg.exe",
    ]
    for c in candidates:
        if Path(c).is_file():
            return c
    return None


def _apply_radio(out_dir: Path, ffmpeg: str | None) -> None:
    if not ffmpeg:
        print("\n[radio] FFmpeg not found - keeping raw synthesis output "
              "(install ffmpeg, pass --ffmpeg, or use --no-radio to "
              "silence this note)")
        return
    wav_files = sorted(out_dir.glob("*.wav"))
    if not wav_files:
        return
    print(f"\nApplying radio effect to {len(wav_files)} file(s) "
          "via FFmpeg...")
    ok = 0
    for path in wav_files:
        tmp = out_dir / f".tmp_{path.name}"
        cmd = [
            ffmpeg, "-y",
            "-i", str(path),
            "-af", RADIO_FILTER_CHAIN,
            "-ar", "22050",
            "-ac", "1",
            str(tmp),
        ]
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0 and tmp.is_file():
            try:
                os.replace(tmp, path)
                ok += 1
                print(f"  [OK] {path.name}")
            except PermissionError:
                tmp.unlink(missing_ok=True)
                print(f"  [X] {path.name}: locked (open in a player?), "
                      "skipped")
        else:
            if tmp.is_file():
                tmp.unlink()
            err = result.stderr.strip().splitlines()
            print(f"  [X] {path.name}: {err[-1] if err else 'ffmpeg error'}")
    print(f"Radio effect applied: {ok}/{len(wav_files)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate spotter voice lines with Piper TTS",
    )
    parser.add_argument("--model",
                        help="path to the Piper .onnx model "
                             "(default: auto-detect in models/)")
    parser.add_argument("--output-dir", default="audio",
                        help="output folder (default: audio)")
    parser.add_argument("--length-scale", type=float, default=0.82,
                        help="speech speed, lower = faster "
                             "(0.82 fits spotter talk)")
    parser.add_argument("--no-radio", action="store_true",
                        help="skip the FFmpeg radio effect step")
    parser.add_argument("--ffmpeg",
                        help="path to ffmpeg.exe (default: auto-detect)")
    args = parser.parse_args()

    from piper import PiperVoice  # only needed for generation
    from piper.config import SynthesisConfig

    model_path = Path(args.model) if args.model else _find_model()
    if model_path is None:
        sys.exit("no model found: pass --model or drop a .onnx into models/")
    if not model_path.is_file():
        sys.exit(f"model not found: {model_path}")
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading Piper model: {model_path}")
    voice = PiperVoice.load(str(model_path))

    total = 0
    locked = []
    skipped = []
    for event_id, variants in PHRASES.items():
        for i, text in enumerate(variants):
            if "{" in text:
                skipped.append(f"{event_id}[{i}]: '{text}'")
                continue
            path = out_dir / f"{event_id}_{i}.wav"
            try:
                with wave.open(str(path), "wb") as wav_file:
                    voice.synthesize_wav(
                        text, wav_file,
                        syn_config=SynthesisConfig(
                            length_scale=args.length_scale),
                    )
            except PermissionError:
                locked.append((path, text))
                continue
            total += 1
            print(f"  [OK] {path.name}: '{text}'")

    print(f"\nDone: {total} files -> {out_dir}")
    if locked:
        print("Locked files (open in a player / Explorer preview?), "
              "retrying them:")
        for path, text in locked:
            try:
                with wave.open(str(path), "wb") as wav_file:
                    voice.synthesize_wav(
                        text, wav_file,
                        syn_config=SynthesisConfig(
                            length_scale=args.length_scale),
                    )
                total += 1
                print(f"  [OK] {path.name}: '{text}'")
            except PermissionError:
                print(f"  [X] still locked: {path} - close the app that "
                      "has it open and re-run")
    if skipped:
        print("Skipped (phrases with {placeholders} need runtime text, "
              "e.g. lap time):")
        for s in skipped:
            print(f"  - {s}")

    if not args.no_radio:
        ffmpeg = args.ffmpeg or _find_ffmpeg()
        if args.ffmpeg and not Path(args.ffmpeg).is_file():
            print(f"[radio] --ffmpeg not found: {args.ffmpeg}")
            ffmpeg = None
        _apply_radio(out_dir, ffmpeg)


if __name__ == "__main__":
    main()
