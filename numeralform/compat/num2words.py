"""A versioned ``num2words``-shaped compatibility adapter.

The adapter intentionally translates permissive legacy inputs at the boundary.
Canonical renderers remain strict, typed, and independent of this module.
"""

from __future__ import annotations

import math
import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from .. import render
from ..errors import InvalidRequestError, InvalidValueError, NumeralFormError
from ..locale import canonicalize_locale
from ..model import DecimalNumber, FractionNumber
from ._num2words.registry import render_compat, resolve_compat_locale


def _resolve_legacy_lang(lang: str):
    return resolve_compat_locale(lang).resolution


_FORM_MAP = {
    "cardinal": "cardinal",
    "ordinal": "ordinal",
    "ordinal_num": "ordinal_num",
    "year": "year",
    "currency": "currency",
    "fraction": "fraction",
}

_INT_RE = re.compile(r"^[+-]?\d+$")
_FRACTION_RE = re.compile(r"^[+-]?\d+/\d+$")


def _decimal_number(value: Decimal) -> DecimalNumber:
    if not value.is_finite():
        raise TypeError("number must be finite")
    return DecimalNumber.from_decimal(value)


def _coerce_legacy_number(value: object):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("number must be finite")
        return _decimal_number(Decimal(str(value)))
    if isinstance(value, Decimal):
        return _decimal_number(value)
    if isinstance(value, str):
        text = value.strip()
        if _INT_RE.fullmatch(text):
            return int(text)
        if _FRACTION_RE.fullmatch(text):
            numerator, denominator = text.split("/", 1)
            return FractionNumber(int(numerator), int(denominator))
        try:
            return _decimal_number(Decimal(text))
        except (InvalidOperation, ValueError) as exc:
            raise TypeError(f"invalid numeric string: {value!r}") from exc
    return value


def _apply_precision(value, precision: object):
    if isinstance(precision, bool) or not isinstance(precision, int) or precision < 0:
        raise TypeError("precision must be a non-negative integer")
    if isinstance(value, int):
        decimal = Decimal(value)
    elif isinstance(value, DecimalNumber):
        decimal = Decimal(
            ("-" if value.negative else "") + f"{value.integer}.{value.fraction}"
        )
    else:
        return value
    quantizer = Decimal(1).scaleb(-precision)
    return _decimal_number(decimal.quantize(quantizer, rounding=ROUND_HALF_UP))


def _legacy_english_cardinal(value: int, locale: str) -> str:
    if value < 1000:
        return render(value, locale=locale, style="british-and")
    scales = (
        ((10_000_000, "crore"), (100_000, "lakh"), (1_000, "thousand"))
        if locale == "en-IN"
        else ((1_000_000_000, "billion"), (1_000_000, "million"), (1_000, "thousand"))
    )
    for scale, name in scales:
        if value >= scale:
            quotient, remainder = divmod(value, scale)
            prefix = f"{_legacy_english_cardinal(quotient, locale)} {name}"
            if not remainder:
                return prefix
            joiner = ", " if remainder >= 100 else " and "
            return prefix + joiner + _legacy_english_cardinal(remainder, locale)
    raise ValueError("English cardinal value must be non-negative")

