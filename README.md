# boltun

Самописный споттер для **Assetto Corsa Evo**: читает телеметрию из
shared memory и реагирует на события голосом/текстом.

## Как это работает

AC Evo публикует три именованных блока shared memory (Windows):

| Блок | Имя | Частота |
| --- | --- | --- |
| physics | `Local\acevo_pmf_physics` | каждый шаг физики (~333 Гц) |
| graphics | `Local\acevo_pmf_graphics` | каждый кадр (HUD) |
| static | `Local\acevo_pmf_static` | один раз за сессию |

Споттер открывает эти блоки через Win32 `OpenFileMappingW` (без `mmap`,
потому что `mmap` молча создаёт пустой блок и не даёт понять, что игра
не запущена), раскладывает байты в ctypes-структуры и превращает в
плоский срез `TelemetrySnapshot`. Детекторы смотрят на срезы и при
выполнении условий генерируют события, которые выводятся текстом и/или
озвучкой из локальных файлов.

## Быстрый старт

Только стандартная библиотека, зависимости не нужны.

```powershell
python main.py            # живая телеметрия (нужна запущенная игра)
python main.py --demo     # симуляция, чтобы проверить ивенты без игры
python main.py --hz 120   # частота цикла
python main.py --cooldown 5.0   # пауза между повторами одного ивента, сек
```

В `--demo` за ~1 минуту срабатывают все стартовые ивенты: старт сессии,
пит-лимитер, низкое/критичное топливо, езда не в ту сторону, круг,
разворот и удар.

## Структура проекта

```
main.py                  # CLI: main.py [--demo] [--hz N] [--cooldown S]
spotter/
  shmem.py               # низкоуровневый Win32 доступ к shared memory
  structs.py             # ctypes-структуры трёх блоков (раскладка официального SDK)
  snapshot.py            # плоский TelemetrySnapshot из сырых структур
  live.py                # живой источник (SharedMemorySource)
  demo.py                # симулятор телеметрии для отладки
  events.py              # детекторы ивентов + SpotterEvent
  phrases.py             # банк фраз (локальный файл, в git не лежит)
  announcer.py           # вывод: ConsoleAnnouncer / AudioAnnouncer (очередь + приоритеты)
  engine.py              # цикл: чтение -> детекторы -> вывод (+ cooldown, verbose)
```

## Как добавить ивент

1. В `phrases.py` добавь варианты фраз для нового `event_id` (минимум 2,
   лучше 3-5).
2. В `events.py` напиши детектор (класс от `Detector`) и зарегистрируй
   его в `default_detectors()`. **Обязательно** укажи его cooldown в
   `EVENT_COOLDOWNS` (если не указан — используется `--cooldown`) и
   приоритет в `EVENT_PRIORITIES` (по умолчанию 0 — информационное).
3. Если нужно новое поле телеметрии — добавь его в `snapshot.py`
   (поле берётся из `structs.py`).
4. Перегенерируй звук: `python generate_voice.py`.

## Как добавить звук

Файлы лежат в `audio/` (папка в `.gitignore` — звуки локальные). Поиск
файла для события, по порядку:

1. `audio/<event_id>.mp3` — один файл руками (например, для отладки);
2. `audio/<event_id>_<n>.wav` — варианты, сгенерированные скриптом
   (выбирается случайный).

Запуск с озвучкой: `python main.py --audio`. Пока файла нет — споттер
печатает текст и `[audio] missing sound file`, так что отлаживать можно
и без звуков. Воспроизведение через Windows MCI (winmm), MP3/WAV
поддерживаются системой, для проигрывания зависимости не нужны.

## Генерация голосов (Piper TTS)

Модели с предпрослушиванием: https://rhasspy.github.io/piper-samples/
Скачай `.onnx` (+ рядом `.onnx.json`) понравившегося голоса, например
`en_US-lessac-high` или `en_US-ryan-high`, и положи в папку `models/`.

```powershell
pip install -r requirements.txt          # ставит piper-tts
python generate_voice.py                 # найдёт модель в models/ сам
python generate_voice.py --model models\en_US-ryan-high.onnx
python generate_voice.py --length-scale 0.82
```

Скрипт берёт фразы прямо из `spotter/phrases.py` (единый источник
правды, отдельный phrases.txt не нужен) и пишет в `audio/` по файлу на
вариант: `session_start_0.wav`, `session_start_1.wav` и т.д. Фразы с
плейсхолдерами (`{...}`) пропускаются — им нужен текст на лету, а у нас
только заранее сгенерированные файлы.

