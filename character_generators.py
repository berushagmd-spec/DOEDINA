"""Name databases for Romix Tatar and Dima Nelis generators."""

from __future__ import annotations

import random
import re

from name_generator import BRIDGES, NUCLEI, ONSETS, RandomLike


_SYSTEM_RANDOM = random.SystemRandom()
_TRIPLE_LETTERS = re.compile(r"([а-яё])\1{2,}")
_ONLY_CYRILLIC = re.compile(r"^[а-яё]+$")
_BLOCKED_FRAGMENTS = (
    "хуй", "хуя", "хуё", "пизд", "ёб", "еба", "бля", "гандон",
    "пидор", "педоф", "ниггер",
)


def _lines(block: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(line.strip() for line in block.splitlines() if line.strip()))


ROMIX_CURATED = _lines(
    """
    Ромикс
    Домикс
    Комикс
    Томикс
    Сомикс
    Ломикс
    Бомикс
    Гомикс
    Жомикс
    Зомикс
    Момикс
    Номикс
    Фомикс
    Хомикс
    Чомикс
    Шомикс
    Ремикс
    Демикс
    Семикс
    Темикс
    Кемикс
    Лемикс
    Мемикс
    Громикс
    Бобикс
    Глебикс
    Владикс
    Славикс
    Ярикс
    Рурикс
    Добрикс
    Квадрикс
    Турбикс
    Кефирикс
    Йогуртикс
    Молокикс
    Бубликс
    Шарикс
    Сухарикс
    Пельменикс
    Арбузикс
    Огурчикс
    Котикс
    Смайликс
    Пикселикс
    Кубикс
    Рофликс
    Мемикс
    Геликс
    Феникс
    Лунатикс
    Космикс
    """
)


ETHNONYMS = _lines(
    """
    татар
    русский
    украинец
    белорус
    поляк
    чех
    словак
    словенец
    хорват
    серб
    черногорец
    босняк
    болгарин
    македонец
    русин
    кашуб
    лужичанин
    башкир
    чуваш
    мариец
    удмурт
    коми
    коми-пермяк
    карел
    вепс
    ижорец
    эрзянин
    мокшанин
    ненец
    ханты
    манси
    саам
    селькуп
    нганасан
    финн
    эстонец
    венгр
    казах
    киргиз
    узбек
    туркмен
    азербайджанец
    турок
    гагауз
    каракалпак
    ногай
    кумык
    карачаевец
    балкарец
    крымский татарин
    сибирский татарин
    уйгур
    тувинец
    хакас
    алтаец
    якут
    шорец
    грузин
    армянин
    осетин
    чеченец
    ингуш
    аварец
    даргинец
    лезгин
    лакец
    табасаранец
    агул
    рутулец
    цахур
    абхаз
    абазин
    адыгеец
    кабардинец
    черкес
    мегрел
    сван
    литовец
    латыш
    немец
    австриец
    швейцарец
    нидерландец
    фламандец
    фриз
    датчанин
    швед
    норвежец
    исландец
    фаререц
    англичанин
    шотландец
    валлиец
    ирландец
    француз
    бретонец
    корсиканец
    испанец
    каталонец
    баск
    галисиец
    португалец
    итальянец
    сардинец
    сицилиец
    албанец
    грек
    румын
    молдаванин
    мальтиец
    киприот
    американец
    канадец
    квебекец
    мексиканец
    кубинец
    пуэрториканец
    ямаец
    гаитянин
    доминиканец
    гватемалец
    гондурасец
    сальвадорец
    никарагуанец
    костариканец
    панамец
    колумбиец
    венесуэлец
    эквадорец
    перуанец
    боливиец
    чилиец
    аргентинец
    уругваец
    парагваец
    бразилец
    кечуа
    аймара
    гуарани
    мапуче
    майя
    ацтек
    инуит
    алеут
    навахо
    чероки
    ирокез
    кри
    метис
    араб
    перс
    курд
    еврей
    ассириец
    езид
    друз
    пуштун
    таджик
    хазареец
    белудж
    памирец
    афганец
    пакистанец
    индиец
    бенгалец
    пенджабец
    синдх
    гуджаратец
    маратх
    тамил
    телугу
    малаяли
    непалец
    бутанец
    тибетец
    шерпа
    сингал
    мальдивец
    китаец
    ханец
    монгол
    бурят
    калмык
    кореец
    японец
    айну
    вьетнамец
    кхмер
    лаосец
    таец
    бирманец
    малаец
    яванец
    сунданец
    балиец
    филиппинец
    тагал
    индонезиец
    сингапурец
    маори
    самоанец
    тонганец
    фиджиец
    гаваец
    папуас
    австралиец
    новозеландец
    египтянин
    копт
    ливиец
    тунисец
    алжирец
    марокканец
    амазиг
    туарег
    суданец
    эфиоп
    эритреец
    сомалиец
    кениец
    масай
    танзаниец
    угандиец
    руандиец
    конголезец
    ангольец
    мозамбикец
    малагасиец
    зулус
    коса
    бур
    йоруба
    игбо
    хауса
    ашанти
    сенегалец
    ганец
    нигериец
    камерунец
    малиец
    чадец
    намибиец
    зимбабвиец
    замбиец
    ботсванец
    малаец
    полинезиец
    меланезиец
    микронезиец
    """
)


