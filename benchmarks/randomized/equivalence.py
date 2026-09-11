"""Narrow, auditable equivalence rules for randomized differential output."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from decimal import Decimal

from .model import RandomCase

_PUNCTUATION_RE = re.compile(r"[^\w\s]", re.UNICODE)
_SPACE_RE = re.compile(r"\s+")
_SAFE_SURFACE_SHAPES = frozenset(
    {
        "hyphenation only",
        "whitespace only",
        "case only",
        "punctuation difference",
        "Unicode normalization difference",
    }
)
_EN_SMALL = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
)

# These are benchmark policy aliases, not runtime lexicon data. They must only
# collapse terminology that denotes the same currency units; they must not
# normalize numeric words or signs.
_CURRENCY_RULES = {
    ("en", "EUR"): (("euro", "euros"), ("cent", "cents"), ("and",)),
    ("en", "USD"): (("dollar", "dollars"), ("cent", "cents"), ("and",)),
    ("en", "GBP"): (
        ("pound", "pounds", "pound sterling", "pounds sterling"),
        ("penny", "pence"),
        ("and",),
    ),
    ("en", "CAD"): (("dollar", "dollars", "Canadian dollar", "Canadian dollars"), ("cent", "cents"), ("and",)),
    ("en", "AUD"): (("dollar", "dollars", "Australian dollar", "Australian dollars"), ("cent", "cents"), ("and",)),
    ("en", "INR"): (("rupee", "rupees", "Indian rupee", "Indian rupees"), ("paisa", "paise"), ("and",)),
    ("en", "RUB"): (("ruble", "rubles", "rouble", "roubles"), ("kopeck", "kopecks", "kopek", "kopeks"), ("and",)),
    ("en", "SAR"): (
        ("Saudi riyal", "Saudi riyals", "riyal", "riyals"),
        ("halala", "halalas", "halalah", "halalahs"),
        ("and",),
    ),
    ("en", "PLN"): (("zloty", "zlotys", "złoty", "złotys"), ("grosz", "groszy"), ("and",)),
    ("en", "JPY"): (("yen",), ("sen",), ("and",)),
    ("en", "HUF"): (("forint", "forints"), ("fillér", "filler", "fillers"), ("and",)),
    ("en", "NOK"): (
        ("krone", "kroner", "Norwegian krone", "Norwegian kroner"),
        ("øre",),
        ("and",),
    ),
    ("en", "SEK"): (
        ("krona", "kronor", "Swedish krona", "Swedish kronor"),
        ("öre",),
        ("and",),
    ),
    ("es", "CAD"): (
        ("dólar", "dólares", "dólar canadiense", "dólares canadienses"),
        ("centavo", "centavos"),
        ("y", "con", "and"),
    ),
    ("es", "NOK"): (
        ("corona", "coronas", "corona noruega", "coronas noruegas"),
        ("øre",),
        ("y", "con", "and"),
    ),
    ("es", "GBP"): (
        ("libra", "libras", "libra esterlina", "libras esterlinas"),
        ("penique", "peniques"),
        ("y", "con", "and"),
    ),
    ("fi", "GBP"): (
        ("punta", "puntaa"),
        ("penny", "pennyä"),
        ("ja", "and"),
    ),
    ("fi", "AUD"): (
        ("dollari", "dollaria", "Australian dollari", "Australian dollaria"),
        ("sentti", "senttiä"),
        ("ja", "and"),
    ),
    ("fi", "INR"): (
        ("rupia", "rupiaa", "Intian rupia", "Intian rupiaa"),
        ("paisa", "paisaa"),
        ("ja", "and"),
    ),
    ("fi", "SEK"): (
        ("kruunu", "kruunua"),
        ("äyri", "äyriä", "öre"),
        ("ja", "and"),
    ),
    ("ru", "EUR"): (("евро",), ("цент", "цента", "центов"), ("и",)),
    ("ru", "USD"): (("доллар", "доллара", "долларов"), ("цент", "цента", "центов"), ("и",)),
    ("ru", "RUB"): (("рубль", "рубля", "рублей"), ("копейка", "копейки", "копеек"), ("и",)),
    ("cs", "EUR"): (("euro", "eura", "eur"), ("cent", "centy", "centů"), ("a",)),
    ("cs", "USD"): (("dolar", "dolary", "dolarů"), ("cent", "centy", "centů"), ("a",)),
    ("cs", "GBP"): (("libra", "libry", "liber"), ("pence", "pencí"), ("a",)),
    ("cs", "JPY"): (("jen", "yeny", "jenů"), ("sen", "sény", "senů"), ("a",)),
    ("pt", "AUD"): (
        ("dólar", "dólares", "dólar australiano", "dólares australianos"),
        ("cêntimo", "cêntimos"),
        ("e",),
    ),
    ("pt", "CAD"): (
        ("dólar", "dólares", "dólar canadiano", "dólares canadianos"),
        ("cêntimo", "cêntimos"),
        ("e",),
    ),
    ("pt", "EUR"): (
        ("euro", "euros"),
        ("cêntimo", "cêntimos"),
        ("e",),
    ),
    ("pt", "GBP"): (
        ("libra", "libras"),
        ("pence", "péni", "pénis"),
        ("e",),
    ),
}

_ES_ORDINAL_VARIANTS = {
    11: {"undécimo", "decimoprimero", "décimo primero"},
    12: {"duodécimo", "decimosegundo", "décimo segundo"},
}
_ES_ORDINAL_ACCENT_VARIANTS = {20: ("vigesimo", "vigésimo")}
_FR_CONTINUATION_WORDS = frozenset(
    {
        "un", "une", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
        "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "vingt",
        "trente", "quarante", "cinquante", "soixante", "septante", "huitante", "nonante",
        "et", "mille", "premier", "première", "deuxième", "troisième", "quatrième",
        "cinquième", "sixième", "septième", "huitième", "neuvième", "dixième",
        "onzième", "douzième", "treizième", "quatorzième", "quinzième", "seizième",
        "septantième", "huitantième", "nonantième",
    }
)
_FR_NOUN_AFTER_NUMBER = frozenset(
    {
        "million", "millions", "milliard", "milliards",
        "euro", "euros", "dollar", "dollars", "livre", "livres",
    }
)
_PT_ORDINAL_ORACLE_REPAIRS = {
    "quadrigentésimo": "quadringentésimo",
    "septigentésimo": "septingentésimo",
    "octigentésimo": "octingentésimo",
    "tricentésimo": "trecentésimo",
    "seiscentésimo": "sexcentésimo",
}
_VI_UNDER_20 = (
    "không",
    "một",
    "hai",
    "ba",
    "bốn",
    "năm",
    "sáu",
    "bảy",
    "tám",
    "chín",
    "mười",
    "mười một",
    "mười hai",
    "mười ba",
    "mười bốn",
    "mười lăm",
    "mười sáu",
    "mười bảy",
    "mười tám",
    "mười chín",
)
_DE_UNITS = ("null", "eins", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun")
_DE_TEENS = ("zehn", "elf", "zwölf", "dreizehn", "vierzehn", "fünfzehn", "sechzehn", "siebzehn", "achtzehn", "neunzehn")
_DE_TENS = ("", "", "zwanzig", "dreißig", "vierzig", "fünfzig", "sechzig", "siebzig", "achtzig", "neunzig")


def _surface_key(text: str) -> str:
    text = unicodedata.normalize("NFC", text).casefold().replace("-", " ")
    text = _PUNCTUATION_RE.sub(" ", text)
    return _SPACE_RE.sub(" ", text).strip()


def _explicit_sign(text: str) -> str | None:
    stripped = text.lstrip()
    if stripped.startswith(('-', '+')):
        return stripped[0]
    return None

def _replace_phrase(text: str, phrase: str, marker: str) -> str:
    pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
    return re.sub(pattern, marker, text)


def _currency_key(case: RandomCase, text: str) -> str | None:
    language = case.locale.split("-", 1)[0]
    rule = _CURRENCY_RULES.get((language, case.currency or ""))
    if rule is None:
        return None
    major_aliases, minor_aliases, connector_aliases = rule
    normalized = _surface_key(text)
    for alias in sorted(major_aliases, key=len, reverse=True):
        normalized = _replace_phrase(normalized, _surface_key(alias), "<major>")
    for alias in sorted(minor_aliases, key=len, reverse=True):
        normalized = _replace_phrase(normalized, _surface_key(alias), "<minor>")
    connectors = {connector.casefold() for connector in connector_aliases}
    tokens = [token for token in normalized.split() if token not in connectors]
    return " ".join(tokens)


def _english_under_100(value: int) -> str:
    if value < 20:
        return (
            "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
            "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
            "seventeen", "eighteen", "nineteen",
        )[value]
    tens = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")[value // 10]
    return tens if value % 10 == 0 else f"{tens}-{_EN_SMALL[value % 10]}"


def _english_year_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "en" or case.kind != "year":
        return False
    value = case.python_value()
    if not isinstance(value, int):
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    allowed: set[str] = set()
    if 100 <= value <= 999:
        hundreds, remainder = divmod(value, 100)
        if remainder == 0:
            return False
        prefix = _EN_SMALL[hundreds]
        remainder_words = _english_under_100(remainder)
        forms = {
            f"{prefix} {remainder_words}",
            f"{prefix} hundred {remainder_words}",
            f"{prefix} hundred and {remainder_words}",
        }
        if remainder < 10:
            forms.add(f"{prefix} oh {_EN_SMALL[remainder]}")
        allowed = {_surface_key(item) for item in forms}
        return expected_key in allowed and actual_key in allowed

    if 1000 <= value <= 9999:
        thousands, remainder = divmod(value, 1000)
        forms: set[str] = set()
        if remainder == 0:
            return False
        if thousands < 10 and remainder < 100:
            remainder_words = _english_under_100(remainder)
            forms.update(
                {
                    f"{_EN_SMALL[thousands]} thousand {remainder_words}",
                    f"{_EN_SMALL[thousands]} thousand and {remainder_words}",
                }
            )
        first, second = divmod(value, 100)
        if 10 <= first < 100 and second:
            if second < 10:
                forms.add(f"{_english_under_100(first)} oh {_EN_SMALL[second]}")
            else:
                forms.add(f"{_english_under_100(first)} {_english_under_100(second)}")
        allowed = {_surface_key(item) for item in forms}
        return bool(allowed) and expected_key in allowed and actual_key in allowed
    return False


def _de_cardinal_under_10000(value: int) -> str:
    if value < 10:
        return _DE_UNITS[value]
    if value < 20:
        return _DE_TEENS[value - 10]
    if value < 100:
        tens, units = divmod(value, 10)
        if units == 0:
            return _DE_TENS[tens]
        unit = "ein" if units == 1 else _DE_UNITS[units]
        return f"{unit}und{_DE_TENS[tens]}"
    if value < 1000:
        hundreds, remainder = divmod(value, 100)
        prefix = ("ein" if hundreds == 1 else _DE_UNITS[hundreds]) + "hundert"
        return prefix + (_de_cardinal_under_10000(remainder) if remainder else "")
    thousands, remainder = divmod(value, 1000)
    prefix = "eintausend" if thousands == 1 else f"{_de_cardinal_under_10000(thousands)}tausend"
    return prefix + (_de_cardinal_under_10000(remainder) if remainder else "")


def _german_post_2000_year_oracle_quirk(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "de" or case.kind != "year":
        return False
    value = case.python_value()
    if not isinstance(value, int) or not 2000 <= value <= 9999:
        return False
    canonical = _de_cardinal_under_10000(value)
    century, remainder = divmod(value, 100)
    oracle_style = f"{_de_cardinal_under_10000(century)}hundert"
    if remainder:
        oracle_style += _de_cardinal_under_10000(remainder)
    return _surface_key(expected) == _surface_key(oracle_style) and _surface_key(actual) == _surface_key(canonical)

def _german_year_einshundert_oracle_quirk(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "de" or case.kind != "year":
        return False
    value = case.python_value()
    if not isinstance(value, int) or not 100 <= value < 200:
        return False
    remainder = _de_cardinal_under_10000(value % 100) if value % 100 else ""
    oracle_style = "einshundert" + remainder
    canonical = _de_cardinal_under_10000(value)
    return _surface_key(expected) == _surface_key(oracle_style) and _surface_key(actual) == _surface_key(canonical)

def _czech_optional_one_million_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "cs" or case.kind not in {"cardinal", "year"}:
        return False
    value = case.python_value()
    if not isinstance(value, int) or not 1_000_000 <= abs(value) < 2_000_000:
        return False

    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)

    def drop_optional_one(text: str) -> str:
        return re.sub(r"^(mínus )?jeden milion\b", r"\1milion", text)

    return (
        drop_optional_one(expected_key) == drop_optional_one(actual_key)
        and expected_key != actual_key
    )


def _german_optional_ein_ordinal_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "de" or case.kind != "ordinal":
        return False
    allowed = {100: {"hundertste", "einhundertste"}, 1000: {"tausendste", "eintausendste"}}.get(
        case.python_value()
    )
    if allowed is None:
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    return expected_key in allowed and actual_key in allowed and expected_key != actual_key
def _decimal_trailing_zero_precision_variant(case: RandomCase, expected: str, actual: str) -> bool:
    language = case.locale.split("-", 1)[0]
    decimal_words = {
        "en": ("point", "zero"),
        "es": ("punto", "cero"),
    }
    if case.kind != "decimal" or language not in decimal_words:
        return False
    marker, zero = decimal_words[language]
    _, fraction = case.value.value.split(".", 1) if "." in case.value.value else ("", "")
    trimmed = fraction.rstrip("0")
    trailing = len(fraction) - len(trimmed)
    if not trailing:
        return False
    candidate = _surface_key(actual).split()
    for _ in range(trailing):
        if not candidate or candidate[-1] != zero:
            return False
        candidate.pop()
    if not trimmed:
        if not candidate or candidate[-1] != marker:
            return False
        candidate.pop()
    return " ".join(candidate) == _surface_key(expected)


def _spanish_ordinal_accent_oracle_quirk(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "es" or case.kind != "ordinal":
        return False
    pair = _ES_ORDINAL_ACCENT_VARIANTS.get(case.python_value())
    return pair is not None and _surface_key(expected) == pair[0] and _surface_key(actual) == pair[1]


def _spanish_ordinal_synonym_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "es" or case.kind != "ordinal":
        return False
    allowed = _ES_ORDINAL_VARIANTS.get(case.python_value())
    return allowed is not None and _surface_key(expected) in {_surface_key(value) for value in allowed} and _surface_key(actual) in {_surface_key(value) for value in allowed}


def _spanish_currency_gender_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "es" or case.kind != "currency":
        return False
    if case.currency not in {"GBP", "NOK"}:
        return False
    repaired = _surface_key(expected)
    for masculine, feminine in (
        ("doscientos", "doscientas"),
        ("trescientos", "trescientas"),
        ("cuatrocientos", "cuatrocientas"),
        ("quinientos", "quinientas"),
        ("seiscientos", "seiscientas"),
        ("setecientos", "setecientas"),
        ("ochocientos", "ochocientas"),
        ("novecientos", "novecientas"),
    ):
        repaired = _replace_phrase(repaired, masculine, feminine)
    if repaired == _surface_key(expected):
        return False
    expected_key = _currency_key(case, repaired)
    actual_key = _currency_key(case, actual)
    return expected_key is not None and expected_key == actual_key


def _spanish_gbp_gender_variant(case: RandomCase, expected: str, actual: str) -> bool:
    return case.currency == "GBP" and _spanish_currency_gender_variant(case, expected, actual)


def _spanish_nok_gender_variant(case: RandomCase, expected: str, actual: str) -> bool:
    return case.currency == "NOK" and _spanish_currency_gender_variant(case, expected, actual)

def _finnish_compound_spacing_variant(case: RandomCase, expected: str, actual: str) -> bool:
    return (
        case.locale.split("-", 1)[0] == "fi"
        and case.kind in {"cardinal", "year"}
        and "".join(expected.split()) == "".join(actual.split())
    )


def _repair_french_oracle(text: str) -> str:
    tokens = _surface_key(text).split()
    repaired: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token == "centsième":
            repaired.append("centième")
            index += 1
            continue
        if token == "cents" and index + 1 < len(tokens):
            next_token = tokens[index + 1]
            if next_token not in _FR_NOUN_AFTER_NUMBER:
                repaired.append("cent")
                index += 1
                continue
        if token == "quatre" and index + 1 < len(tokens) and tokens[index + 1] == "vingtsième":
            repaired.extend(("quatre", "vingtième"))
            index += 2
            continue
        if (
            token == "quatre"
            and index + 2 < len(tokens)
            and tokens[index + 1] == "vingt"
            and tokens[index + 2] in {
                "million", "millions", "milliard", "milliards",
                "penny", "pence", "centime", "centimes",
                "euro", "euros", "dollar", "dollars", "livre", "livres",
            }
        ):
            repaired.extend(("quatre", "vingts"))
            index += 2
            continue
        if (
            token == "quatre"
            and index + 3 < len(tokens)
            and tokens[index + 1] == "vingt"
            and tokens[index + 2] == "et"
            and tokens[index + 3] in {"un", "unième"}
        ):
            repaired.extend(("quatre", "vingt", tokens[index + 3]))
            index += 4
            continue
        repaired.append(token)
        index += 1

    # num2words occasionally omits the plural on a terminal 80. Repair only the
    # oracle side; an erroneous Numeralform "quatre-vingt millions" must remain a mismatch.
    if len(repaired) >= 2 and repaired[-2:] == ["quatre", "vingt"]:
        repaired[-1] = "vingts"
    return " ".join(repaired)

def _french_cent_oracle_quirk(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "fr" or case.kind not in {"cardinal", "ordinal", "year", "currency"}:
        return False
    tokens = _surface_key(expected).split()
    repaired = [
        "cent"
        if token == "cents"
        and index + 1 < len(tokens)
        and tokens[index + 1] in _FR_CONTINUATION_WORDS
        and tokens[index + 1] not in _FR_NOUN_AFTER_NUMBER
        else token
        for index, token in enumerate(tokens)
    ]
    return " ".join(repaired) == _surface_key(actual) and repaired != tokens


def _french_oracle_orthography_quirk(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "fr" or case.kind not in {"cardinal", "ordinal", "year", "currency"}:
        return False
    repaired = _repair_french_oracle(expected)
    value = case.python_value()
    if case.kind == "cardinal" and isinstance(value, int) and 1_000_000 <= abs(value) < 2_000_000:
        repaired = re.sub(r"^(moins )?un millions\b", r"\1un million", repaired)
    return repaired != _surface_key(expected) and repaired == _surface_key(actual)


def _italian_cento_elision_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "it":
        return False

    def canonical(text: str) -> str:
        return re.sub("cento(?=(?:ottanta|ottant|otto|uno|undici))", "cent", _surface_key(text))

    return canonical(expected) == canonical(actual) and (
        canonical(expected) != _surface_key(expected)
        or canonical(actual) != _surface_key(actual)
    )


def _italian_number_orthography_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "it" or case.kind not in {"cardinal", "currency", "year"}:
        return False
    # Do not use accent folding to excuse a Numeralform regression when the oracle
    # already carries the required final accent.
    if "tré" in expected and "tré" not in actual:
        return False

    expected_key = _surface_key(expected).replace("dicotto", "diciotto")
    actual_key = _surface_key(actual)
    # A compound ending in -tré takes the written accent. Do not strip an accent
    # inside a longer token such as *trentatrémila; there `tre` is not word-final.
    expected_key = re.sub(r"tré\b", "tre", expected_key)
    actual_key = re.sub(r"tré\b", "tre", actual_key)
    expected_key = re.sub("cento(?=(?:ottanta|ottant|otto|uno|undici))", "cent", expected_key)
    actual_key = re.sub("cento(?=(?:ottanta|ottant|otto|uno|undici))", "cent", actual_key)
    return expected_key == actual_key and (
        expected_key != _surface_key(expected)
        or actual_key != _surface_key(actual)
    )

def _italian_ordinal_oracle_quirk(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "it" or case.kind != "ordinal":
        return False
    value = case.python_value()
    repaired = _surface_key(expected).replace("dicottesimo", "diciottesimo").replace("diecesimo", "decimo")
    if value == 0:
        repaired = repaired.replace("zero", "zeresimo")
    elif isinstance(value, int) and value % 1000 == 0:
        repaired = repaired.replace("millesimo", "milesimo")
    return repaired != _surface_key(expected) and repaired == _surface_key(actual)

def _japanese_ordinal_numeric_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "ja" or case.kind != "ordinal_num":
        return False
    value = case.python_value()
    allowed = {f"第{value}", f"{value}番目"}
    return expected in allowed and actual in allowed


def _korean_ordinal_numeric_spacing_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "ko" or case.kind != "ordinal_num":
        return False

    def canonical(text: str) -> str:
        return re.sub(r"\s+(?=번째\b)", "", unicodedata.normalize("NFC", text).strip())

    return canonical(expected) == canonical(actual) and expected != actual


def _portuguese_ordinal_oracle_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "pt" or case.kind != "ordinal":
        return False
    repaired = _surface_key(expected)
    for oracle, canonical in _PT_ORDINAL_ORACLE_REPAIRS.items():
        repaired = _replace_phrase(repaired, oracle, canonical)
    return repaired != _surface_key(expected) and repaired == _surface_key(actual)
def _portuguese_zero_minor_omission_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "pt" or case.kind != "currency":
        return False
    value = case.python_value()
    if not isinstance(value, Decimal) or int((abs(value) * 100) % 100) != 0:
        return False
    expected_key = _currency_key(case, expected)
    actual_key = _currency_key(case, actual)
    if expected_key is None or actual_key is None or not actual_key.endswith(" zero <minor>"):
        return False
    repaired = actual_key.removesuffix(" zero <minor>")
    return repaired == expected_key and repaired != actual_key

def _russian_decimal_whole_agreement_oracle_quirk(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "ru" or case.kind != "decimal":
        return False
    value = case.python_value()
    number = case.as_decimal_number()
    whole = int(number.integer)
    expected_key = _surface_key(expected)
    repaired_expected = expected_key
    if whole % 10 == 1 and whole % 100 != 11:
        repaired_expected = _replace_phrase(repaired_expected, "целых", "целая")
    else:
        repaired_expected = _replace_phrase(repaired_expected, "целая", "целых")
    actual_key = _surface_key(actual)
    repaired_actual = actual_key
    if (
        isinstance(value, Decimal)
        and value < 0
        and whole == 0
        and not expected_key.startswith("минус ")
        and repaired_actual.startswith("минус ")
    ):
        repaired_actual = repaired_actual.removeprefix("минус ")
    return (
        repaired_expected != expected_key and repaired_expected == repaired_actual
    ) or (
        repaired_actual != actual_key and repaired_expected == repaired_actual
    )

def _swedish_optional_ett_ordinal_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "sv" or case.kind != "ordinal":
        return False
    allowed = {100: {"hundrade", "etthundrade"}, 1000: {"tusende", "etttusende"}}.get(
        case.python_value()
    )
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    if allowed is not None:
        return expected_key in allowed and actual_key in allowed and expected_key != actual_key
    value = case.python_value()
    if not isinstance(value, int) or value < 1000 or value % 1000 != 100:
        return False
    return (
        expected_key.endswith(" etthundrade")
        and actual_key.endswith("hundrade")
        and expected_key.removesuffix(" etthundrade") == actual_key.removesuffix("hundrade")
    )
def _swedish_oracle_orthography_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "sv":
        return False
    repaired = _surface_key(expected).replace("förtio", "fyrtio")
    return "".join(repaired.split()) == "".join(_surface_key(actual).split())


def _swedish_ordinal_oracle_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "sv" or case.kind != "ordinal":
        return False
    repaired = _surface_key(expected).replace("tjugode", "tjugonde")
    return repaired != _surface_key(expected) and "".join(repaired.split()) == "".join(_surface_key(actual).split())


def _thai_currency_connector_variant(case: RandomCase, expected: str, actual: str) -> bool:
    if (
        case.locale.split("-", 1)[0] != "th"
        or case.kind != "currency"
        or case.options.get("separator") is not None
    ):
        return False

    def canonical(text: str) -> str:
        return re.sub(r"\s+", "", unicodedata.normalize("NFC", text)).replace("และ", "")

    return canonical(expected) == canonical(actual) and expected != actual


_THAI_CURRENCY_UNITS = {
    "EUR": ("ยูโร", "เซนต์"),
    "USD": ("ดอลลาร์", "เซนต์"),
}


def _thai_zero_currency_component_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if (
        case.locale != "th"
        or case.kind != "currency"
        or case.options.get("separator") is not None
        or case.currency not in _THAI_CURRENCY_UNITS
    ):
        return False
    value = case.python_value()
    if not isinstance(value, Decimal):
        return False
    absolute = abs(value)
    major = int(absolute)
    minor = int((absolute * 100) % 100)
    major_name, minor_name = _THAI_CURRENCY_UNITS[case.currency]
    def canonical(text: str) -> str:
        return re.sub(r"\s+", "", unicodedata.normalize("NFC", text)).replace("และ", "")
    expected_key = canonical(expected)
    candidates = [canonical(actual)]
    if major == 0:
        component = f"ศูนย์{major_name}"
        candidates = [
            candidate.replace(component, "", 1)
            for candidate in candidates
            if component in candidate
        ] + candidates
    if minor == 0:
        component = f"ศูนย์{minor_name}"
        candidates = [
            candidate.replace(component, "", 1)
            for candidate in candidates
            if component in candidate
        ] + candidates
    actual_key = canonical(actual)
    return any(candidate == expected_key and candidate != actual_key for candidate in candidates)
def _vietnamese_negative_oracle_quirk(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "vi" or case.kind != "cardinal":
        return False
    value = case.python_value()
    if not isinstance(value, int) or not -20 <= value <= -1:
        return False
    if value == -20:
        correct = "âm hai mươi"
        oracle_bug = _VI_UNDER_20[0]
    else:
        correct = f"âm {_VI_UNDER_20[-value]}"
        oracle_bug = _VI_UNDER_20[20 + value]
    return _surface_key(expected) == _surface_key(oracle_bug) and _surface_key(actual) == _surface_key(correct)


def _rule_registry() -> tuple[tuple[str, Callable[[RandomCase, str, str], bool]], ...]:
    return (
        ("variant:cs-optional-one-million", _czech_optional_one_million_variant),
        ("oracle:de-year-einshundert", _german_year_einshundert_oracle_quirk),
        ("en-year-reading", _english_year_variant),
        ("oracle:de-post-2000-year", _german_post_2000_year_oracle_quirk),
        ("variant:de-optional-ein-ordinal", _german_optional_ein_ordinal_variant),
        ("decimal-trailing-zero-precision", _decimal_trailing_zero_precision_variant),
        ("oracle:es-ordinal-accent", _spanish_ordinal_accent_oracle_quirk),
        ("variant:es-ordinal-synonym", _spanish_ordinal_synonym_variant),
        ("oracle:es-gbp-gender", _spanish_gbp_gender_variant),
        ("oracle:es-nok-gender", _spanish_nok_gender_variant),
        ("variant:fi-compound-spacing", _finnish_compound_spacing_variant),
        ("oracle:fr-cent-overpluralization", _french_cent_oracle_quirk),
        ("oracle:fr-number-orthography", _french_oracle_orthography_quirk),
        ("variant:it-cento-elision", _italian_cento_elision_variant),
        ("oracle:it-ordinal-orthography", _italian_ordinal_oracle_quirk),
        ("oracle:it-number-orthography", _italian_number_orthography_variant),
        ("variant:ja-ordinal-notation", _japanese_ordinal_numeric_variant),
        ("variant:ko-ordinal-spacing", _korean_ordinal_numeric_spacing_variant),
        ("variant:pt-ordinal-orthography", _portuguese_ordinal_oracle_variant),
        ("variant:pt-zero-minor-omission", _portuguese_zero_minor_omission_variant),
        ("oracle:ru-decimal-whole-agreement", _russian_decimal_whole_agreement_oracle_quirk),
        ("variant:sv-optional-ett-ordinal", _swedish_optional_ett_ordinal_variant),
        ("oracle:sv-number-orthography", _swedish_oracle_orthography_variant),
        ("oracle:sv-ordinal-orthography", _swedish_ordinal_oracle_variant),
        ("variant:th-currency-connector", _thai_currency_connector_variant),
        ("variant:th-zero-currency-component", _thai_zero_currency_component_variant),
        ("oracle:vi-negative-cardinal", _vietnamese_negative_oracle_quirk),
    )


_VARIANT_RULES = _rule_registry()


def accepted_variant(
    case: RandomCase,
    expected: str,
    actual: str,
    *,
    difference_shape: str,
) -> str | None:
    """Return the named equivalence rule when a textual difference is acceptable."""
    if difference_shape in _SAFE_SURFACE_SHAPES:
        if _explicit_sign(expected) != _explicit_sign(actual):
            return None
        return f"surface:{difference_shape}"
    for name, predicate in _VARIANT_RULES:
        if predicate(case, expected, actual):
            if name == "decimal-trailing-zero-precision" and case.locale.split("-", 1)[0] == "en":
                return "en-decimal-trailing-zero-precision"
            return name
    if case.kind == "currency":
        expected_key = _currency_key(case, expected)
        actual_key = _currency_key(case, actual)
        if expected_key is not None and expected_key == actual_key:
            language = case.locale.split("-", 1)[0]
            return f"{language}-{case.currency.lower()}-currency"
    return None


__all__ = ["accepted_variant"]
