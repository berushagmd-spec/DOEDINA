"""Procedural name database for Derd Generator 95.

The generator mixes curated Derd-like names with phonetic fragments.  It keeps
the source file small while providing far more combinations than a static text
file could reasonably contain.
"""

from __future__ import annotations

import random
import re
from typing import Protocol


class RandomLike(Protocol):
    def choice(self, seq): ...
    def choices(self, population, weights=None, *, cum_weights=None, k=1): ...


_SYSTEM_RANDOM = random.SystemRandom()

REQUIRED_ENDINGS = ("ерд", "рд", "ед")


CURATED_NAMES = (
    "Дерд", "Доед", "Деед", "Даед", "Дуед", "Диед", "Дёрд", "Дэрд",
    "Дард", "Дорд", "Дурд", "Дырд", "Дирд", "Дюрд", "Дярд", "Деорд",
    "Диорд", "Дуорд", "Даорд", "Дуард", "Деард",
    "Берд", "Верд", "Герд", "Жерд", "Зерд", "Керд", "Лерд", "Мерд",
    "Нерд", "Перд", "Рерд", "Серд", "Терд", "Ферд", "Херд", "Церд",
    "Черд", "Шерд", "Щерд", "Бард", "Вард", "Гард", "Жард", "Зард",
    "Кард", "Лард", "Мард", "Нард", "Пард", "Рард", "Сард", "Тард",
    "Фард", "Хард", "Цард", "Чард", "Шард", "Щард", "Борд", "Ворд",
    "Горд", "Жорд", "Зорд", "Корд", "Лорд", "Морд", "Норд", "Порд",
    "Рорд", "Сорд", "Торд", "Форд", "Хорд", "Цорд", "Чорд", "Шорд",
    "Щорд", "Бурд", "Вурд", "Гурд", "Журд", "Зурд", "Курд", "Лурд",
    "Мурд", "Нурд", "Пурд", "Рурд", "Сурд", "Турд", "Фурд", "Хурд",
    "Цурд", "Чурд", "Шурд", "Щурд", "Беед", "Веед", "Геед", "Жеед",
    "Зеед", "Кеед", "Леед", "Меед", "Неед", "Пеед", "Реед", "Сеед",
    "Теед", "Феед", "Хеед", "Цеед", "Чеед", "Шеед", "Щеед", "Боед",
    "Воед", "Гоед", "Жоед", "Зоед", "Коед", "Лоед", "Моед", "Ноед",
    "Поед", "Роед", "Соед", "Тоед", "Фоед", "Хоед", "Цоед", "Чоед",
    "Шоед", "Щоед", "Блерд", "Влерд", "Глерд", "Дверд", "Зверд",
    "Кверд", "Плерд", "Сверд", "Тверд", "Флерд", "Хверд", "Шверд",
    "Бруед", "Вруед", "Груед", "Друед", "Круед", "Пруед", "Труед",
    "Фруед", "Хруед", "Шруед", "Куард", "Скуед", "Флоорд", "Жаерд",
)


ONSETS = (
    "", "б", "в", "г", "д", "ж", "з", "к", "л", "м", "н", "п",
    "р", "с", "т", "ф", "х", "ц", "ч", "ш", "щ",
    "бр", "вр", "гр", "др", "жр", "зр", "кр", "пр", "тр", "фр",
    "хр", "шр", "бл", "вл", "гл", "дл", "зл", "кл", "пл", "сл",
    "фл", "хл", "шл", "дв", "кв", "св", "тв", "вз", "вн", "мн",
    "ск", "см", "сн", "сп", "ст", "сф", "сх", "сц", "сч", "шт",
    "шк", "шп", "бру", "гру", "дру", "кру", "пру", "тру", "фру",
)


NUCLEI = (
    "а", "е", "ё", "и", "о", "у", "ы", "э", "ю", "я",
    "аа", "ае", "аи", "ао", "ау", "ая", "еа", "ее", "еи", "ео",
    "еу", "ея", "ёа", "ёо", "иа", "ие", "ии", "ио", "иу", "ия",
    "оа", "ое", "ои", "оо", "оу", "оя", "уа", "уе", "уи", "уо",
    "уу", "уя", "ыа", "ые", "ыо", "ыя", "эа", "эе", "эо", "юа",
    "юе", "юо", "яа", "яе", "яо", "ай", "ей", "ой", "уй", "яй",
    "ар", "ер", "ёр", "ир", "ор", "ур", "ыр", "эр", "юр", "яр",
)