`spotter/phrases.py` **не в git** (локальный файл) — это твоя личная
копия. Делаешь свои фразы по шаблону ниже, перегенерируешь звук,
и ничего не конфликтует с репозиторием.

Сразу после синтеза каждый файл прогоняется через FFmpeg с эффектом
рации (band-pass ~350-2800 Гц, подъём середины, лёгкое квантование,
моно 22.05 кГц). FFmpeg ищется в PATH, `C:\ffmpeg\...`, MOZA Pit House
и BlueStacks; иначе укажи путь: `python generate_voice.py --ffmpeg C:\ffmpeg\bin\ffmpeg.exe`. Отключить шаг: `--no-radio`.

Повторный запуск перезаписывает файлы, так что можно спокойно
перегенерировать набор после правки фраз.

## Фразы: шаблон для копипаста

`spotter/phrases.py` — это `PHRASES: dict[str, list[str]]`: каждый ивент
имеет список вариантов. Аннаунсер берёт случайный вариант, генератор
делает один WAV на вариант. **Минимум 2 варианта на ивент, лучше 3-5.**
Фразы — короткие, в стиле рации, имя гонщика вплетай в часть из них.

Полный список ивентов и их смысл (для генерации фраз):

| event_id | Смысл |
| --- | --- |
| `session_start` | старт сессии |
| `weather_clear/hot/cold/wet` | погодный бриф на старте |
| `wrong_way` | едет не в ту сторону (удержание 2 с) |
| `wrong_way_clear` | направление снова верное |
| `track_limits` | живой срез: выиграл время за пределами трассы, не отдал |
| `pit_limiter_on/off` | пит-лимитер вкл/выкл |
| `fuel_low` / `fuel_critical` | топливо низкое / критичное |
| `fuel_laps_10/5/3/2/1` | осталось N кругов по топливу |
| `crash` | удар |
| `damage_front/rear/left/right/center/suspension` | повреждение зоны |
| `spin` | разворот |
| `lap_completed` / `lap_invalidated` | круг засчитан / нет |
| `new_best_lap` | новый личный рекорд круга |
| `lap_pace_gain` / `lap_pace_loss` | круг сильно быстрее/медленнее лучшего |
| `pace_gain_live` / `pace_loss_live` | живая дельта: набирает/теряет время сейчас |

Шаблон (копируй целиком в `spotter/phrases.py`, подставь свои фразы
вместо `<variant N>`):

```python
"""Phrase bank for spotter events.

The announcer picks a random variant per event; generate_voice.py makes
one WAV per variant. Do NOT use {placeholders} in phrases - they are
skipped by the generator and cause missing-sound warnings at runtime.

This file is local (gitignored) - edit freely and run:
    python generate_voice.py
"""

from __future__ import annotations

import random

PHRASES: dict[str, list[str]] = {
    "session_start": ["<variant 1>", "<variant 2>", "<variant 3>"],
    "weather_clear": ["<variant 1>", "<variant 2>"],
    "weather_hot": ["<variant 1>", "<variant 2>"],
    "weather_cold": ["<variant 1>", "<variant 2>"],
    "weather_wet": ["<variant 1>", "<variant 2>"],
    "wrong_way": ["<variant 1>", "<variant 2>", "<variant 3>"],
    "wrong_way_clear": ["<variant 1>", "<variant 2>"],
    "track_limits": ["<variant 1>", "<variant 2>", "<variant 3>"],
    "pit_limiter_on": ["<variant 1>", "<variant 2>"],
    "pit_limiter_off": ["<variant 1>", "<variant 2>"],
    "fuel_low": ["<variant 1>", "<variant 2>", "<variant 3>"],
    "fuel_critical": ["<variant 1>", "<variant 2>"],
    "fuel_laps_10": ["<variant 1>", "<variant 2>"],
    "fuel_laps_5": ["<variant 1>", "<variant 2>"],
    "fuel_laps_3": ["<variant 1>", "<variant 2>"],
    "fuel_laps_2": ["<variant 1>", "<variant 2>"],
    "fuel_laps_1": ["<variant 1>", "<variant 2>"],
    "crash": ["<variant 1>", "<variant 2>", "<variant 3>"],
    "damage_front": ["<variant 1>", "<variant 2>"],
    "damage_rear": ["<variant 1>", "<variant 2>"],
    "damage_left": ["<variant 1>", "<variant 2>"],
    "damage_right": ["<variant 1>", "<variant 2>"],
    "damage_center": ["<variant 1>", "<variant 2>"],
    "damage_suspension": ["<variant 1>", "<variant 2>"],
    "spin": ["<variant 1>", "<variant 2>"],
    "lap_completed": ["<variant 1>", "<variant 2>"],
    "lap_invalidated": ["<variant 1>", "<variant 2>"],
    "new_best_lap": ["<variant 1>", "<variant 2>"],
    "lap_pace_gain": ["<variant 1>", "<variant 2>"],
    "lap_pace_loss": ["<variant 1>", "<variant 2>"],
    "pace_gain_live": ["<variant 1>", "<variant 2>"],
    "pace_loss_live": ["<variant 1>", "<variant 2>"],
}


def format_phrase(event_id: str, params: dict | None = None) -> str:
    variants = PHRASES.get(event_id) or ["[no phrase for {0}]".format(event_id)]
    phrase = random.choice(variants)
    if params:
        try:
            phrase = phrase.format(**params)
        except (KeyError, ValueError):
            pass
    return phrase
```