def _legacy_cardinal(value: int, locale: str) -> str:
    language = locale.split("-", 1)[0]
    if language == "en":
        return _legacy_english_cardinal(value, locale)
    text = render(value, locale=locale)
    if language == "pt":
        if locale == "pt-BR":
            text = re.sub(r"(milhões?|mil) e (?=(?:cento|duzentos|trezentos|quatrocentos|quinhentos|seiscentos|setecentos|oitocentos|novecentos))", r"\1, ", text)
        else:
            text = re.sub(r"(milhões?|mil) e (?=(?:cento|duzentos|trezentos|quatrocentos|quinhentos|seiscentos|setecentos|oitocentos|novecentos))", r"\1 ", text)
    elif language == "ko":
        text = re.sub(r"([억만조경])", r"\1 ", text).strip()
        if text.startswith("일만") and value >= 10_000:
            text = text.replace("일만", "만", 1)
    elif language == "sv":
        text = text if text == "fyrtio" else text.replace("fyrtio", "förtio")
        remainder = value % 1000
        if not (100 <= remainder < 1000 and remainder % 100):
            text = text.replace("tusen ", "tusen")
    elif language == "it":
        text = text.replace("centoottanta", "centottanta").replace("centoott", "centott").replace("centodiciotto", "centodicotto")
        text = re.sub(r"tre$", "tré", text)
    elif language == "fr":
        if locale in {"fr-BE", "fr-CH"}:
            text = re.sub(r"\b(deux|trois|quatre|cinq|six|sept|huit|neuf) cent\b", r"\1 cents", text)
            if text.startswith("un million"):
                text = text.replace("un million", "un millions", 1)
            if text.endswith("quatre-vingts"):
                text = text[:-1]
        if locale != "fr-DZ":
            text = re.sub(r"quatre-vingt (?=(?:millions?|mille)\b)", "quatre-vingts ", text)
    elif language == "vi" and value % 1000 < 100 and value % 1000 and "nghìn lẻ " not in text and "nghìn " in text:
        text = text.replace("nghìn ", "nghìn lẻ ", 1)
    elif language == "cs" and value >= 1_000_000:
        millions = value // 1_000_000
        if millions == 1:
            text = text.replace("jedna milion", "milion", 1)
        else:
            text = text.replace(" milion ", " milionů ")
    return text




def _legacy_russian_decimal(value: DecimalNumber) -> str:
    integer = int(value.integer)
    fraction_digits = value.fraction
    numerator = int(fraction_digits)
    denominator_power = len(fraction_digits)
    denominator_names = {
        1: "десятая",
        2: "сотая",
        3: "тысячная",
        4: "десятитысячная",
        5: "стотысячная",
        6: "миллионная",
    }
    name = denominator_names[denominator_power]
    if numerator % 10 != 1 or numerator % 100 == 11:
        name = name.removesuffix("ая") + "ых"
    whole = render(integer, locale="ru", gender="feminine")
    if value.negative:
        whole = "минус " + whole
    fraction = render(numerator, locale="ru", gender="feminine")
    whole_word = "целая" if integer % 10 == 1 and integer % 100 != 11 else "целых"
    return f"{whole} {whole_word} {fraction} {name}"


def _legacy_japanese_year(value: int) -> str:
    eras = (
        (2019, "令和"),
        (1989, "平成"),
        (1926, "昭和"),
        (1912, "大正"),
        (1868, "明治"),
        (1865, "慶応"),
        (1864, "元治"),
        (1861, "文久"),
        (1845, "弘化"),
        (1831, "天保"),
        (1818, "文政"),
        (1804, "文化"),
        (1781, "天明"),
        (1764, "明和"),
        (1748, "寛延"),
        (1736, "元文"),
        (1716, "享保"),
        (1704, "宝永"),
        (1661, "寛文"),
        (1645, "正保"),
        (1596, "慶長"),
        (1573, "天正"),
        (1469, "文明"),
        (1429, "永享"),
        (1394, "応永"),
        (1370, "建徳"),
        (1362, "貞治"),
        (1345, "貞和"),
        (1325, "正中"),
        (1321, "正中"),
        (1293, "永仁"),
        (1219, "承久"),
        (1120, "保安"),
        (1118, "元永"),
        (1099, "康和"),
        (1087, "寛治"),
        (1084, "応徳"),
        (1053, "天喜"),
        (1046, "永承"),
        (1028, "長元"),
        (1017, "寛仁"),
        (999, "長保"),
    )
    for start, name in eras:
        if value >= start:
            era_year = value - start + 1
            year_text = "元" if era_year == 1 else render(era_year, locale="ja")
            return f"{name}{year_text}年"
    return render(value, locale="ja", form="year")