SLAVIC_GIVEN_NAMES = _lines(
    """
    Александр
    Алексей
    Анатолий
    Андрей
    Антон
    Аркадий
    Арсений
    Артём
    Богдан
    Борис
    Вадим
    Валентин
    Валерий
    Василий
    Виктор
    Виталий
    Владимир
    Владислав
    Всеволод
    Вячеслав
    Геннадий
    Георгий
    Герман
    Глеб
    Григорий
    Даниил
    Денис
    Дмитрий
    Дима
    Добрыня
    Егор
    Евгений
    Елисей
    Захар
    Иван
    Игорь
    Илья
    Кирилл
    Клим
    Константин
    Лев
    Леонид
    Максим
    Марк
    Матвей
    Михаил
    Мирон
    Мстислав
    Никита
    Николай
    Олег
    Павел
    Пётр
    Платон
    Прохор
    Ратмир
    Родион
    Роман
    Ростислав
    Руслан
    Савелий
    Святослав
    Семён
    Сергей
    Станислав
    Степан
    Тарас
    Тимофей
    Тихон
    Фёдор
    Филипп
    Юрий
    Ярослав
    Адам
    Адриан
    Алёша
    Блажей
    Боян
    Бранислав
    Вацлав
    Велимир
    Витомир
    Войцех
    Горан
    Далибор
    Дамир
    Драган
    Збигнев
    Зденек
    Зоран
    Казимир
    Карел
    Кшиштоф
    Любомир
    Лукаш
    Милан
    Милош
    Мирослав
    Неманья
    Предраг
    Пржемысл
    Радек
    Радован
    Томаш
    Якуб
    """
)


WORLD_GIVEN_NAMES = _lines(
    """
    Аарон
    Абдулла
    Абрахам
    Акира
    Али
    Амир
    Андерс
    Андреас
    Анри
    Арман
    Артур
    Бен
    Бернард
    Бьорн
    Бруно
    Габриэль
    Ганс
    Генрих
    Давид
    Джамал
    Джеймс
    Джон
    Диего
    Жан
    Ибрагим
    Исаак
    Карим
    Карл
    Кенджи
    Клаус
    Ли
    Луис
    Марко
    Мартин
    Махмуд
    Мигель
    Мохаммед
    Мустафа
    Нильс
    Омар
    Оскар
    Пабло
    Патрик
    Пьер
    Рашид
    Роберт
    Самир
    Сантьяго
    Стефан
    Томас
    Уильям
    Фарид
    Феликс
    Франц
    Фредерик
    Ханс
    Хасан
    Хироси
    Чэнь
    Шон
    Эдвард
    Эмиль
    Энцо
    Юсуф
    """
)