После заполнения:

```powershell
python generate_voice.py   # пересоберёт audio/*.wav (с эффектом рации)
python main.py --demo --audio   # послушать
```

## Промпт для opencode / работяги

Скопируй текст ниже, **замени `<ТВОЁ ИМЯ>` на своё имя** (латиницей,
как произносится: `Alex`, `Dima`, `Artyom`...) и вставь в opencode.
Он сам откроет README, возьмёт шаблон и таблицу ивентов, напишет фразы
и перегенерирует звук.

````text
Сделай мне персональную озвучку для споттера в Assetto Corsa Evo.

Моё имя: <ТВОЁ ИМЯ>.

Прочитай в README.md раздел "Фразы: шаблон для копипаста" - там полный
список event_id с пояснениями и шаблон файла spotter/phrases.py.

Перепиши spotter/phrases.py целиком: для каждого event_id из шаблона
напиши 3-5 вариантов фраз (для малых событий минимум 3). Требования:

- язык английский, стиль - спортивный радист (spotter), короткие ёмкие
  фразы, 3-8 слов, без канцелярита;
- имя <ТВОЁ ИМЯ> вплетай в большинство фраз, но не в каждую - пусть
  звучит естественно;
- тон: поддерживающий на позитиве ("nice lap", "great pace"), чёткий и
  спокойный на критике ("you're down, push", "box now");
- НЕ используй {плейсхолдеры} - такие фразы генератор пропускает и на
  рантайме будет "missing sound file";
- не ломай format_phrase() - оставь функцию как есть;
- фразы лаконичнее для аварийных ивентов (crash, fuel_laps_1,
  fuel_critical, wrong_way), длиннее допустимы для инфо (weather_*,
  session_start).

После записи файла запусти:
python generate_voice.py
и проверь, что все ивенты получили свои *_N.wav в audio/ и радио-эффект
применился ко всем (не должно быть ошибок и "skipped"). Если где-то
ошибка - исправь и перегенерируй.
````

## Контекст для ИИ-ассистента (и для тех, кто вайбкодит в этой репе)

### Что нужно знать перед правками

- Runtime использует только стандартную библиотеку (Windows). Для генерации
  звука нужны `piper-tts` и `ffmpeg` (см. «Генерация голосов»).
- `spotter/phrases.py`, `audio/`, `models/` — в `.gitignore` и **не коммитятся**:
  это персональные файлы (свои фразы/голос у каждого). После свежего клона
  `spotter/phrases.py` не существует — его надо создать из шаблона выше или
  через промпт opencode, иначе `import spotter` упадёт. Не коммить
  сгенерированные `.wav` и `.onnx` — они большие и локальные.
- Комментарии в коде на русском, стиль — как в соседних файлах. Новые файлы
  без необходимости не создаём.

### Что воссоздать после клона (всё из `.gitignore`)

Эти файлы/папки не в git — после `git clone` их надо получить/сгенерировать:

| Что | Откуда | Как |
| --- | --- | --- |
| `spotter/phrases.py` | шаблон выше или промпт opencode | **обязательно**, иначе `import spotter` упадёт |
| `models/en_US-ryan-high.onnx` + `en_US-ryan-high.onnx.json` | Hugging Face: репо `rhasspy/piper-voices`, папка `en/en_US/ryan/high/` | качаются **два** файла: веса `.onnx` и конфиг `.onnx.json` рядом (без конфига Piper не загрузит голос). Другие голоса — аналогично из своей папки |
| `audio/*.wav` | генерируются скриптом из `phrases.py` | `python generate_voice.py` |
| `.venv/`, `venv/` | не нужны | runtime без зависимостей; для генерации достаточно `pip install -r requirements.txt` |
| `__pycache__/`, `*.pyc` | создаются Python'ом сами | — |