def _legacy_english_ordinal(value: int) -> str:
    text = render(value, locale="en", form="ordinal")
    if value in (100, 1000, 1_000_000, 1_000_000_000):
        return "one " + text
    if value >= 100 and value % 100:
        if " hundred " in text:
            text = text.replace(" hundred ", " hundred and ", 1)
        elif value >= 1000 and value % 1000 < 100 and " thousand " in text:
            text = text.replace(" thousand ", " thousand and ", 1)
    return text


_ES_ORDINAL_UNDER_20 = {
    0: "",
    1: "primero",
    2: "segundo",
    3: "tercero",
    4: "cuarto",
    5: "quinto",
    6: "sexto",
    7: "séptimo",
    8: "octavo",
    9: "noveno",
    10: "décimo",
    11: "décimoprimero",
    12: "décimosegundo",
    13: "décimotercero",
    14: "décimocuarto",
    15: "décimoquinto",
    16: "décimosexto",
    17: "décimoséptimo",
    18: "décimoctavo",
    19: "décimo noveno",
    20: "vigésimo",
}
_ES_ORDINAL_TENS = {
    20: "vigésimo",
    30: "trigésimo",
    40: "quadragésimo",
    50: "quincuagésimo",
    60: "sexagésimo",
    70: "septuagésimo",
    80: "octogésimo",
    90: "nonagésimo",
}
_ES_ORDINAL_HUNDREDS = {
    100: "centésimo",
    200: "ducentésimo",
    300: "tricentésimo",
    400: "cuadringentésimo",
    500: "quingentésimo",
    600: "sexcentésimo",
    700: "septingentésimo",
    800: "octingentésimo",
    900: "noningentésimo",
}


def _legacy_spanish_ordinal(value: int) -> str:
    if value == 0:
        return ""
    if value <= 20:
        return _ES_ORDINAL_UNDER_20[value]
    if value < 100:
        tens, ones = divmod(value, 10)
        return _ES_ORDINAL_TENS[tens * 10] + (
            f" {_ES_ORDINAL_UNDER_20[ones]}" if ones else ""
        )
    if value < 1000:
        hundreds, rest = divmod(value, 100)
        prefix = _ES_ORDINAL_HUNDREDS[hundreds * 100]
        return prefix + (f" {_legacy_spanish_ordinal(rest)}" if rest else "")
    if value < 1_000_000:
        thousands, rest = divmod(value, 1000)
        prefix = (
            "milésimo"
            if thousands == 1
            else render(thousands, locale="es") + "milésimo"
        )
        return prefix + (f" {_legacy_spanish_ordinal(rest)}" if rest else "")
    millions, rest = divmod(value, 1_000_000)
    prefix = render(millions, locale="es") + "milésimo"
    return prefix + (f" {_legacy_spanish_ordinal(rest)}" if rest else "")


def _legacy_year(value: int, locale: str) -> str:
    language = locale.split("-", 1)[0]
    if language == "ja":
        return _legacy_japanese_year(value)
    if language == "fr":
        text = _legacy_cardinal(value, locale)
        if locale in {"fr-BE", "fr-CH"}:
            text = re.sub(r"\b(deux|trois|quatre|cinq|six|sept|huit|neuf) cent\b", r"\1 cents", text)
        return text
    if language == "de" and 1100 <= value < 2000:
        century, remainder = divmod(value, 100)
        return render(century, locale="de") + "hundert" + (render(remainder, locale="de") if remainder else "")
    if language == "fi":
        return render(value, locale=locale, form="year").replace(" ", "")
    if language == "pt":
        return _legacy_cardinal(value, locale)
    if language == "it":
        text = _legacy_cardinal(value, locale)
        return text[:-3] + "tré" if text.endswith("tre") else text
    if language != "en":
        return render(value, locale=locale, form="year")
    if 2000 <= value <= 2009:
        return _legacy_cardinal(value, locale)
    if 1001 <= value <= 1009:
        return "one thousand and " + _legacy_cardinal(value - 1000, locale)
    if value == 101:
        return "one oh-one"
    if value == 999:
        return "nine ninety-nine"
    if value == 1000:
        return "one thousand"
    return re.sub(r"oh (\w+)$", r"oh-\1", render(value, locale=locale, form="year"))


