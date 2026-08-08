# AGENTS.md — правила для ИИ-ассистента

Споттер для **Assetto Corsa Evo** (Windows): shared memory -> детекторы ->
события -> текст + озвучка (Piper TTS + FFmpeg радио-эффект). Runtime — только
stdlib; для генерации звука нужны `piper-tts` и `ffmpeg`.

## Железные правила

- `spotter/phrases.py`, `audio/`, `models/`, `venv/` — в `.gitignore`,
  **не коммитить** (персональные/локальные файлы). WAV и ONNX тоже не коммитим.
- Фразы — **без `{плейсхолдеров}`**: генератор их пропускает, на рантайме
  `missing sound file`.
- Комментарии в коде на русском, стиль — как в соседних файлах.
- Поля shared memory меняются между версиями игры: новые поля сверяй с
  актуальной раскладкой SDK AC Evo.

## Новый ивент (всегда весь список)

1. `spotter/phrases.py` — минимум 2-3 варианта фраз.
2. `spotter/events.py` — детектор (база `Detector` или `_SustainedStateDetector`)
   + регистрация в `default_detectors()` + cooldown в `EVENT_COOLDOWNS` +
   приоритет в `EVENT_PRIORITIES`.
3. Новое поле телеметрии: `structs.py` -> `snapshot.py` (`TelemetrySnapshot` +
   `snapshot_from_shm`) + `format_debug()`.
4. Обновить README: таблицу ивентов, шаблон `phrases.py`, список в промпте.
5. `python generate_voice.py` — без ошибок и «skipped», у каждого ивента `_N.wav`.
6. Проверить: сниппет из README или `python main.py --demo --verbose` (каждый
   ивент срабатывает один раз за инцидент, без спама).

## Отладка

- Быстро (без ожидания демо): скормить детектору синтетические
  `TelemetrySnapshot` (рабочий пример — в README, «Проверка детектора без игры»).
- В игре: споттер запускать **после входа в заезд**, перезапускать при смене
  сессии. `--dump --hz 60` — посмотреть реальные поля SM, `--verbose --audio`.

## Git-флоу (trunk-based)

- В `master` напрямую не коммитим: `git checkout -b <ник>/<фича>`.
- Мелкие осмысленные коммиты; в конце работы ветку мержим в `master` и удаляем.
- Чужие персональные файлы (`phrases.py`) в чужих ветках не трогаем.

## После клона (gitignored-файлы)

- `spotter/phrases.py` — создать из шаблона в README (или через промпт opencode):
  **обязательно**, иначе `import spotter` падает.
- `models/en_US-ryan-high.onnx` **и** `en_US-ryan-high.onnx.json` — 2 файла с
  Hugging Face (`rhasspy/piper-voices`, папка `en/en_US/ryan/high/`). Без
  `.json` голос не грузится.
- `audio/` — `python generate_voice.py`.
- venv не нужен: `pip install -r requirements.txt` только для генерации.