### Чеклист: новый ивент (делать каждый раз)

1. `spotter/phrases.py` — минимум 2-3 варианта фраз, **без `{плейсхолдеров}`**
   (такие фразы пропускаются генератором и на рантайме дают
   `missing sound file`).
2. `spotter/events.py` — класс-детектор (база `Detector` или
   `_SustainedStateDetector` для сигналов с удержанием) + регистрация в
   `default_detectors()` + cooldown в `EVENT_COOLDOWNS` + приоритет в
   `EVENT_PRIORITIES` (иначе информационный = 0).
3. Если нужно новое поле телеметрии: сначала `structs.py` (раскладка из
   официального SDK AC Evo, поля меняются между версиями игры — сверять
   актуальные оффсеты), потом `snapshot.py` (`TelemetrySnapshot` +
   `snapshot_from_shm`) и `format_debug()` для `--dump`.
4. Обновить README: таблицу ивентов, шаблон `phrases.py`, список в промпте.
5. `python generate_voice.py` — должно пройти **без ошибок и «skipped»**;
   каждый ивент обязан получить свои `_N.wav`.
6. Проверить детектор (сниппет ниже) и/или полный `python main.py --demo`.

### Проверка детектора без игры

Быстрая детерминированная проверка — скармливаем синтетические слепки
(без ожидания 70 секунд демо):

```python
python -c "
from spotter.events import TrackLimitsDetector
from spotter.snapshot import TelemetrySnapshot
det = TrackLimitsDetector(); prev = None; fired = []
for i in range(60 * 10):
    t = i / 60.0
    snap = TelemetrySnapshot(ts=t, packet_id=i)
    snap.race_cut_gained_time_ms = 300 if 2.0 <= t < 5.0 else 0
    for ev in det.check(snap, prev):
        fired.append((round(ev.ts, 1), ev.event_id))
    prev = snap
print(fired)  # ожидаем один track_limits около t=3.0, без повторов внутри
"
```

Либо полный прогон `python main.py --demo --verbose`: за ~70 секунд
проигрываются все события. В логе каждый ивент должен сработать ровно один
раз за свой инцидент, без спама (за это отвечают удержание в детекторе +
cooldown в движке).

### Отладка в игре

- Споттер запускается **после входа в заезд** (shared memory появляется со
  стартом сессии) и перезапускается при смене сессии (static-блок читается
  один раз).
- `python main.py --dump --hz 60` — посмотреть, что реально приходит из SM
  перед написанием/правкой детектора.
- `python main.py --verbose --audio --hz 120` — события со звуком и логом
  подавлений (`fired ... suppressed by cooldown`).
- Воспроизведение через MCI: если звук не играет, проверь, что файл лежит в
  `audio/` и не залочен другим процессом.

### Флоу ветвления (trunk-based)

- В `master` напрямую **не коммитим**. Работаем в коротких ветках:
  `git checkout -b <ник>/<фича>` (например `artyom/track-limits`).
- Коммиты мелкие, с осмысленным сообщением.
- Перед мержем: `git checkout master; git pull; git merge <ветка>` (или
  rebase), решить конфликты. `master` всегда остаётся рабочим.
- В конце работы ветка мержится в `master` и удаляется.
- Чужие персональные файлы (`phrases.py`) в чужих ветках не трогаем.

## Дорожная карта

- [x] Чтение телеметрии из shared memory AC Evo
- [x] Детекция стартового набора ивентов, вывод текстом
- [x] `AudioAnnouncer`: проигрывание локальных аудиофайлов (Windows MCI)
- [x] Генерация озвучки через Piper TTS + эффект рации (FFmpeg)
- [x] Очередь озвучки с приоритетами (никто сам себя не перебивает)
- [x] Погодный бриф, повреждения кузова, темп по кругам и живая дельта
- [x] Подсказки по топливу (10/5/3/2/1 круг)
- [ ] Больше ивентов: флаги, соседи, повреждения шин
- [ ] Посекторные сплиты (появятся в SM — сразу добавить в structs.py)
- [ ] Настройки порогов через конфиг (JSON/YAML)