NELIS_CURATED = _lines(
    """
    Нелис
    Белис
    Велис
    Гелис
    Делис
    Елис
    Желис
    Зелис
    Келис
    Лелис
    Мелис
    Пелис
    Релис
    Селис
    Телис
    Фелис
    Хелис
    Целис
    Челис
    Шелис
    Ялис
    Налис
    Нилис
    Нолис
    Нулис
    Найлис
    Нейлис
    Норис
    Лорис
    Марис
    Тарис
    Варис
    Зарис
    Карис
    Парис
    Сарис
    Фарис
    Харис
    Денис
    Анис
    Ирис
    Борис
    Мирис
    Громис
    Светис
    Добрис
    Кефирис
    Йогуртис
    Рофлис
    Мемис
    Кубис
    """
)


def _clean(value: str) -> str:
    value = value.lower().replace("ъ", "").replace("ьы", "ы")
    return _TRIPLE_LETTERS.sub(r"\1\1", value)


def _valid(value: str, ending: str, minimum: int = 4) -> bool:
    return (
        minimum <= len(value) <= 15
        and _ONLY_CYRILLIC.fullmatch(value) is not None
        and value.endswith(ending)
        and not value.startswith(("ы", "ь", "й"))
        and not any(fragment in value for fragment in _BLOCKED_FRAGMENTS)
    )


def _procedural_ending_name(
    ending: str,
    curated: tuple[str, ...],
    rng: RandomLike,
) -> str:
    for _ in range(100):
        style = rng.choices(
            ("curated", "simple", "double"),
            weights=(32, 43, 25),
            k=1,
        )[0]
        if style == "curated":
            return rng.choice(curated)
        if style == "simple":
            value = rng.choice(ONSETS) + rng.choice(NUCLEI) + ending
        else:
            value = (
                rng.choice(ONSETS)
                + rng.choice(NUCLEI)
                + rng.choice(BRIDGES)
                + rng.choice(NUCLEI)
                + ending
            )
        value = _clean(value)
        if _valid(value, ending):
            return value[0].upper() + value[1:]
    return curated[0]


def generate_romix(rng: RandomLike | None = None) -> tuple[str, str]:
    """Return a generated -икс name and a random nationality/ethnicity."""

    rng = rng or _SYSTEM_RANDOM
    name = _procedural_ending_name("икс", ROMIX_CURATED, rng)
    ethnonym = rng.choice(ETHNONYMS)
    return name, ethnonym[0].upper() + ethnonym[1:]


def generate_nelis(rng: RandomLike | None = None) -> tuple[str, str]:
    """Return a mostly Slavic given name and a generated -ис surname."""

    rng = rng or _SYSTEM_RANDOM
    pool = rng.choices(
        (SLAVIC_GIVEN_NAMES, WORLD_GIVEN_NAMES),
        weights=(82, 18),
        k=1,
    )[0]
    given_name = rng.choice(pool)
    surname = _procedural_ending_name("ис", NELIS_CURATED, rng)
    return given_name, surname


def romix_combination_count() -> int:
    procedural_names = (
        len(ROMIX_CURATED)
        + len(ONSETS) * len(NUCLEI)
        + len(ONSETS) * len(NUCLEI) * len(BRIDGES) * len(NUCLEI)
    )
    return procedural_names * len(ETHNONYMS)


def nelis_combination_count() -> int:
    procedural_surnames = (
        len(NELIS_CURATED)
        + len(ONSETS) * len(NUCLEI)
        + len(ONSETS) * len(NUCLEI) * len(BRIDGES) * len(NUCLEI)
    )
    return (len(SLAVIC_GIVEN_NAMES) + len(WORLD_GIVEN_NAMES)) * procedural_surnames


if __name__ == "__main__":
    print(f"Ромикс-комбинаций: {romix_combination_count():,}".replace(",", " "))
    print(f"Нелис-комбинаций: {nelis_combination_count():,}".replace(",", " "))
    for _ in range(10):
        print(*generate_romix(), "|", *generate_nelis())
