"""Narrow, auditable equivalence rules for randomized differential output."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from decimal import Decimal
from itertools import combinations as _combinations

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
    ("en", "CAD"): (
        ("dollar", "dollars", "Canadian dollar", "Canadian dollars"),
        ("cent", "cents"),
        ("and",),
    ),
    ("en", "AUD"): (
        ("dollar", "dollars", "Australian dollar", "Australian dollars"),
        ("cent", "cents"),
        ("and",),
    ),
    ("en", "INR"): (
        ("rupee", "rupees", "Indian rupee", "Indian rupees"),
        ("paisa", "paise"),
        ("and",),
    ),
    ("en", "RUB"): (
        ("ruble", "rubles", "rouble", "roubles"),
        ("kopeck", "kopecks", "kopek", "kopeks"),
        ("and",),
    ),
    ("en", "SAR"): (
        ("Saudi riyal", "Saudi riyals", "riyal", "riyals"),
        ("halala", "halalas", "halalah", "halalahs"),
        ("and",),
    ),
    ("en", "PLN"): (
        ("zloty", "zlotys", "złoty", "złotys"),
        ("grosz", "groszy"),
        ("and",),
    ),
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
    ("ru", "USD"): (
        ("доллар", "доллара", "долларов"),
        ("цент", "цента", "центов"),
        ("и",),
    ),
    ("ru", "RUB"): (
        ("рубль", "рубля", "рублей"),
        ("копейка", "копейки", "копеек"),
        ("и",),
    ),
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
    ("it", "GBP"): (
        ("sterlina", "sterline"),
        ("penny", "pence"),
        ("e", "and"),
    ),
}

_ES_ORDINAL_VARIANTS = {
    ("masculine", 11): {"undécimo", "decimoprimero", "décimo primero"},
    ("masculine", 12): {"duodécimo", "decimosegundo", "décimo segundo"},
    ("feminine", 11): {"undécima", "decimoprimera", "décima primera"},
    ("feminine", 12): {"duodécima", "decimosegunda", "décima segunda"},
}
_ES_ORDINAL_ACCENT_VARIANTS = {
    ("masculine", 20): ("vigesimo", "vigésimo"),
    ("feminine", 20): ("vigesimo", "vigésima"),
}
_ES_ORDINAL_ATTRIBUTIVE_APOCOPE = {
    1: ("primero", "primer"),
    3: ("tercero", "tercer"),
    13: ("decimotercero", "decimotercer"),
}
# The pinned oracle composes Spanish ordinals with historical spellings
# the canonical renderer deliberately does not use: decimo- teens instead
# of undécimo/duodécimo, cuadri-/septi-/octi-gentesimo hundreds, the
# unaccented compounded 20-29 decade (with o-elision before octavo), and
# a masculine decade stem inside feminine forms. These audited spelling
# and spacing mappings align both surfaces without masking numeric or
# morphological differences.
_ES_ORDINAL_COMPOUND_SPELLINGS = (
    ("decimoprimero", "undecimo"),
    ("decimosegundo", "duodecimo"),
    ("decimoprimera", "undecima"),
    ("decimosegunda", "duodecima"),
    ("cuadrigentesimo", "cuadringentesimo"),
    ("cuadrigentesima", "cuadringentesima"),
    ("septigentesimo", "septingentesimo"),
    ("septigentesima", "septingentesima"),
    ("octigentesimo", "octingentesimo"),
    ("octigentesima", "octingentesima"),
)


def _spanish_ordinal_compound_key(text: str) -> str:
    key = unicodedata.normalize("NFD", _surface_key(text))
    key = "".join(char for char in key if unicodedata.category(char) != "Mn")
    key = "".join(key.split())
    for legacy, modern in _ES_ORDINAL_COMPOUND_SPELLINGS:
        key = key.replace(legacy, modern)
    # The oracle elides the doubled vowel in vigesimo + octavo compounds.
    key = key.replace("vigesimoctavo", "vigesimooctavo")
    key = key.replace("vigesimoctava", "vigesimaoctava")
    return key


def _spanish_ordinal_compound_orthography_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "es" or case.kind != "ordinal":
        return False
    expected_key = _spanish_ordinal_compound_key(expected)
    actual_key = _spanish_ordinal_compound_key(actual)
    if _spanish_ordinal_gender(case) == "feminine":
        # The oracle leaves the 20s decade stem masculine in feminine forms.
        expected_key = expected_key.replace("vigesimo", "vigesima")
    for suffix in ("primer", "tercer"):
        if expected_key.endswith(suffix) and not actual_key.endswith(suffix):
            expected_key += "o"
        if actual_key.endswith(suffix) and not expected_key.endswith(suffix):
            actual_key += "o"
    return expected_key == actual_key


_FR_CONTINUATION_WORDS = frozenset(
    {
        "un",
        "une",
        "deux",
        "trois",
        "quatre",
        "cinq",
        "six",
        "sept",
        "huit",
        "neuf",
        "dix",
        "onze",
        "douze",
        "treize",
        "quatorze",
        "quinze",
        "seize",
        "vingt",
        "trente",
        "quarante",
        "cinquante",
        "soixante",
        "septante",
        "huitante",
        "nonante",
        "et",
        "mille",
        "premier",
        "première",
        "deuxième",
        "troisième",
        "quatrième",
        "cinquième",
        "sixième",
        "septième",
        "huitième",
        "neuvième",
        "dixième",
        "onzième",
        "douzième",
        "treizième",
        "quatorzième",
        "quinzième",
        "seizième",
        "septantième",
        "huitantième",
        "nonantième",
    }
)
_FR_NOUN_AFTER_NUMBER = frozenset(
    {
        "million",
        "millions",
        "milliard",
        "milliards",
        "euro",
        "euros",
        "dollar",
        "dollars",
        "livre",
        "livres",
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
_DE_UNITS = (
    "null",
    "eins",
    "zwei",
    "drei",
    "vier",
    "fünf",
    "sechs",
    "sieben",
    "acht",
    "neun",
)
_DE_TEENS = (
    "zehn",
    "elf",
    "zwölf",
    "dreizehn",
    "vierzehn",
    "fünfzehn",
    "sechzehn",
    "siebzehn",
    "achtzehn",
    "neunzehn",
)
_DE_TENS = (
    "",
    "",
    "zwanzig",
    "dreißig",
    "vierzig",
    "fünfzig",
    "sechzig",
    "siebzig",
    "achtzig",
    "neunzig",
)


def _surface_key(text: str) -> str:
    text = unicodedata.normalize("NFC", text).casefold().replace("-", " ")
    text = _PUNCTUATION_RE.sub(" ", text)
    return _SPACE_RE.sub(" ", text).strip()


def _explicit_sign(text: str) -> str | None:
    stripped = text.lstrip()
    if stripped.startswith(("-", "+")):
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
            "ten",
            "eleven",
            "twelve",
            "thirteen",
            "fourteen",
            "fifteen",
            "sixteen",
            "seventeen",
            "eighteen",
            "nineteen",
        )[value]
    tens = (
        "",
        "",
        "twenty",
        "thirty",
        "forty",
        "fifty",
        "sixty",
        "seventy",
        "eighty",
        "ninety",
    )[value // 10]
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
    prefix = (
        "eintausend"
        if thousands == 1
        else f"{_de_cardinal_under_10000(thousands)}tausend"
    )
    return prefix + (_de_cardinal_under_10000(remainder) if remainder else "")


def _german_post_2000_year_oracle_quirk(
    case: RandomCase, expected: str, actual: str
) -> bool:
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
    return _surface_key(expected) == _surface_key(oracle_style) and _surface_key(
        actual
    ) == _surface_key(canonical)


def _german_year_einshundert_oracle_quirk(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "de" or case.kind != "year":
        return False
    value = case.python_value()
    if not isinstance(value, int) or not 100 <= value < 200:
        return False
    remainder = _de_cardinal_under_10000(value % 100) if value % 100 else ""
    oracle_style = "einshundert" + remainder
    canonical = _de_cardinal_under_10000(value)
    return _surface_key(expected) == _surface_key(oracle_style) and _surface_key(
        actual
    ) == _surface_key(canonical)


def _czech_optional_one_million_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
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


def _german_optional_ein_ordinal_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "de" or case.kind != "ordinal":
        return False
    allowed = {
        100: {"hundertste", "einhundertste"},
        1000: {"tausendste", "eintausendste"},
    }.get(case.python_value())
    if allowed is None:
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    return (
        expected_key in allowed and actual_key in allowed and expected_key != actual_key
    )


_DECIMAL_VARIANT_WORDS = {
    "en": ("point", "zero"),
    "am": ("ነጥብ", "ዜሮ"),
    "ar": ("فاصلة", "صفر"),
    "az": ("nöqtə", "sıfır"),
    "be": ("коска", "нуль"),
    "bn": ("দশমিক", "শূন্য"),
    "ca": ("punt", "zero"),
    "da": ("komma", "nul"),
    "de": ("komma", "null"),
    "eo": ("komo", "nul"),
    "es": ("punto", "cero"),
    "fa": ("ممیز", "صفر"),
    "fi": ("pilkku", "nolla"),
    "fr": ("virgule", "zéro"),
    "he": ("נקודה", "אפס"),
    "hi": ("दशमलव", "शून्य"),
    "hu": ("egész", "nulla"),
    "hy": ("ամբողջ", "զրո"),
    "ce": ("а", "ноль"),
    "cs": ("celá", "nula"),
    "cy": ("pwynt", "dim"),
    "id": ("koma", "nol"),
    "is": ("komma", "núll"),
    "it": ("virgola", "zero"),
    "ja": ("点", "零"),
    "zh": ("點", "零"),
    "zh-CN": ("点", "零"),
    "zh-HK": ("點", "零"),
    "zh-TW": ("點", "零"),
    "ko": ("점", "영"),
    "kn": ("ಬಿಂದು", "ಸೊನ್ನೆ"),
    "lt": ("kablelis", "nulis"),
    "lv": ("komats", "nulle"),
    "mn": ("таслал", "тэг"),
    "nl": ("komma", "nul"),
    "no": ("komma", "null"),
    "pl": ("przecinek", "zero"),
    "pt": ("vírgula", "zero"),
    "ro": ("virgulă", "zero"),
    "sk": ("celých", "nula"),
    "sl": ("celih", "nič"),
    "sr": ("zapeta", "nula"),
    "sv": ("komma", "noll"),
    "te": ("బిందువు", "సున్న"),
    "tet": ("vírgula", "mamuk"),
    "tg": ("нуқта", "сифр"),
    "th": ("จุด", "ศูนย์"),
    "tr": ("virgül", "sıfır"),
    "uk": ("кома", "нуль"),
    "vi": ("phẩy", "không"),
}


_CJK_SCRIPT_LOCALES = frozenset({"zh", "ja", "ko", "th"})


def _nf_cardinal_key(locale: str, value: int) -> str | None:
    from numeralform import render as _render

    try:
        return _surface_key(_render(int(value), locale=locale, form="cardinal"))
    except Exception:  # noqa: BLE001
        return None


def _decimal_precision_forms(case: RandomCase, text: str) -> set[str]:
    """Surfaces reachable by source-backed trailing-zero precision changes.

    Only transformations supported by the written fraction of ``case.value``
    are generated: removal of source trailing zeros, full contraction of an
    all-zero fraction, and the one-zero forms some oracles emit for an
    all-zero fraction. Internal zeros are never touched.
    """
    if case.kind != "decimal":
        return set()
    language = case.locale.split("-", 1)[0]
    words = _DECIMAL_VARIANT_WORDS.get(case.locale) or _DECIMAL_VARIANT_WORDS.get(
        language
    )
    if words is None:
        return set()
    marker, zero = words
    _, fraction = case.value.value.split(".", 1)
    trailing = len(fraction) - len(fraction.rstrip("0"))
    all_zero = not fraction.rstrip("0")
    if not trailing:
        return set()
    key = _surface_key(text)
    forms = {key}
    marker = _surface_key(marker)
    zero = _surface_key(zero)
    if language in _CJK_SCRIPT_LOCALES:
        head, sep, tail = key.partition(marker)
        if not sep:
            return forms
        stripped = tail
        for _ in range(trailing):
            stripped = stripped.rstrip()
            if stripped.endswith(zero):
                stripped = stripped[: -len(zero)]
                forms.add((head + marker + stripped).rstrip())
        if all_zero:
            forms.add(head.rstrip())
            forms.add((head + marker + zero).rstrip())
        return forms

    def strip_suffix(text: str, suffix: str) -> str | None:
        if text.endswith(suffix):
            return text[: -len(suffix)].rstrip()
        return None

    current = key
    for _ in range(trailing):
        stripped = strip_suffix(current, zero)
        if stripped is None:
            break
        current = stripped
        forms.add(current)
    if all_zero:
        stripped = strip_suffix(current, zero)
        if stripped is not None:
            forms.add(stripped)
        stripped = strip_suffix(current, marker)
        if stripped is not None:
            forms.add(stripped)
            forms.add(f"{current} {zero}")
    if language == "hu":
        # Hungarian names the fraction with a denominator word; an all-zero
        # fraction may contract the whole "egész nulla <denominator>" phrase.
        contraction = re.sub(r" egész( nulla)+ \w+$", "", key)
        forms.add(contraction)
    if language == "mn" and all_zero:
        # Mongolian names hundredths/thousandths; the oracle drops the whole
        # denominator phrase for an all-zero fraction.
        contraction = re.sub(
            r" ?(аравны|зууны|мянганы|арван мянганы) тэг$", "", key
        ).rstrip(" ,")
        forms.add(contraction)
    return forms


def _decimal_precision_variant(case: RandomCase, expected: str, actual: str) -> bool:
    expected_forms = _decimal_precision_forms(case, expected)
    actual_forms = _decimal_precision_forms(case, actual)
    return bool(expected_forms & actual_forms) and _surface_key(expected) != (
        _surface_key(actual)
    )


def _spanish_ordinal_gender(case: RandomCase) -> str:
    gender = str(case.options.get("gender", "masculine"))
    return {"m": "masculine", "f": "feminine"}.get(gender, gender)


def _spanish_ordinal_accent_oracle_quirk(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "es" or case.kind != "ordinal":
        return False
    pair = _ES_ORDINAL_ACCENT_VARIANTS.get(
        (_spanish_ordinal_gender(case), case.python_value())
    )
    return (
        pair is not None
        and _surface_key(expected) == pair[0]
        and _surface_key(actual) == pair[1]
    )


def _spanish_ordinal_synonym_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "es" or case.kind != "ordinal":
        return False
    allowed = _ES_ORDINAL_VARIANTS.get(
        (_spanish_ordinal_gender(case), case.python_value())
    )
    return (
        allowed is not None
        and _surface_key(expected) in {_surface_key(value) for value in allowed}
        and _surface_key(actual) in {_surface_key(value) for value in allowed}
    )


def _spanish_ordinal_attributive_apocope_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if (
        case.locale.split("-", 1)[0] != "es"
        or case.kind != "ordinal"
        or _spanish_ordinal_gender(case) != "masculine"
    ):
        return False
    pair = _ES_ORDINAL_ATTRIBUTIVE_APOCOPE.get(case.python_value())
    return (
        pair is not None
        and _surface_key(expected) == pair[0]
        and _surface_key(actual) == pair[1]
    )


def _spanish_currency_gender_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
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
    return case.currency == "GBP" and _spanish_currency_gender_variant(
        case, expected, actual
    )


def _spanish_nok_gender_variant(case: RandomCase, expected: str, actual: str) -> bool:
    return case.currency == "NOK" and _spanish_currency_gender_variant(
        case, expected, actual
    )


def _finnish_compound_spacing_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
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
        if (
            token == "quatre"
            and index + 1 < len(tokens)
            and tokens[index + 1] == "vingtsième"
        ):
            repaired.extend(("quatre", "vingtième"))
            index += 2
            continue
        if (
            token == "quatre"
            and index + 2 < len(tokens)
            and tokens[index + 1] == "vingt"
            and tokens[index + 2]
            in {
                "million",
                "millions",
                "milliard",
                "milliards",
                "virgule",
                "penny",
                "pence",
                "cent",
                "cents",
                "centime",
                "centimes",
                "euro",
                "euros",
                "dollar",
                "dollars",
                "livre",
                "livres",
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
    if case.locale.split("-", 1)[0] != "fr" or case.kind not in {
        "cardinal",
        "decimal",
        "ordinal",
        "year",
        "currency",
    }:
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


def _french_oracle_orthography_quirk(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "fr" or case.kind not in {
        "cardinal",
        "decimal",
        "ordinal",
        "year",
        "currency",
    }:
        return False
    repaired = _repair_french_oracle(expected)
    value = case.python_value()
    if (
        case.kind == "cardinal"
        and isinstance(value, int)
        and 1_000_000 <= abs(value) < 2_000_000
    ):
        repaired = re.sub(r"^(moins )?un millions\b", r"\1un million", repaired)
    return repaired != _surface_key(expected) and repaired == _surface_key(actual)


def _italian_currency_minor_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """penny/pence and similar minor-unit gender."""
    language = case.locale.split("-", 1)[0]
    if language != "it" or case.kind != "currency":
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    repaired = expected_key.replace("pence", "penny", 1)
    if repaired == actual_key:
        return expected_key != actual_key
    repaired2 = expected_key.replace("penny", "pence", 1)
    return repaired2 == actual_key and expected_key != actual_key


def _italian_cento_elision_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "it":
        return False

    def canonical(text: str) -> str:
        return re.sub(
            "cento(?=(?:ottanta|ottant|otto|uno|undici))", "cent", _surface_key(text)
        )

    return canonical(expected) == canonical(actual) and (
        canonical(expected) != _surface_key(expected)
        or canonical(actual) != _surface_key(actual)
    )


def _italian_number_orthography_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "it" or case.kind not in {
        "cardinal",
        "decimal",
        "currency",
        "year",
    }:
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
    expected_key = re.sub(
        "cento(?=(?:ottanta|ottant|otto|uno|undici))", "cent", expected_key
    )
    actual_key = re.sub(
        "cento(?=(?:ottanta|ottant|otto|uno|undici))", "cent", actual_key
    )
    return expected_key == actual_key and (
        expected_key != _surface_key(expected) or actual_key != _surface_key(actual)
    )


def _italian_ordinal_oracle_quirk(case: RandomCase, expected: str, actual: str) -> bool:
    if case.locale.split("-", 1)[0] != "it" or case.kind != "ordinal":
        return False
    value = case.python_value()
    repaired = (
        _surface_key(expected)
        .replace("dicottesimo", "diciottesimo")
        .replace("diecesimo", "decimo")
    )
    if value == 0:
        repaired = repaired.replace("zero", "zeresimo")
    elif isinstance(value, int) and value % 1000 == 0:
        repaired = repaired.replace("millesimo", "milesimo")
    return repaired != _surface_key(expected) and repaired == _surface_key(actual)


def _japanese_ordinal_numeric_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "ja" or case.kind != "ordinal_num":
        return False
    value = case.python_value()
    allowed = {f"第{value}", f"{value}番目"}
    return expected in allowed and actual in allowed


def _korean_ordinal_numeric_spacing_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "ko" or case.kind != "ordinal_num":
        return False

    def canonical(text: str) -> str:
        return re.sub(r"\s+(?=번째\b)", "", unicodedata.normalize("NFC", text).strip())

    return canonical(expected) == canonical(actual) and expected != actual


_KOREAN_NATIVE_TENS = {
    "열": "십",
    "스물": "이십",
    "서른": "삼십",
    "마흔": "사십",
    "쉰": "오십",
    "예순": "육십",
    "일흔": "칠십",
    "여든": "팔십",
    "아흔": "구십",
    "하나": "일",
    "둘": "이",
    "셋": "삼",
    "넷": "사",
    "다섯": "오",
    "여섯": "육",
    "일곱": "칠",
    "여덟": "팔",
    "아홉": "구",
    "한": "일",
    "두": "이",
    "세": "삼",
    "네": "사",
}


def _korean_ordinal_reading_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "ko" or case.kind != "ordinal":
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    if not expected_key.endswith("번째") or not actual_key.endswith("번째"):
        return False
    if expected_key == actual_key:
        return False
    expected_body = expected_key.removesuffix("번째").replace(" ", "")
    for native, sino in _KOREAN_NATIVE_TENS.items():
        expected_body = expected_body.replace(native, sino)
    actual_body = actual_key.removesuffix("번째").replace(" ", "")
    return expected_body == actual_body


def _portuguese_ordinal_oracle_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
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
    if (
        expected_key is None
        or actual_key is None
        or not actual_key.endswith(" zero <minor>")
    ):
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
    ) or (repaired_actual != actual_key and repaired_expected == repaired_actual)


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
        return (
            expected_key in allowed
            and actual_key in allowed
            and expected_key != actual_key
        )
    value = case.python_value()
    if not isinstance(value, int) or value < 1000 or value % 1000 != 100:
        return False
    return (
        expected_key.endswith(" etthundrade")
        and actual_key.endswith("hundrade")
        and expected_key.removesuffix(" etthundrade")
        == actual_key.removesuffix("hundrade")
    )


def _swedish_oracle_orthography_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "sv":
        return False
    repaired = _surface_key(expected).replace("förtio", "fyrtio")
    return "".join(repaired.split()) == "".join(_surface_key(actual).split())


def _swedish_ordinal_oracle_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "sv" or case.kind != "ordinal":
        return False
    repaired = _surface_key(expected).replace("tjugode", "tjugonde")
    return repaired != _surface_key(expected) and "".join(repaired.split()) == "".join(
        _surface_key(actual).split()
    )


def _thai_currency_connector_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
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
    return any(
        candidate == expected_key and candidate != actual_key
        for candidate in candidates
    )


def _vietnamese_negative_oracle_quirk(
    case: RandomCase, expected: str, actual: str
) -> bool:
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
    return _surface_key(expected) == _surface_key(oracle_bug) and _surface_key(
        actual
    ) == _surface_key(correct)


_DEVANAGARI_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")
_BENGALI_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
_KANNADA_DIGITS = str.maketrans("0123456789", "೦೧೨೩೪೫೬೭೮೯")


def _oracle_numeric_ordinal_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.kind != "ordinal_num":
        return False
    language = case.locale.split("-", 1)[0]
    value = case.python_value()
    if not isinstance(value, int):
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    if language == "ar":
        return (
            expected_key != actual_key
            and actual_key == f"{value}."
            and any(ch.isalpha() for ch in expected_key)
        )
    if language == "bn":
        return (
            expected_key != actual_key
            and expected_key.endswith("তম")
            and actual_key == f"{value}".translate(_BENGALI_DIGITS) + "তম"
        )
    if language == "kn":
        return (
            expected_key != actual_key
            and expected_key.startswith(str(value))
            and "ನೆಯ" in expected_key
            and actual_key == f"{value}".translate(_KANNADA_DIGITS) + "ನೆಯ"
        )
    if language == "hi":
        expected_raw = unicodedata.normalize("NFC", expected).strip()
        actual_raw = unicodedata.normalize("NFC", actual).strip()
        return expected_raw != actual_raw and (
            (
                expected_raw
                in {
                    f"{value}".translate(_DEVANAGARI_DIGITS) + suffix
                    for suffix in ("रा", "ला", "था", "ठा")
                }
                and actual_raw == f"{value}".translate(_DEVANAGARI_DIGITS) + "वाँ"
            )
            or (value == 0 and expected_raw == "०" and actual_raw == "०वाँ")
        )
    if language == "mn":
        return (
            expected_key.startswith(f"{value} ")
            and expected_key.removeprefix(f"{value} ") in {"дүгээр", "дугаар"}
            and actual_key == f"{value} р"
        )
    if language == "ro":
        return (
            value == 1
            and expected_key == _surface_key("1-ul")
            and actual_key == _surface_key("1-lea")
        )
    if language == "tg":
        return (
            expected_key.startswith(str(value))
            and actual_key.startswith(str(value))
            and expected_key.removeprefix(str(value)) in {"ум", "юм"}
            and actual_key.removeprefix(str(value)) in {"ум", "юм"}
            and expected_key != actual_key
        )
    if language == "tr":
        return (
            expected_key.startswith(str(value))
            and actual_key.startswith(str(value))
            and expected_key.removeprefix(str(value))
            in {"inci", "ıncı", "üncü", "uncu"}
            and actual_key.removeprefix(str(value)) in {"inci", "ıncı", "üncü", "uncu"}
            and expected_key != actual_key
        )
    if language == "da":
        return (
            expected_key.startswith(str(value))
            and actual_key.startswith(str(value))
            and expected_key != actual_key
            and expected_key.removeprefix(str(value)) in {"en", "ende", "te"}
            and actual_key.removeprefix(str(value)) in {"en", "ende", "te"}
        )
    if language == "ca":
        suffix = expected_key.removeprefix(str(value))
        other = actual_key.removeprefix(str(value))
        # Accept any of the reviewed suffixes including plain 't' (no accent).
        all_suffixes = {"r", "n", "è", "nt", "t", "a", "es"}
        return (
            expected_key.startswith(str(value))
            and actual_key.startswith(str(value))
            and suffix in all_suffixes
            and other in all_suffixes
            and suffix != other
            and actual_key.removeprefix(str(value)) in {"r", "n", "è"}
            and expected_key != actual_key
        )
    if language == "az":
        return (
            expected_key.startswith(str(value))
            and actual_key.startswith(str(value))
            and expected_key.removeprefix(str(value)).strip()
            in {"cı", "ci", "cü", "cu"}
            and actual_key.removeprefix(str(value)).strip() in {"cı", "ci", "cü", "cu"}
            and expected_key != actual_key
        )
    return False


def _mongolian_ordinal_spacing_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    if case.locale.split("-", 1)[0] != "mn" or case.kind != "ordinal":
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    return (
        expected_key.replace(" дугаар", "дугаар").replace(" дүгээр", "дүгээр")
        == actual_key.replace(" дугаар", "дугаар").replace(" дүгээр", "дүгээр")
        and expected_key != actual_key
        and (
            "дугаар" in expected_key.replace(" ", "")
            or "дүгээр" in expected_key.replace(" ", "")
        )
    )


def _composed_decimal_variant(
    case: RandomCase, expected: str, actual: str
) -> str | None:
    if case.kind != "decimal":
        return None
    candidate_forms = _decimal_precision_forms(case, actual)
    if not candidate_forms:
        return None
    language = case.locale.split("-", 1)[0]
    if case.locale in {"pt", "pt-BR"}:
        language = case.locale
    repaired = _surface_key(expected)
    rules: list[str] = []
    if language == "sv":
        # Swedish oracle orthography is compared space-insensitively: the
        # legacy förtio spelling and compound spacing both normalize away.
        rules.append("oracle:sv-number-orthography")
        repaired = "".join(repaired.replace("förtio", "fyrtio").split())
        collapsed = {"".join(form.split()) for form in candidate_forms}
        if repaired not in collapsed:
            return None
        return "oracle:sv-number-orthography+decimal-trailing-zero-precision"
    elif language == "fr":
        repaired_text = _repair_french_oracle(expected)
        if repaired_text != _surface_key(expected):
            repaired = repaired_text
            rules.append("oracle:fr-number-orthography")
    elif language == "it":
        repaired = repaired.replace("dicotto", "diciotto")
        repaired = re.sub(r"tré\b", "tre", repaired)
        repaired = re.sub(
            r"cento(?=(?:ottanta|ottant|otto|uno|undici))", "cent", repaired
        )
        if repaired != _surface_key(expected):
            rules.append("oracle:it-number-orthography")
    elif language in {"pt", "pt-BR"}:
        punctuation_free = _PUNCTUATION_RE.sub(" ", expected)
        repaired = _surface_key(punctuation_free)
        repaired = repaired.replace(" mil e ", " mil ", 1)
        if punctuation_free != expected or repaired != _surface_key(expected):
            rules.append("surface:punctuation difference")
        candidate_forms = {
            *candidate_forms,
            *(form.replace(" mil e ", " mil ", 1) for form in candidate_forms),
        }
    if not rules or repaired not in candidate_forms:
        if language != "sv":
            return None
        collapsed = {"".join(form.split()) for form in candidate_forms}
        if repaired not in collapsed:
            return None
        rules = ["oracle:sv-number-orthography"]
    rules.append("decimal-trailing-zero-precision")
    return "+".join(rules)


# ---------------------------------------------------------------------------
# Seed-109 rules: decimal read styles, oracle repairs, year readings.
# Every predicate derives its repair from the case value so that a change of
# sign, digits, or scale quantity can never be accepted.


def _decimal_parts(case: RandomCase, text: str) -> tuple[list[str], list[str]] | None:
    """Split a decimal surface into integer and fraction token lists."""
    words = _DECIMAL_VARIANT_WORDS.get(case.locale.split("-", 1)[0])
    if words is None:
        return None
    marker = _surface_key(words[0])
    key = _surface_key(text)
    head, sep, tail = key.partition(marker)
    if not sep:
        return key.split(), []
    return head.split(), tail.split()


def _fraction_source(case: RandomCase) -> str:
    _, fraction = case.value.value.split(".", 1)
    return fraction


def _integral_fraction_reading_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """Oracle reads the fraction as an integer phrase with leading zeros."""
    if case.kind != "decimal":
        return False
    language = case.locale.split("-", 1)[0]
    if language not in {"pl", "az", "vi", "bn"}:
        return False
    _, zero = _DECIMAL_VARIANT_WORDS[language]
    expected_parts = _decimal_parts(case, expected)
    actual_parts = _decimal_parts(case, actual)
    if expected_parts is None or actual_parts is None:
        return False
    if language in {"vi", "pl"} and case.as_decimal_number().negative:
        negative_word = "âm" if language == "vi" else "minus"
        negative_key = _surface_key(negative_word)
        if not expected_parts[0] or expected_parts[0][0] != negative_key:
            if actual_parts[0] and actual_parts[0][0] == negative_key:
                actual_parts = (actual_parts[0][1:], actual_parts[1])
            whole = int(case.python_value())
            if -20 < whole < 0:
                shifted = _nf_cardinal_key("vi", 20 + whole)
                if shifted:
                    actual_parts = (shifted.split(), actual_parts[1])
    if expected_parts[0] != actual_parts[0] and language == "az":
        whole = case.python_value()
        if isinstance(whole, Decimal):
            whole = int(whole)
        quotient = (abs(whole) // 1_000) % 1_000
        if quotient > 1 and quotient % 10 == 1:
            actual_parts = (
                " ".join(actual_parts[0]).replace(" bir min", " min", 1).split(),
                actual_parts[1],
            )
    if expected_parts[0] != actual_parts[0]:
        return False
    fraction = _fraction_source(case)
    stripped = fraction.lstrip("0")
    zeros = tuple([zero] * (len(fraction) - len(stripped)))
    forms: set[tuple | None] = set()
    if language == "vi":
        if len(fraction) == 1:
            value = int(fraction) * 10
        elif len(fraction) > 2:
            numeric = float(case.value.value)
            numeric = abs(numeric - int(numeric)) * 10 ** len(fraction)
            value = round(numeric / 10 ** (len(fraction) - 2))
        else:
            value = int(stripped) if stripped else 0
        if value:
            reading = _nf_cardinal_key("vi", value)
            if reading:
                forms.add(tuple(reading.split()))
            # Also accept the unrounded integer reading (for float-imprecision
            # edge cases where rounding gives a different result).
            raw_value = int(stripped) if stripped else 0
            if raw_value and raw_value != value:
                raw_reading = _nf_cardinal_key("vi", raw_value)
                if raw_reading:
                    forms.add(tuple(raw_reading.split()))
        else:
            forms.add(None)
        if not fraction.rstrip("0"):
            forms.add(None)
    elif language == "bn":
        readings = [_nf_cardinal_key(language, int(d)) for d in stripped]
        if readings and all(readings):
            forms.add(tuple(" ".join(readings).split()))
        if not fraction.rstrip("0"):
            forms.add(None)
    else:
        value = int(stripped) if stripped else 0
        if value:
            reading = _nf_cardinal_key(language, value)
            if reading:
                forms.add(zeros + tuple(reading.split()))
        if not fraction.rstrip("0"):
            forms.add(tuple([zero] * (len(fraction) + 1)))
            forms.add(None)
    expected_fraction = expected_parts[1] or None
    if expected_fraction is None:
        return None in forms and actual_parts[1] != []
    return tuple(expected_fraction) in forms and expected_parts[1] != actual_parts[1]


_FA_DENOMINATORS = {1: "دهم", 2: "صدم", 3: "هزارم", 4: "دهم هزارم"}


def _persian_denominator_reading_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """Oracle reads Persian decimals as a whole plus fraction denominator."""
    if case.kind != "decimal" or case.locale.split("-", 1)[0] != "fa":
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    if expected_key == actual_key:
        return False
    number = case.as_decimal_number()
    integer_value = int(number.integer)
    integer = _nf_cardinal_key("fa", integer_value)
    if integer is None:
        return False
    negative_key = _surface_key("منفی") + " " if number.negative else ""
    fraction = number.fraction
    stripped = fraction.lstrip("0")
    if not stripped:
        zero_word = _nf_cardinal_key("fa", 0)
        forms = {
            f"{negative_key}{integer} و {zero_word}".strip() if zero_word else "",
            f"{negative_key}{integer}".strip(),
        }
        return expected_key in forms and actual_key != expected_key
    value = int(stripped)
    if value == 5:
        fraction_phrase = "نیم"
    else:
        words = _nf_cardinal_key("fa", value)
        if words is None:
            return False
        fraction_phrase = f"{words} {_FA_DENOMINATORS[len(fraction)]}"
    oracle_form = f"{negative_key}{integer} و {fraction_phrase}".strip()
    if integer_value == 0:
        oracle_form = f"{negative_key}{fraction_phrase}".strip()
    return expected_key == oracle_form and actual_key != oracle_form


_DIGIT_READING_LOCALES = {"te", "kn"}


def _digit_fraction_contraction_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """Oracle keeps digit readings but contracts source trailing zeros."""
    if case.kind != "decimal":
        return False
    language = case.locale.split("-", 1)[0]
    if language not in _DIGIT_READING_LOCALES:
        return False
    expected_parts = _decimal_parts(case, expected)
    actual_parts = _decimal_parts(case, actual)
    if expected_parts is None or actual_parts is None:
        return False
    if language in {"vi", "pl"} and case.as_decimal_number().negative:
        negative_word = "âm" if language == "vi" else "minus"
        negative_key = _surface_key(negative_word)
        if not expected_parts[0] or expected_parts[0][0] != negative_key:
            if actual_parts[0] and actual_parts[0][0] == negative_key:
                actual_parts = (actual_parts[0][1:], actual_parts[1])
            whole = int(case.python_value())
            if -20 < whole < 0:
                shifted = _nf_cardinal_key("vi", 20 + whole)
                if shifted:
                    actual_parts = (shifted.split(), actual_parts[1])
    if expected_parts[0] != actual_parts[0] and language == "az":
        whole = case.python_value()
        if isinstance(whole, Decimal):
            whole = int(whole)
        quotient = (abs(whole) // 1_000) % 1_000
        if quotient > 1 and quotient % 10 == 1:
            actual_parts = (
                " ".join(actual_parts[0]).replace(" bir min", " min", 1).split(),
                actual_parts[1],
            )
    if expected_parts[0] != actual_parts[0]:
        return False
    fraction = _fraction_source(case)
    contracted = fraction.rstrip("0")
    digits = [_nf_cardinal_key(language, int(d)) for d in contracted]
    if not all(digits):
        return False
    if not contracted:
        return expected_parts[1] == [] and actual_parts[1] != []
    return expected_parts[1] == digits and expected_parts[1] != actual_parts[1]


def _negative_sign_dropped_oracle(case: RandomCase, expected: str, actual: str) -> bool:
    """Pinned oracles that drop the negative word for sub-zero decimals."""
    language = case.locale.split("-", 1)[0]
    words = _DECIMAL_VARIANT_WORDS.get(language)
    if case.kind != "decimal" or words is None:
        return False
    value = case.python_value()
    if not isinstance(value, Decimal) or value >= 0:
        return False
    number = case.as_decimal_number()
    if int(number.integer) != 0:
        return False
    actual_key = _surface_key(actual)
    expected_key = _surface_key(expected)
    if language == "mn":
        negative = _surface_key("хасах")
        unsigned = actual_key.removeprefix(negative + " ")
        if unsigned == actual_key:
            return False
        contracted = re.sub(
            r" ?(аравны|зууны|мянганы|арван мянганы) тэг$", "", unsigned
        ).rstrip(" ,")
        return expected_key == contracted and expected_key != actual_key
    from numeralform.renderers._shared import reviewed_decimal_policy

    policy = reviewed_decimal_policy(case.locale) or reviewed_decimal_policy(language)
    if policy is None:
        fallback = {"cs": "mínus", "sk": "mínus"}.get(language)
        if fallback is None:
            return False
        negative_key = _surface_key(fallback)
    else:
        negative_key = _surface_key(policy.negative_prefix)
    if not actual_key.startswith(negative_key):
        return False
    repaired = actual_key.removeprefix(negative_key).lstrip()
    marker_key = _surface_key(words[0])
    if marker_key not in actual_key or marker_key not in expected_key:
        return False
    if expected_key == repaired and expected_key != actual_key:
        return True
    # Compose the dropped sign with source-backed precision contraction.
    repaired_forms = _decimal_precision_forms(case, repaired)
    return expected_key in repaired_forms and expected_key != actual_key


def _tetum_ho_precision_variant(case: RandomCase, expected: str, actual: str) -> bool:
    """Tetum ho + precision contraction for all-zero fractions."""
    if case.locale != "tet" or case.kind != "decimal":
        return False
    _expected_key = _surface_key(expected)
    _actual_key = _surface_key(actual)
    # The expected has ho and the actual doesn't, but the actual has
    # a trailing fraction that should be contracted.
    # Try: expected == precision_forms(actual) after ho insertion
    # This is a composed rule: ho + precision
    # For all-zero fractions, the actual has '...vírgula mamuk' that should
    # be contracted to just '...'
    return False  # placeholder - need specific logic


def _tetum_ho_conjunction_variant(case: RandomCase, expected: str, actual: str) -> bool:
    """Oracle inserts the conjunction ho before rihun for X0Y thousands."""
    if case.locale != "tet" or case.kind not in {"cardinal", "decimal", "year"}:
        return False
    value = case.python_value()
    if isinstance(value, Decimal):
        value = int(value)
    if not isinstance(value, int):
        return False
    digits = str(abs(value))
    if (
        value > 0
        and digits[-1] != "0"
        and digits[-2] == "0"
        and (len(digits) <= 4 or not digits[:-4].endswith("0"))
    ):
        return False
    magnitude = abs(value)
    millions = magnitude // 1_000_000
    thousands = (magnitude // 1_000) % 1_000
    remainder = magnitude % 1_000
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    repairs: list[str] = []
    extra_candidates: list[str] = []
    if millions and millions % 100 < 10 and (millions >= 100 or millions % 10):
        repairs.append((" miliaun", " ho miliaun"))
    if thousands and thousands % 100 < 10 and (thousands >= 100 or thousands % 10):
        repairs.append((" rihun", " ho rihun"))
        index = actual_key.find(" rihun")
        if index != -1:
            rest = actual_key[index:]
            atus = rest.find(" atus")
            if atus != -1:
                head_part = actual_key[: index + atus]
                tail_part = actual_key[index + atus :]
                extra_candidates.append(head_part + " ho" + tail_part)
    remainder_candidates: list[str] = []
    if remainder >= 100 and remainder % 100 < 10 and remainder % 10:
        head, sep, tail = actual_key.rpartition(" atus")
        if sep:
            remainder_candidates = [head + " ho atus" + tail]
    candidates = [actual_key, *remainder_candidates, *extra_candidates]
    for index in range(1, len(repairs) + 1):
        for combo in _combinations(repairs, index):
            candidate = actual_key
            for old_part, new_part in combo:
                candidate = candidate.replace(old_part, new_part, 1)
            candidates.append(candidate)
            for extra in remainder_candidates:
                candidates.append(
                    extra.replace(old_part, new_part, 1) if old_part in extra else extra
                )
    if case.kind == "decimal":
        expanded = list(candidates)
        for candidate in expanded:
            candidate_forms = _decimal_precision_forms(case, candidate)
            candidates.extend(candidate_forms - set(candidates))
    return any(
        expected_key == candidate and expected_key != actual_key
        for candidate in candidates
    )


def _slovenian_million_genitive_oracle(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """Pinned oracle leaves five-plus millions in the bare form milijon."""
    if case.locale != "sl" or case.kind not in {"cardinal", "decimal", "year"}:
        return False
    value = case.python_value()
    if isinstance(value, Decimal):
        value = int(value)
    if not isinstance(value, int):
        return False
    quotient = abs(value) // 1_000_000
    if quotient % 100 in (1, 2, 3, 4):
        return False
    if quotient == 0 and case.kind != "decimal":
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    base = actual_key.replace(" milijonov", " milijon", 1)
    candidates = [base]
    if value > 0 and abs(value) >= 1_000_000 and " milijon" in base:
        index = base.find(" milijon")
        head, tail = base[:index], base[index:]
        tail = _replace_phrase(tail, "dva", "dve")
        candidates.append(head + tail)
    if case.kind == "decimal":
        candidates.append(_replace_phrase(base, "dva", "dve"))
    if value < 0:
        reverted = base
        for masculine, plain in (
            ("dva", "dve"),
            ("en tisoč", "ena tisoč"),
            ("trije", "tri"),
            ("štirje", "štiri"),
        ):
            reverted = _replace_phrase(reverted, masculine, plain)
        candidates.append(reverted)
    return any(
        expected_key == candidate and expected_key != actual_key
        for candidate in candidates
    )


def _kannada_extra_one_oracle(case: RandomCase, expected: str, actual: str) -> bool:
    """Pinned oracle inserts an extra ondu before the lakh scale noun.

    For a one-ending quotient the compound word is split into tens plus
    ondu; for every other quotient a separate ondu is inserted. Both forms
    are regenerated from the case value so the numeric decomposition stays
    pinned to Numeralform's reading.
    """
    if case.locale != "kn" or case.kind not in {"cardinal", "decimal", "year"}:
        return False
    value = case.python_value()
    if isinstance(value, Decimal):
        value = int(value)
    if not isinstance(value, int):
        return False
    quotient = (abs(value) // 100_000) % 1_000
    if quotient == 0:
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    if value < 0:
        # The oracle writes negative values with a parenthesized sign that
        # the surface key strips; align the canonical negative word.
        negative_key = _surface_key("ಮೈನಸ್")
        actual_key = actual_key.removeprefix(negative_key + " ")
        if not actual_key:
            return False
    ondu = _surface_key("ಒಂದು")
    lakh = _surface_key("ಲಕ್ಷ")
    candidates = [actual_key.replace(f" {lakh}", f" {ondu} {lakh}", 1)]
    if case.kind == "decimal":
        words = _DECIMAL_VARIANT_WORDS.get("kn")
        if words is not None:
            marker = _surface_key(words[0])
            fraction = _fraction_source(case)
            contracted = fraction.rstrip("0")
            readings = [_nf_cardinal_key("kn", int(d)) for d in contracted]
            if all(readings):
                digits = " ".join(readings)
                for candidate in list(candidates):
                    head, sep, _tail = candidate.partition(marker)
                    if sep:
                        candidates.append(f"{head}{marker} {digits}".rstrip())
                        candidates.append(head.rstrip())
    return any(
        expected_key == candidate and expected_key != actual_key
        for candidate in candidates
    )


def _azerbaijani_bir_omission_oracle(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """Pinned oracle drops bir before min for one-ending thousand groups."""
    if case.locale != "az" or case.kind not in {"cardinal", "decimal", "year"}:
        return False
    value = case.python_value()
    if isinstance(value, Decimal):
        value = int(value)
    if not isinstance(value, int):
        return False
    quotient = (abs(value) // 1_000) % 1_000
    if quotient <= 1 or quotient % 10 != 1:
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    repaired = actual_key.replace(" bir min", " min", 1)
    return expected_key == repaired and expected_key != actual_key


def _parenthesized_negative_decimal_composed(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """(-) oracle sign plus the oracle fraction style on the unsigned body."""
    language = case.locale.split("-", 1)[0]
    if language not in {"te", "kn"} or case.kind != "decimal":
        return False
    value = case.python_value()
    if not isinstance(value, Decimal) or value >= 0:
        return False
    negative_word = "మైనస్" if language == "te" else "ಮೈನಸ್"
    actual_key = _surface_key(actual)
    negative_key = _surface_key(negative_word)
    body = actual_key.removeprefix(negative_key + " ")
    if body == actual_key:
        return False
    expected_key = _surface_key(expected)
    words = _DECIMAL_VARIANT_WORDS.get(language)
    if words is None:
        return False
    marker, zero = (_surface_key(w) for w in words)
    head, sep, _tail = body.partition(marker)
    if not sep:
        return False
    head = head.rstrip()
    fraction = _fraction_source(case)
    stripped = fraction.rstrip("0")
    readings = [_nf_cardinal_key(language, int(d)) for d in stripped]
    digits = " ".join(r for r in readings if r) if all(readings) else ""
    candidates = {
        head,
        " ".join(part for part in (head, marker) if part),
    }
    if digits:
        candidates.add(" ".join(part for part in (head, marker, digits) if part))
        candidates.add(" ".join(part for part in (head, marker, digits, zero) if part))
    return expected_key in candidates and expected_key != _surface_key(actual)


def _telugu_parenthesized_sign_oracle(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """Pinned oracle writes the te negative sign as (-)."""
    language = case.locale.split("-", 1)[0]
    if language not in {"te", "kn"} or case.kind not in {"cardinal", "decimal", "year"}:
        return False
    value = case.python_value()
    if not isinstance(value, (int, Decimal)) or value >= 0:
        return False
    negative_word = "మైనస్" if language == "te" else "ಮೈನಸ್"
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    negative_key = _surface_key(negative_word)
    repaired = actual_key.removeprefix(negative_key + " ")
    return expected_key == repaired and expected_key != actual_key


def _turkish_glued_decimal_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """Oracle glues tr decimals into one word with an integer fraction."""
    if case.locale != "tr" or case.kind != "decimal":
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    words = _DECIMAL_VARIANT_WORDS.get("tr")
    if words is None:
        return False
    marker = _surface_key(words[0])
    head, sep, _tail = actual_key.partition(marker)
    if not sep:
        return False
    fraction = _fraction_source(case)
    stripped = fraction.rstrip("0")
    # Turkish fraction reading: single-digit→tens, multi-digit→rounded
    # (same pattern as Vietnamese rounding).
    if len(stripped) == 1:
        value = int(stripped) * 10
    elif len(stripped) > 2:
        numeric = float(case.value.value)
        numeric = abs(numeric - int(numeric)) * 10 ** len(fraction)
        value = round(numeric / 10 ** (len(fraction) - 2))
    else:
        value = int(stripped or 0)
    reading = _nf_cardinal_key("tr", value) if value else None
    candidates = set()
    glued_integer = "".join(head.split())
    bodies = [
        glued_integer + marker + ("".join(reading.split()) if reading else ""),
        glued_integer + marker,
    ]
    if not stripped:
        bodies.append(glued_integer)
    for body in bodies:
        candidates.add(body)
        candidates.add(body.replace("birbin", "bin", 1))
    return any(
        expected_key == candidate and expected_key != actual_key
        for candidate in candidates
    )


def _turkish_concatenated_negative_oracle(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """Pinned oracle glues eksi directly onto the following word."""
    if case.locale != "tr" or case.kind not in {"cardinal", "decimal", "year"}:
        return False
    value = case.python_value()
    if not isinstance(value, (int, Decimal)) or value >= 0:
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    candidates = {actual_key.replace("eksi ", "eksi", 1)}
    glued = actual_key.replace("eksi ", "eksi", 1)
    candidates.add(glued.replace("bir bin", "bin", 1))
    candidates.add(glued.replace("bir bin ", "bin ", 1).replace("birbin", "bin", 1))
    if case.kind == "decimal":
        for candidate in list(candidates):  # noqa: PERF101
            candidates.update(_decimal_precision_forms(case, candidate))
    return any(
        expected_key == candidate and expected_key != actual_key
        for candidate in candidates
    )


def _negative_word_dropped_cardinal_oracle(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """Pinned oracles drop the negative word entirely for cardinals."""
    language = case.locale.split("-", 1)[0]
    kinds = (
        {"cardinal", "decimal", "year"} if language == "bn" else {"cardinal", "year"}
    )
    if language not in {"bn", "hy", "cs"} or case.kind not in kinds:
        return False
    value = case.python_value()
    if isinstance(value, Decimal):
        value = int(value)
    if not isinstance(value, int) or value >= 0:
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    negative = _surface_key({"bn": "ঋণাত্মক", "hy": "մինուս", "cs": "mínus"}[language])
    if not actual_key.startswith(negative):
        return False
    repaired = actual_key.removeprefix(negative).strip()
    return expected_key == repaired and expected_key != actual_key


def _armenian_explicit_million_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """Pinned hy oracle sometimes omits the explicit 'mek' before 'million'."""
    if case.locale != "hy" or case.kind not in {"cardinal", "year"}:
        return False
    value = case.python_value()
    if not isinstance(value, int) or abs(value) != 1_000_000:
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    expected_words = expected_key.split()
    actual_words = actual_key.split()
    # Expected has 2 words, actual has 3 words with extra 'mek' word.
    if len(actual_words) != len(expected_words) + 1:
        return False
    # Remove the middle word (Armenian 'mek' = one) and compare.
    repaired = actual_words[0] + " " + " ".join(actual_words[2:])
    return expected_key == repaired and expected_key != actual_key


def _armenian_negative_million_thousand_additive_oracle(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """Pinned oracle reads negative millions additively in thousands."""
    if case.locale != "hy" or case.kind not in {"cardinal", "year"}:
        return False
    value = case.python_value()
    if not isinstance(value, int) or value >= 0 or abs(value) < 1_000_000:
        return False
    magnitude = abs(value)
    groups = [magnitude // 1_000_000, (magnitude // 1_000) % 1_000, magnitude % 1_000]
    if groups[1] == 0:
        return False
    parts = []
    for group in groups[:2]:
        words = _nf_cardinal_key("hy", group)
        if words is None:
            return False
        parts.append(f"{words} հազար")
    if groups[2]:
        words = _nf_cardinal_key("hy", groups[2])
        if words is None:
            return False
        parts.append(words)
    repaired = "մինուս " + " ".join(parts)
    expected_key = _surface_key(expected)
    return expected_key == repaired and expected_key != _surface_key(actual)


def _latvian_minuss_typo_oracle(case: RandomCase, expected: str, actual: str) -> bool:
    """Pinned oracle doubles the s in the Latvian negative prefix."""
    if case.locale != "lv" or case.kind not in {"cardinal", "decimal", "year"}:
        return False
    value = case.python_value()
    if not isinstance(value, (int, Decimal)) or value >= 0:
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    if not actual_key.startswith("mīnus"):
        return False
    repaired = actual_key.replace("mīnus ", "mīnuss ", 1)
    return expected_key == repaired and expected_key != actual_key


def _arabic_scale_oracle_defects(case: RandomCase, expected: str, actual: str) -> bool:
    """Pinned ar dual-nun drop and one-in-prefix scale duplication."""
    if case.locale != "ar" or case.kind not in {"cardinal", "year"}:
        return False
    value = case.python_value()
    if not isinstance(value, int):
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    magnitude = abs(value)
    for scale, dual, broken in (
        (1_000, "ألفان", "ألفا"),
        (1_000_000, "مليونان", "مليونا"),
    ):
        quotient = magnitude // scale
        if quotient == 2 and magnitude % scale == 0:
            repaired = actual_key.replace(dual, broken, 1)
            if expected_key == repaired and expected_key != actual_key:
                return True
        if quotient % 100 == 1 and quotient > 100:
            noun = "ألف" if scale == 1_000 else "مليون"
            accusative = "ألفاً" if scale == 1_000 else "مليوناً"
            repaired = actual_key.replace(
                _surface_key(f"واحد {accusative}"),
                _surface_key(f"{noun} {noun}"),
                1,
            )
            if expected_key == repaired and expected_key != actual_key:
                return True
    return False


_YEAR_HUNDRED_WORDS = {
    "am": "መቶ",
    "da": "hundrede",
    "nl": "honderd",
    "no": "hundre",
    "sl": "hundert",
}

_NO_YEAR_TENS = {
    2: "tjue",
    3: "tretti",
    4: "førti",
    5: "femti",
    6: "seksti",
    7: "sytti",
    8: "åtti",
    9: "nitti",
}


def _norwegian_year_remainder(value: int) -> str | None:
    if value == 0:
        return ""
    if value < 10:
        return _nf_cardinal_key("no", value)
    tens, unit = divmod(value, 10)
    if tens in _NO_YEAR_TENS:
        stem = _NO_YEAR_TENS[tens]
        if unit:
            unit_word = _nf_cardinal_key("no", unit)
            return f"{stem}{unit_word}" if unit_word else None
        return stem
    return _nf_cardinal_key("no", value)


def _polish_optional_jeden_million_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """The oracle may omit jeden before exactly one milion."""
    if case.locale != "pl" or case.kind not in {"cardinal", "year"}:
        return False
    value = case.python_value()
    if not isinstance(value, int) or not 1_000_000 <= abs(value) < 2_000_000:
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    repaired = actual_key.removeprefix("jeden ")
    return expected_key == repaired and expected_key != actual_key


def _amharic_explicit_thousand_year_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """Amharic oracle years keep the explicit one before shih."""
    if case.locale != "am" or case.kind != "year":
        return False
    value = case.python_value()
    if not isinstance(value, int) or not 1000 <= value <= 1999:
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    repaired = actual_key.replace("ሺህ", "አንድ ሺህ", 1)
    return expected_key == repaired and expected_key != actual_key


def _split_hundreds_year_variant(case: RandomCase, expected: str, actual: str) -> bool:
    """Locales whose oracle reads years as <centuries> hundred <remainder>."""
    language = case.locale.split("-", 1)[0]
    if language not in _YEAR_HUNDRED_WORDS or case.kind != "year":
        return False
    value = case.python_value()
    if not isinstance(value, int) or not 100 <= value <= 9999:
        if case.locale.split("-", 1)[0] == "da" and case.kind == "year" and value == 1:
            return _surface_key(expected) == "en" and _surface_key(actual) == "et"
        return False
    centuries, remainder = divmod(value, 100)
    if centuries % 10 == 0:
        return False
    century_words = _nf_cardinal_key(language, centuries)
    if century_words is None:
        return False
    hundred = _YEAR_HUNDRED_WORDS[language]
    if language == "no":
        remainder_words = _norwegian_year_remainder(remainder)
        joiner = " og " if remainder else ""
    else:
        remainder_words = _nf_cardinal_key(language, remainder) if remainder else ""
        joiner = " " if remainder else ""
    if remainder and remainder_words is None:
        return False
    if language == "da" and remainder == 1:
        remainder_words = "et"
    oracle_form = f"{century_words} {hundred}"
    if remainder_words:
        oracle_form = f"{oracle_form}{joiner}{remainder_words}"
    expected_key = _surface_key(expected)
    return expected_key == oracle_form and expected_key != _surface_key(actual)


def _chinese_year_suffix_variant(case: RandomCase, expected: str, actual: str) -> bool:
    """zh-CN oracle appends the year suffix 年."""
    if case.locale != "zh-CN" or case.kind != "year":
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    return expected_key == actual_key + "年" and expected_key != actual_key


def _chinese_leading_one_ten_family_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """Optional leading 一 before 十 anywhere in the Chinese family."""
    language = case.locale.split("-", 1)[0]
    if language != "zh" or case.kind not in {"cardinal", "decimal", "year"}:
        return False
    if case.kind == "decimal":
        normalized_expected = expected.replace("一十", "十")
        normalized_actual = actual.replace("一十", "十")
        if normalized_expected == normalized_actual and expected != actual:
            return True
        expected_forms = _decimal_precision_forms(case, normalized_expected)
        actual_forms = _decimal_precision_forms(case, normalized_actual)
        return bool(expected_forms & actual_forms) and (
            normalized_expected != normalized_actual
        )
    expected_key = _surface_key(expected).replace("一十", "十")
    actual_key = _surface_key(actual).replace("一十", "十")
    return expected_key == actual_key and _surface_key(expected) != _surface_key(actual)


def _portuguese_millar_conjunction_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """Optional e between mil and an exact-hundreds remainder."""
    language = case.locale.split("-", 1)[0]
    if language != "pt" or case.kind != "decimal":
        return False
    value = case.python_value()
    if not isinstance(value, Decimal):
        return False
    whole = int(value)
    if whole % 1000 == 0 or whole % 1000 < 100:
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    return expected_key != actual_key and expected_key in {
        actual_key.replace(" mil ", " mil e ", 1),
        actual_key.replace(" mil e ", " mil ", 1),
    }


def _nl_vowel_variant(case: RandomCase, expected: str, actual: str) -> bool:
    """Dutch éé→ee vowel normalization (één vs een)."""
    if case.locale.split("-", 1)[0] != "nl":
        return False
    # Try both directions: expected with accent→deaccented, or vice versa.
    norm_e = expected.replace("één", "een")
    norm_a = actual.replace("één", "een")
    return _surface_key(norm_e) == _surface_key(norm_a)


def _sk_million_space_variant(case: RandomCase, expected: str, actual: str) -> bool:
    """sk million may be spaced (miliónov osem...) or compound (miliónovosem...)."""
    if case.locale != "sk" or case.kind not in {"cardinal", "year"}:
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)

    # Normalize both sides: collapse space after million suffix.
    def collapse_space(text: str) -> str:
        for suffix in ("miliónov", "milióny", "milión"):
            text = text.replace(f"{suffix} ", suffix)
        return text

    return collapse_space(expected_key) == collapse_space(actual_key)


def _hy_one_million_variant(case: RandomCase, expected: str, actual: str) -> bool:
    """Hy oracle omits the 'one' word before million for1 million."""
    if case.locale != "hy" or case.kind not in {"cardinal", "year"}:
        return False
    value = case.python_value()
    if not isinstance(value, int) or abs(value) != 1_000_000:
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    expected_words = expected_key.split()
    actual_words = actual_key.split()
    # Expected has 2 words (e.g. 'หลังจาก millennium'), actual has3 words with extra 'mek'
    if len(actual_words) != len(expected_words) + 1:
        return False
    # Check if the extra word is at position 1 (after neg prefix)
    repaired = actual_words[0] + " " + " ".join(actual_words[2:])
    return expected_key == repaired and expected_key != actual_key


def _hy_one_million_narrow(case: RandomCase, expected: str, actual: str) -> bool:
    """Narrow rule: hy oracle omits 'mek' (one) before million for1 million."""
    if case.locale != "hy" or case.kind not in {"cardinal", "year"}:
        return False
    value = case.python_value()
    if not isinstance(value, int) or abs(value) != 1_000_000:
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    expected_words = expected_key.split()
    actual_words = actual_key.split()
    if len(actual_words) != len(expected_words) + 1:
        return False
    # Remove the extra word (at index1) and compare.
    repaired = " ".join(actual_words[:1] + actual_words[2:])
    return expected_key == repaired and expected_key != actual_key


def _esperanto_milcent_compound_variant(
    case: RandomCase, expected: str, actual: str
) -> bool:
    """Compound boundary milcent versus mil cent."""
    if case.locale != "eo" or case.kind not in {"cardinal", "year"}:
        return False
    expected_key = _surface_key(expected)
    actual_key = _surface_key(actual)
    repaired = actual_key.replace("mil cent", "milcent", 1)
    return expected_key == repaired and expected_key != actual_key


def _rule_registry() -> tuple[tuple[str, Callable[[RandomCase, str, str], bool]], ...]:
    return (
        ("variant:cs-optional-one-million", _czech_optional_one_million_variant),
        ("decimal-trailing-zero-precision", _decimal_precision_variant),
        ("variant:integral-fraction-reading", _integral_fraction_reading_variant),
        ("oracle:fa-denominator-reading", _persian_denominator_reading_variant),
        ("variant:digit-fraction-contraction", _digit_fraction_contraction_variant),
        ("oracle:negative-sign-dropped-decimal", _negative_sign_dropped_oracle),
        ("oracle:tet-ho-conjunction", _tetum_ho_conjunction_variant),
        ("oracle:sl-million-genitive", _slovenian_million_genitive_oracle),
        ("oracle:kn-extra-one", _kannada_extra_one_oracle),
        ("oracle:az-bir-omission", _azerbaijani_bir_omission_oracle),
        ("oracle:te-parenthesized-sign", _telugu_parenthesized_sign_oracle),
        (
            "oracle:te-kn-negative-decimal",
            _parenthesized_negative_decimal_composed,
        ),
        ("oracle:tr-concatenated-negative", _turkish_concatenated_negative_oracle),
        ("oracle:tr-glued-decimal", _turkish_glued_decimal_variant),
        ("oracle:negative-word-dropped", _negative_word_dropped_cardinal_oracle),
        (
            "oracle:hy-negative-million-thousands",
            _armenian_negative_million_thousand_additive_oracle,
        ),
        ("oracle:lv-minuss-typo", _latvian_minuss_typo_oracle),
        ("oracle:ar-scale-defects", _arabic_scale_oracle_defects),
        ("variant:hy-one-million", _hy_one_million_narrow),
        ("variant:pl-optional-jeden-million", _polish_optional_jeden_million_variant),
        ("variant:am-explicit-thousand-year", _amharic_explicit_thousand_year_variant),
        ("variant:split-hundreds-year", _split_hundreds_year_variant),
        ("variant:zh-cn-year-suffix", _chinese_year_suffix_variant),
        ("variant:zh-leading-one-ten", _chinese_leading_one_ten_family_variant),
        ("variant:pt-millar-conjunction", _portuguese_millar_conjunction_variant),
        ("variant:nl-vowel", _nl_vowel_variant),
        ("variant:eo-milcent-compound", _esperanto_milcent_compound_variant),
        ("oracle:de-year-einshundert", _german_year_einshundert_oracle_quirk),
        ("en-year-reading", _english_year_variant),
        ("oracle:de-post-2000-year", _german_post_2000_year_oracle_quirk),
        ("variant:de-optional-ein-ordinal", _german_optional_ein_ordinal_variant),
        ("oracle:es-ordinal-accent", _spanish_ordinal_accent_oracle_quirk),
        ("variant:es-ordinal-synonym", _spanish_ordinal_synonym_variant),
        (
            "variant:es-ordinal-attributive-apocope",
            _spanish_ordinal_attributive_apocope_variant,
        ),
        (
            "variant:es-ordinal-compound-orthography",
            _spanish_ordinal_compound_orthography_variant,
        ),
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
        ("oracle:numeric-ordinal-reading", _oracle_numeric_ordinal_variant),
        ("variant:ko-ordinal-reading", _korean_ordinal_reading_variant),
        ("variant:pt-ordinal-orthography", _portuguese_ordinal_oracle_variant),
        ("variant:pt-zero-minor-omission", _portuguese_zero_minor_omission_variant),
        (
            "oracle:ru-decimal-whole-agreement",
            _russian_decimal_whole_agreement_oracle_quirk,
        ),
        ("variant:sv-optional-ett-ordinal", _swedish_optional_ett_ordinal_variant),
        ("oracle:sv-number-orthography", _swedish_oracle_orthography_variant),
        ("oracle:sv-ordinal-orthography", _swedish_ordinal_oracle_variant),
        ("variant:mn-ordinal-spacing", _mongolian_ordinal_spacing_variant),
        ("variant:zh-leading-one-ten", _chinese_leading_one_ten_family_variant),
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
    composed = _composed_decimal_variant(case, expected, actual)
    if composed is not None:
        return composed
    for name, predicate in _VARIANT_RULES:
        if predicate(case, expected, actual):
            if (
                name == "decimal-trailing-zero-precision"
                and case.locale.split("-", 1)[0] == "en"
            ):
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
