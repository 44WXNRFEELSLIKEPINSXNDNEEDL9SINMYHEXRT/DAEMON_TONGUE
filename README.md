# DAEMON TONGUE

> A classifier for grimdark phrases — dark, poetic, fatalistic aesthetic.

Trained on dark quotes and lyrics.  
Classifies phrases as **DAEMON** (grimdark aesthetic) or **MORTAL** (everything else).

---

## Quickstart

```bash
uv sync
uv run src/predict.py
```

## Training

```bash
uv run src/train.py
```

## Dataset

1000+ manually labeled phrases _(as of 09.06.2026)_.  
Label `1` = grimdark aesthetic (dark, poetic, fatalistic).  
Label `0` = neutral, mechanical, or plainly aggressive.

## Model

Hosted on HuggingFace: `44WXNRFEELSLIKEPINSANDNEEDLESINMYHEART/DAEMON_TONGUE_JUDGE`

```python
from transformers import pipeline
clf = pipeline("text-classification", model="44WXNRFEELSLIKEPINSANDNEEDLESINMYHEART/DAEMON_TONGUE_JUDGE")
clf("The blood of the fallen will anoint me")
# [{'label': 'DAEMON', 'score': 0.94}]
```
HuggingFace Spaces link: [`44WXNRFEELSLIKEPINSANDNEEDLESINMYHEART/DAEMON_TONGUE`](https://huggingface.co/spaces/44WXNRFEELSLIKEPINSANDNEEDLESINMYHEART/DAEMON_TONGUE)
## Labels

| Label | Name   | Meaning                                       |
| ----- | ------ | --------------------------------------------- |
| `1`   | DAEMON | Dark, poetic, fatalistic — grimdark aesthetic |
| `0`   | MORTAL | Neutral, mechanical, plainly aggressive       |

---
# DAEMON TONGUE

> Классификатор гримдарк-фраз — тёмная, поэтическая, фаталистическая эстетика.

Обучен на тёмных цитатах и лирике. 
Классифицирует фразы как **DAEMON** (гримдарк-эстетика) или **MORTAL** (всё остальное).

---

## Быстрый старт

```bash
uv sync
uv run src/predict.py
```

## Обучение

```bash
uv run src/train.py
```

## Датасет

1000+ вручную размеченных фраз _(по состоянию на 09.06.2026)_.  
Метка `1` = гримдарк-эстетика (тёмное, поэтическое, фаталистическое).  
Метка `0` = нейтральное, механическое или просто агрессивное.

## Модель

Размещена на HuggingFace: `44WXNRFEELSLIKEPINSANDNEEDLESINMYHEART/DAEMON_TONGUE_JUDGE`

```python
from transformers import pipeline
clf = pipeline("text-classification", model="44WXNRFEELSLIKEPINSANDNEEDLESINMYHEART/DAEMON_TONGUE_JUDGE")
clf("The blood of the fallen will anoint me")
```

Ссылка на HuggingFace Spaces: [`44WXNRFEELSLIKEPINSANDNEEDLESINMYHEART/DAEMON_TONGUE`](https://huggingface.co/spaces/44WXNRFEELSLIKEPINSANDNEEDLESINMYHEART/DAEMON_TONGUE)
## Метки

| Метка | Название | Значение                                                 |
| ----- | -------- | -------------------------------------------------------- |
| `1`   | DAEMON   | Тёмное, поэтическое, фаталистическое — гримдарк-эстетика |
| `0`   | MORTAL   | Нейтральное, механическое, просто агрессивное            |

---
## Ход работы и сложности

> [!Последнее обновление: 09.06.2026]
### Первоначальный сбор данных
Для старта были выбраны: 
- Фразы Атрокса (AATROX) из компьютерной игры League of Legends - богатый источник красивых речевых конструкций антагониста, включающий в себя упоминания таких тем, как: резня, смерть, убийство, враг всего живого, боги на небесах, сокрущение богов, аннигиляция, абсолютная тишина, губитель мира.
>   _"I can smile, and murder while I smile."_
>   _"Gods and mortals, they deserve only death!"_
>   _"I will drown them in oceans of blood!"_
>   _"Cleave through them, Aatrox! Crush their skulls! Shatter their ribs! Disembowl their very souls!" Aatrox breathes heavily. "Our vengeance is at hand!"_
- Названия и описания предметов из The Binding of Isaac - располагает краткими фразами, пропитанными необходимой эстетикой. Однако многие из них являются пограничными случаями, которые сложно единозначно трактовать, поэтому они являются неоптимальным вариантом.
  При парсинге учитывались только фразы, состоящие из 3 слов и более.
>   _Reusable evil... but at what cost?_
>   _Rise from the grave
>   We all float down here..._

Все данные были размечены вручную, потому что задача достаточно специфичная.
### Первый инференс
Как и ожидалось, изначально модель триггерили такие слова, как: "kill", "death" и т.д., даже если они не образуют ничего особенного. Были вручную добавлены пограничные случаи, где явно показано, что нужно считать за эджовые.