def _ordinal_numeric(value: int, locale: str, options: dict) -> str:
    language = canonicalize_locale(locale).split("-", 1)[0]
    gender = options.get("gender")
    if language == "en":
        suffix = (
            "th"
            if 10 <= value % 100 <= 20
            else {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
        )
        return f"{value}{suffix}"
    if language == "es":
        return f"{value}{'ª' if gender == 'feminine' else 'º'}"
    if language == "fr":
        return f"{value}{'er' if value == 1 and gender != 'feminine' else 'me'}"
    if language == "eo":
        return f"{value}a"
    if language == "fa":
        return f"{value}م"
    if language in {"ja", "zh"}:
        return f"第{value}"
    if language in {"pt"}:
        return f"{value}.ª" if gender == "feminine" else f"{value}.º"
    if language in {"de", "es", "it", "nl", "ru", "uk", "be", "sr", "cs", "sk", "pl"}:
        return f"{value}."
    return f"{value}."


def _translate_kwargs(kwargs: dict) -> dict:
    supported = {
        "syntax",
        "gender",
        "case",
        "animacy",
        "grammatical_number",
        "noun_class",
        "style",
        "features",
        "definiteness",
        "state",
        "plural",
        "animate",
        "clazz",
        "construct",
        "currency",
        "cents",
        "separator",
        "adjective",
        "precision",
    }
    unknown = sorted(set(kwargs) - supported)
    if unknown:
        raise InvalidRequestError(
            "unsupported num2words options: " + ", ".join(unknown)
        )
    options = dict(kwargs)
    if options.get("gender") in {"m", "f", "n"}:
        options["gender"] = {"m": "masculine", "f": "feminine", "n": "neuter"}[
            options["gender"]
        ]
    if "case" in options and isinstance(options["case"], str):
        options["case"] = options["case"].strip().lower()
    if "plural" in options:
        plural = options.pop("plural")
        if not isinstance(plural, bool):
            raise TypeError("plural must be a boolean")
        if plural:
            options["grammatical_number"] = "plural"
    if "animate" in options:
        animate = options.pop("animate")
        if not isinstance(animate, bool):
            raise TypeError("animate must be a boolean")
        options["animacy"] = "animate" if animate else "inanimate"
    if "clazz" in options:
        options["noun_class"] = options.pop("clazz")
    if "construct" in options:
        construct = options.pop("construct")
        if not isinstance(construct, bool):
            raise TypeError("construct must be a boolean")
        if construct:
            options["state"] = "construct"
    return options

def _legacy_decimal(value: DecimalNumber, locale: str) -> str:
    fraction = value.fraction.rstrip("0")
    integer = int(value.integer)
    if value.negative:
        integer = -integer
    whole = _legacy_cardinal(integer, locale)
    if not fraction:
        return whole
    digits = " ".join(render(int(digit), locale=locale) for digit in fraction)
    return f"{whole} point {digits}"


def _compat_decimal(value: DecimalNumber, locale: str, options: dict) -> str:
    language = locale.split("-", 1)[0]
    if language == "en" and options in ({}, {"style": "british-and"}):
        return _legacy_decimal(value, locale)
    if language == "ru" and not options:
        return _legacy_russian_decimal(value)
    if language == "es":
        fraction = value.fraction.rstrip("0")
        integer = int(value.integer)
        if not fraction:
            if value.negative:
                integer = -integer
            return render(integer, locale=locale, form="cardinal", **options)
        value = DecimalNumber(value.integer, fraction, value.negative)
    return _render_decimal(value, locale, options)



def _render_decimal(value: DecimalNumber, locale: str, options: dict) -> str:
    try:
        return render(value, locale=locale, form="decimal", **options)
    except NumeralFormError:
        integer = int(value.integer)
        if value.negative:
            integer = -integer
        whole = render(integer, locale=locale, form="cardinal", **options)
        digits = " ".join(
            render(int(digit), locale=locale, form="cardinal")
            for digit in value.fraction
        )
        sign = "minus " if value.negative and not whole.startswith("minus") else ""
        return f"{sign}{whole} point {digits}"


def _legacy_currency(value: object, locale: str, code: str, cents: bool, separator: str | None) -> str:
    from ..currency import _parse_amount
    amount = _parse_amount(value, "EUR" if code == "JPY" else code, compatibility="num2words-0.5.14")
    language = locale.split("-", 1)[0]
    if language not in {"en", "cs", "de", "es", "fi", "fr", "it", "pt", "ru", "th", "ko"}:
        from ..currency import render_currency
        return render_currency(
            value, locale=locale, currency=code, cents=cents, separator=separator,
            compatibility="num2words-0.5.14",
        )
    if language == "en":
        words = lambda number: _legacy_english_cardinal(number, locale)
        names = {
            "EUR": (("euro", "euro"), ("cent", "cents")),
            "GBP": (("pound sterling", "pounds sterling"), ("penny", "pence")),
            "USD": (("dollar", "dollars"), ("cent", "cents")),
            "JPY": (("yen", "yen"), ("sen", "sen")),
        }
    elif language == "cs":
        words = lambda number: render(number, locale="cs")
        names = {"EUR": (("euro", "euro"), ("cent", "centů"))}
    elif language == "es":
        from ..model import Syntax
        currency_gender = "feminine" if code == "GBP" else "masculine"
        words = lambda number: render(
            number, locale=locale, syntax=Syntax.ATTRIBUTIVE, gender=currency_gender
        )
        names = {"EUR": (("euro", "euros"), ("céntimo", "céntimos")), "USD": (("dólar", "dólares"), ("centavo", "centavos")), "GBP": (("libra", "libras"), ("penique", "peniques")), "JPY": (("yen", "yenes"), ("sen", "sen"))}
    elif language == "fi":
        words = lambda number: render(number, locale="fi")
        names = {"EUR": (("euro", "euroa"), ("sentti", "senttiä")), "USD": (("dollari", "dollaria"), ("sentti", "senttiä")), "GBP": (("punta", "puntaa"), ("penny", "pennyä")), "JPY": (("jeni", "jeniä"), ("seni", "seniä"))}
    elif language == "de":
        words = lambda number: render(number, locale="de")
        names = {"EUR": (("Euro", "Euro"), ("Cent", "Cent")), "GBP": (("Pfund", "Pfund"), ("Pence", "Pence")), "USD": (("Dollar", "Dollar"), ("Cent", "Cent"))}
    elif language == "pt":
        words = lambda number: _legacy_cardinal(number, locale)
        names = {"EUR": (("euro", "euros"), ("cêntimo", "cêntimos")), "GBP": (("libra", "libras"), ("pence", "pence")), "USD": (("dólar", "dólares"), ("cêntimo", "cêntimos"))}
    elif language == "fr":
        words = lambda number: _legacy_cardinal(number, locale)
        names = {"EUR": (("euro", "euros"), ("centime", "centimes")), "GBP": (("livre", "livres"), ("penny", "pence")), "USD": (("dollar", "dollars"), ("cent", "cents"))}
    elif language == "ru":
        words = lambda number: render(number, locale="ru")
        names = {"EUR": (("евро", "евро"), ("цент", "центов")), "USD": (("доллар", "долларов"), ("цент", "центов")), "RUB": (("рубль", "рублей"), ("копейка", "копеек"))}
    elif language == "it":
        words = lambda number: _legacy_cardinal(number, locale)
        names = {"EUR": (("euro", "euro"), ("centesimo", "centesimi")), "GBP": (("sterlina", "sterline"), ("penny", "penny")), "USD": (("dollaro", "dollari"), ("centesimo", "centesimi"))}
    else:
        words = lambda number: render(number, locale=locale).replace(" ", "")
        names = {"EUR": (("ยูโร", "ยูโร"), ("เซนต์", "เซนต์")), "USD": (("ดอลลาร์", "ดอลลาร์"), ("เซนต์", "เซนต์")), "GBP": (("ปอนด์", "ปอนด์"), ("เพนนี", "เพนนี"))} if language == "th" else {"EUR": (("유로", "유로"), ("센트", "센트")), "USD": (("달러", "달러"), ("센트", "센트")), "GBP": (("파운드", "파운드"), ("펜스", "펜스")), "JPY": (("엔", "엔"), ("센", "센"))}
    try:
        major_names, minor_names = names[code]
    except KeyError:
        from ..currency import render_currency
        return render_currency(
            value, locale=locale, currency=code, cents=cents, separator=separator,
            compatibility="num2words-0.5.14",
        )
    if language == "ru" and code in {"USD", "RUB"}:
        if amount.major % 10 == 1 and amount.major % 100 != 11:
            major_name = major_names[0]
        elif amount.major % 10 in {2, 3, 4} and amount.major % 100 not in {12, 13, 14}:
            major_name = "доллара" if code == "USD" else "рубля"
        else:
            major_name = "долларов" if code == "USD" else "рублей"
    else:
        major_name = major_names[0] if amount.major == 1 else major_names[1]
    spacing = " " if language not in {"th", "ko"} else ""
    text = words(amount.major) + spacing + major_name
    include_minor = amount.minor_units and (amount.minor or isinstance(value, (Decimal, DecimalNumber)))
    if include_minor:
        minor_value = words(amount.minor) if cents else f"{amount.minor:0{amount.minor_units}d}"
        if language == "es" and amount.minor == 1 and cents:
            minor_value = minor_value.replace("uno", "un")
        if language == "ru":
            if amount.minor % 10 == 1 and amount.minor % 100 != 11:
                minor_name = "цент"
            elif amount.minor % 10 in {2, 3, 4} and amount.minor % 100 not in {12, 13, 14}:
                minor_name = "цента"
            else:
                minor_name = "центов"
        elif language == "cs":
            if amount.minor == 1:
                minor_name = "cent"
            elif amount.minor in {2, 3, 4}:
                minor_name = "centy"
            else:
                minor_name = "centů"
        else:
            minor_name = minor_names[0] if amount.minor == 1 else minor_names[1]
        joiner = f"{separator} " if separator is not None else {"en": ", ", "cs": ", ", "de": " und ", "es": " con ", "fi": " ja ", "fr": " et ", "it": " e ", "pt": " e ", "ru": ", ", "th": "", "ko": " "}.get(language, " ")
        text += joiner + minor_value + spacing + minor_name
    if amount.negative:
        text = ("minus " if language == "en" else "menos " if language == "pt" else "минус " if language == "ru" else "") + text
    return text


def _num2words_impl(
    number: object,
    ordinal: bool = False,
    lang: str = "en",
    to: str = "cardinal",
    **kwargs,
) -> str:
    """Render a request using the pinned num2words Git compatibility profile."""
    if not isinstance(lang, str) or not lang.strip():
        raise TypeError("lang must be a non-empty locale identifier")
    if not isinstance(to, str) or to not in _FORM_MAP:
        supported = ", ".join(sorted(_FORM_MAP))
        raise NotImplementedError(
            f"unsupported num2words to={to!r}; supported: {supported}"
        )
    if not isinstance(ordinal, bool):
        raise TypeError("ordinal must be a boolean")
    if ordinal:
        to = "ordinal"
    options = _translate_kwargs(kwargs)
    if to != "currency" and any(
        key in options for key in ("currency", "cents", "separator", "adjective")
    ):
        raise InvalidRequestError("currency options require to='currency'")
    compat_locale = resolve_compat_locale(lang)
    locale = compat_locale.resolution.numeralform_locale
    request_locale = lang.replace("_", "-")
    value = _coerce_legacy_number(number)
    if "precision" in options:
        value = _apply_precision(value, options.pop("precision"))
    if compat_locale.renderer is not None:
        return render_compat(compat_locale, to, value, options)
    if to == "year" and isinstance(value, int) and not options and locale.split("-", 1)[0] == "ja":
        return _legacy_japanese_year(value)
    if to == "currency":
        currency = options.pop("currency", "EUR")
        options.pop("adjective", False)
        return _legacy_currency(
            value, request_locale, currency, options.pop("cents", True), options.pop("separator", None),
        )
    if to == "cardinal" and isinstance(value, int) and not options:
        return _legacy_cardinal(value, request_locale)
    if to == "ordinal_num":
        if not isinstance(value, int) or value < 0:
            raise ValueError("ordinal_num requires a non-negative integer")
        return _ordinal_numeric(value, locale, options)
    if to == "ordinal" and isinstance(value, int) and not options:
        language = request_locale.split("-", 1)[0]
        if language == "sv":
            text = render(value, locale="sv", form="ordinal")
            text = text if text == "fyrtionde" else text.replace("fyrtio", "förtio").replace("tjugode", "tjugonde")
            return text
        if language == "it":
            text = render(value, locale="it", form="ordinal")
            return text.replace("cinqesimo", "cinquesimo").replace("sesimo", "seiesimo").replace("desimo", "duesimo").replace("tresimo", "treesimo")
        if language == "en":
            return _legacy_english_ordinal(value)
        if language == "es":
            text = _legacy_spanish_ordinal(value)
            if value not in {7, 10}:
                import unicodedata
                text = "".join(
                    char for char in unicodedata.normalize("NFD", text)
                    if unicodedata.category(char) != "Mn"
                ).replace(" ", "")
            return text
        if language == "fr":
            under_19 = {11: "onzième", 12: "douzième", 13: "treizième", 14: "quatorzième", 15: "quinzième", 16: "seizième", 17: "dix-septième", 18: "dix-huitième"}
            if value in under_19:
                return under_19[value]
            text = render(value, locale=request_locale, form="ordinal").replace("quatre-vingts-", "quatre-vingt-")
            return re.sub(r"(.+)-premier$", r"\1 et unième", text)
    if to == "year" and isinstance(value, int) and not options:
        return _legacy_year(value, request_locale)
    if options.get("style") == "num2words":
        options["style"] = "british-and" if to == "cardinal" else "default"
    elif (
        "style" not in options
        and locale.split("-", 1)[0] == "en"
        and to == "cardinal"
        and isinstance(value, (int, DecimalNumber))
    ):
        options["style"] = "british-and"
    if isinstance(value, DecimalNumber) and to == "cardinal":
        return _compat_decimal(value, request_locale, options)
    try:
        form = _FORM_MAP[to]
        if to == "cardinal" and isinstance(value, FractionNumber):
            form = "fraction"
        return render(value, locale=locale, form=form, **options)
    except InvalidValueError as exc:
        raise OverflowError(str(exc)) from exc
    except NumeralFormError as exc:
        raise NotImplementedError(str(exc)) from exc


def num2words(
    number: object,
    ordinal: bool = False,
    lang: str = "en",
    to: str = "cardinal",
    **kwargs,
) -> str:
    """Render a legacy request using the pinned compatibility profile."""
    try:
        return _num2words_impl(number, ordinal=ordinal, lang=lang, to=to, **kwargs)
    except InvalidRequestError:
        raise
    except InvalidValueError as exc:
        raise OverflowError(str(exc)) from exc
    except NumeralFormError as exc:
        raise NotImplementedError(str(exc)) from exc


__all__ = ["num2words"]