BRIDGES = (
    "б", "в", "г", "д", "ж", "з", "к", "л", "м", "н", "п", "р",
    "с", "т", "ф", "х", "ц", "ч", "ш", "щ", "бд", "вд", "гд",
    "дб", "дж", "жд", "зд", "кд", "лд", "мд", "нд", "рд", "сд",
    "тд", "бр", "вр", "гр", "др", "кр", "пр", "тр", "ск", "ст",
    "шт", "чк", "нк", "рк", "рм", "рн", "рс", "рт", "лк", "мп",
)


_BLOCKED_FRAGMENTS = (
    "хуй", "хуя", "хуё", "пизд", "ёб", "еба", "бля", "гандон",
    "пидор", "педоф", "ниггер", "жид",
)

_TRIPLE_LETTERS = re.compile(r"([а-яё])\1{2,}")
_ONLY_CYRILLIC = re.compile(r"^[а-яё]+$")


def raw_combination_count() -> int:
    """Return a conservative count of raw procedural combinations."""

    short = len(ONSETS) * len(REQUIRED_ENDINGS)
    simple = len(ONSETS) * len(NUCLEI) * len(REQUIRED_ENDINGS)
    double = (
        len(ONSETS)
        * len(NUCLEI)
        * len(BRIDGES)
        * len(NUCLEI)
        * len(REQUIRED_ENDINGS)
    )
    long = (
        len(ONSETS)
        * len(NUCLEI)
        * len(BRIDGES)
        * len(NUCLEI)
        * len(BRIDGES)
        * len(NUCLEI)
        * len(REQUIRED_ENDINGS)
    )
    return len(CURATED_NAMES) + short + simple + double + long


def _smooth(value: str) -> str:
    value = value.lower().replace("ъ", "").replace("ьы", "ы")
    value = _TRIPLE_LETTERS.sub(r"\1\1", value)
    return value


def _is_allowed(value: str) -> bool:
    return (
        3 <= len(value) <= 13
        and _ONLY_CYRILLIC.fullmatch(value) is not None
        and not value.startswith(("ы", "ь", "й"))
        and value.endswith(REQUIRED_ENDINGS)
        and not any(fragment in value for fragment in _BLOCKED_FRAGMENTS)
    )


def generate_name(rng: RandomLike | None = None) -> str:
    """Generate one capitalized Derd-like name.

    A custom ``random.Random`` instance may be supplied for reproducible tests.
    Production calls use ``SystemRandom``.
    """

    rng = rng or _SYSTEM_RANDOM

    for _ in range(100):
        style = rng.choices(
            ("curated", "short", "simple", "double", "long"),
            weights=(20, 25, 30, 21, 4),
            k=1,
        )[0]

        if style == "curated":
            return rng.choice(CURATED_NAMES)
        if style == "short":
            value = rng.choice(ONSETS) + rng.choice(REQUIRED_ENDINGS)
        elif style == "simple":
            value = rng.choice(ONSETS) + rng.choice(NUCLEI) + rng.choice(REQUIRED_ENDINGS)
        elif style == "double":
            value = (
                rng.choice(ONSETS)
                + rng.choice(NUCLEI)
                + rng.choice(BRIDGES)
                + rng.choice(NUCLEI)
                + rng.choice(REQUIRED_ENDINGS)
            )
        else:
            value = (
                rng.choice(ONSETS)
                + rng.choice(NUCLEI)
                + rng.choice(BRIDGES)
                + rng.choice(NUCLEI)
                + rng.choice(BRIDGES)
                + rng.choice(NUCLEI)
                + rng.choice(REQUIRED_ENDINGS)
            )

        value = _smooth(value)
        if _is_allowed(value):
            return value[0].upper() + value[1:]

    return "Дерд"


if __name__ == "__main__":
    print(f"Сырых комбинаций: {raw_combination_count():,}".replace(",", " "))
    for _ in range(25):
        print(generate_name())
