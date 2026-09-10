"""Russian cardinal and ordinal rendering with data-driven morphology."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities, NumericDomain
from ..model import (
    DecimalNumber,
    DigitSequence,
    FractionNumber,
    Gender,
    Morphology,
    NumeralForm,
    NumeralRequest,
    NumeralResult,
    Syntax,
)
from .base import require_int, validate_request

_UNDER_20 = (
    "ноль",
    "один",
    "два",
    "три",
    "четыре",
    "пять",
    "шесть",
    "семь",
    "восемь",
    "девять",
    "десять",
    "одиннадцать",
    "двенадцать",
    "тринадцать",
    "четырнадцать",
    "пятнадцать",
    "шестнадцать",
    "семнадцать",
    "восемнадцать",
    "девятнадцать",
)
_TENS = (
    "",
    "",
    "двадцать",
    "тридцать",
    "сорок",
    "пятьдесят",
    "шестьдесят",
    "семьдесят",
    "восемьдесят",
    "девяносто",
)
_HUNDREDS = (
    "",
    "сто",
    "двести",
    "триста",
    "четыреста",
    "пятьсот",
    "шестьсот",
    "семьсот",
    "восемьсот",
    "девятьсот",
)
_DIGITS = (
    "ноль",
    "один",
    "два",
    "три",
    "четыре",
    "пять",
    "шесть",
    "семь",
    "восемь",
    "девять",
)

# Case order is nominative, genitive, dative, accusative, instrumental,
# prepositional.  The accusative pair is animate/inanimate where needed.
_ONES = {
    0: ("ноль", "ноля", "нолю", ("ноля", "ноль"), "нолём", "ноле"),
    1: {
        "m": ("один", "одного", "одному", ("одного", "один"), "одним", "одном"),
        "f": ("одна", "одной", "одной", "одну", "одной", "одной"),
        "n": ("одно", "одного", "одному", "одно", "одним", "одном"),
        "p": ("одни", "одних", "одним", ("одних", "одни"), "одними", "одних"),
    },
    2: {
        "m": ("два", "двух", "двум", ("двух", "два"), "двумя", "двух"),
        "f": ("две", "двух", "двум", ("двух", "две"), "двумя", "двух"),
        "n": ("два", "двух", "двум", "два", "двумя", "двух"),
        "p": ("двое", "двоих", "двоим", "двоих", "двоими", "двоих"),
    },
    3: {
        "m": ("три", "трёх", "трём", ("трёх", "три"), "тремя", "трёх"),
        "f": ("три", "трёх", "трём", ("трёх", "три"), "тремя", "трёх"),
        "n": ("три", "трёх", "трём", "три", "тремя", "трёх"),
        "p": ("трое", "троих", "троим", "троих", "троими", "троих"),
    },
    4: {
        "m": (
            "четыре",
            "четырёх",
            "четырём",
            ("четырёх", "четыре"),
            "четырьмя",
            "четырёх",
        ),
        "f": (
            "четыре",
            "четырёх",
            "четырём",
            ("четырёх", "четыре"),
            "четырьмя",
            "четырёх",
        ),
        "n": ("четыре", "четырёх", "четырём", "четыре", "четырьмя", "четырёх"),
        "p": ("четверо", "четверых", "четверым", "четверых", "четверыми", "четверых"),
    },
}
_ONES_SIMPLE = {
    5: ("пять", "пяти", "пяти", ("пять", "пять"), "пятью", "пяти"),
    6: ("шесть", "шести", "шести", ("шесть", "шесть"), "шестью", "шести"),
    7: ("семь", "семи", "семи", ("семь", "семь"), "семью", "семи"),
    8: ("восемь", "восьми", "восьми", ("восемь", "восемь"), "восемью", "восьми"),
    9: ("девять", "девяти", "девяти", ("девять", "девять"), "девятью", "девяти"),
}
_TENS_CASES = {
    2: ("двадцать", "двадцати", "двадцати", "двадцать", "двадцатью", "двадцати"),
    3: ("тридцать", "тридцати", "тридцати", "тридцать", "тридцатью", "тридцати"),
    4: ("сорок", "сорока", "сорока", "сорок", "сорока", "сорока"),
    5: (
        "пятьдесят",
        "пятидесяти",
        "пятидесяти",
        "пятьдесят",
        "пятьюдесятью",
        "пятидесяти",
    ),
    6: (
        "шестьдесят",
        "шестидесяти",
        "шестидесяти",
        "шестьдесят",
        "шестьюдесятью",
        "шестидесяти",
    ),
    7: (
        "семьдесят",
        "семидесяти",
        "семидесяти",
        "семьдесят",
        "семьюдесятью",
        "семидесяти",
    ),
    8: (
        "восемьдесят",
        "восьмидесяти",
        "восьмидесяти",
        "восемьдесят",
        "восемьюдесятью",
        "восьмидесяти",
    ),
    9: ("девяносто", "девяноста", "девяноста", "девяносто", "девяноста", "девяноста"),
}
_HUNDRED_CASES = {
    1: ("сто", "ста", "ста", "сто", "ста", "ста"),
    2: ("двести", "двухсот", "двумстам", "двести", "двумястами", "двухстах"),
    3: ("триста", "трёхсот", "трёмстам", "триста", "тремястами", "трёхстах"),
    4: (
        "четыреста",
        "четырёхсот",
        "четырёмстам",
        "четыреста",
        "четырьмястами",
        "четырёхстах",
    ),
    5: ("пятьсот", "пятисот", "пятистам", "пятьсот", "пятьюстами", "пятистах"),
    6: ("шестьсот", "шестисот", "шестистам", "шестьсот", "шестьюстами", "шестистах"),
    7: ("семьсот", "семисот", "семистам", "семьсот", "семьюстами", "семистах"),
    8: (
        "восемьсот",
        "восьмисот",
        "восьмистам",
        "восемьсот",
        "восемьюстами",
        "восьмистах",
    ),
    9: (
        "девятьсот",
        "девятисот",
        "девятистам",
        "девятьсот",
        "девятьюстами",
        "девятистах",
    ),
}
_SCALE_NOM = {
    3: ("тысяча", "тысячи", "тысяч"),
    6: ("миллион", "миллиона", "миллионов"),
    9: ("миллиард", "миллиарда", "миллиардов"),
    12: ("триллион", "триллиона", "триллионов"),
    15: ("квадриллион", "квадриллиона", "квадриллионов"),
    18: ("квинтиллион", "квинтиллиона", "квинтиллионов"),
}
_SCALE_CASES = {
    "тысяча": (
        ("тысяча", "тысячи", "тысяч"),
        ("тысячи", "тысяч", "тысяч"),
        ("тысяче", "тысячам", "тысячам"),
        ("тысячу", "тысячи", "тысяч"),
        ("тысячей", "тысячами", "тысячами"),
        ("тысяче", "тысячах", "тысячах"),
    ),
    "миллион": (
        ("миллион", "миллиона", "миллионов"),
        ("миллиона", "миллионов", "миллионов"),
        ("миллиону", "миллионам", "миллионам"),
        ("миллион", "миллиона", "миллионов"),
        ("миллионом", "миллионами", "миллионами"),
        ("миллионе", "миллионах", "миллионах"),
    ),
    "миллиард": (
        ("миллиард", "миллиарда", "миллиардов"),
        ("миллиарда", "миллиардов", "миллиардов"),
        ("миллиарду", "миллиардам", "миллиардам"),
        ("миллиард", "миллиарда", "миллиардов"),
        ("миллиардом", "миллиардами", "миллиардами"),
        ("миллиарде", "миллиардах", "миллиардах"),
    ),
    "триллион": (
        ("триллион", "триллиона", "триллионов"),
        ("триллиона", "триллионов", "триллионов"),
        ("триллиону", "триллионам", "триллионам"),
        ("триллион", "триллиона", "триллионов"),
        ("триллионом", "триллионами", "триллионами"),
        ("триллионе", "триллионах", "триллионах"),
    ),
}
_ORD_STEMS = {
    0: ("нулев", "ой"),
    1: ("перв", "ый"),
    2: ("втор", "ой"),
    3: ("треть", "ий"),
    4: ("четвёрт", "ый"),
    5: ("пят", "ый"),
    6: ("шест", "ой"),
    7: ("седьм", "ой"),
    8: ("восьм", "ой"),
    9: ("девят", "ый"),
    10: ("десят", "ый"),
    11: ("одиннадцат", "ый"),
    12: ("двенадцат", "ый"),
    13: ("тринадцат", "ый"),
    14: ("четырнадцат", "ый"),
    15: ("пятнадцат", "ый"),
    16: ("шестнадцат", "ый"),
    17: ("семнадцат", "ый"),
    18: ("восемнадцат", "ый"),
    19: ("девятнадцат", "ый"),
}


def _case_index(case) -> int:
    value = getattr(case, "value", case) or "nominative"
    return {
        "nominative": 0,
        "genitive": 1,
        "dative": 2,
        "accusative": 3,
        "instrumental": 4,
        "prepositional": 5,
        "locative": 5,
    }.get(value, 0)


def _gender_key(gender, plural: bool = False) -> str:
    if plural:
        return "p"
    value = getattr(gender, "value", gender)
    return {"feminine": "f", "neuter": "n", "plural": "p"}.get(value, "m")


def plural_category(value: int) -> str:
    n100, n10 = abs(value) % 100, abs(value) % 10
    if 11 <= n100 <= 14:
        return "many"
    if n10 == 1:
        return "one"
    if 2 <= n10 <= 4:
        return "few"
    return "many"


class RussianRenderer:
    locale = "ru"

    @staticmethod
    def capabilities() -> LocaleCapabilities:
        cases = frozenset(
            {
                "nominative",
                "genitive",
                "dative",
                "accusative",
                "instrumental",
                "prepositional",
                "locative",
            }
        )
        common_cases = cases
        common_animacies = frozenset({"animate", "inanimate"})
        common_numbers = frozenset({"singular", "plural"})
        common_genders = frozenset({Gender.MASCULINE, Gender.FEMININE, Gender.NEUTER})
        return LocaleCapabilities(
            profiles=(
                CapabilityProfile(
                    NumeralForm.CARDINAL,
                    syntaxes=frozenset({Syntax.STANDALONE, Syntax.ATTRIBUTIVE}),
                    domain=NumericDomain(maximum=10**18 - 1),
                    cases=common_cases,
                    animacies=common_animacies,
                    grammatical_numbers=common_numbers,
                    genders=common_genders,
                ),
                CapabilityProfile(
                    NumeralForm.ORDINAL,
                    syntaxes=frozenset({Syntax.STANDALONE, Syntax.ORDINAL_ADJECTIVAL}),
                    domain=NumericDomain(
                        minimum=0, maximum=10**18 - 1, allow_negative=False
                    ),
                    cases=common_cases,
                    animacies=common_animacies,
                    grammatical_numbers=common_numbers,
                    genders=common_genders,
                ),
                CapabilityProfile(NumeralForm.DIGITS),
                CapabilityProfile(NumeralForm.DECIMAL),
                CapabilityProfile(NumeralForm.FRACTION),
                CapabilityProfile(NumeralForm.YEAR),
            ),
            notes=(
                "Russian case, gender, number, and animacy inventories are explicit.",
                "Scale support covers thousand through quintillion.",
            ),
        )

    def render(self, request: NumeralRequest) -> NumeralResult:
        validate_request(request, self.capabilities())
        value = request.value
        if request.form is NumeralForm.DIGITS:
            text = self._digits(value)
        elif request.form is NumeralForm.DECIMAL:
            text = self._decimal(value)
        elif request.form is NumeralForm.FRACTION:
            text = self._fraction(value)
        elif request.form is NumeralForm.ORDINAL:
            text = self._ordinal(require_int(value), request.morphology)
        elif request.form is NumeralForm.ORDINAL_NUMERIC:
            text = f"{value}."
        else:
            text = self._cardinal(require_int(value), request.morphology)
        return NumeralResult(
            text, request.locale, request.form, request.style, request.morphology
        )

    def _cardinal(self, value: int, morphology) -> str:
        if value < 0:
            return "минус " + self._cardinal(-value, morphology)
        case = _case_index(morphology.case)
        gender = _gender_key(
            morphology.gender, morphology.grammatical_number == "plural"
        )
        animate = getattr(morphology.animacy, "value", morphology.animacy) == "animate"
        return self._integer(value, case, gender, animate)

    def _integer(self, value: int, case: int, gender: str, animate: bool) -> str:
        if value == 0:
            return self._under(0, case, gender, animate)
        if value < 1000:
            return self._under(value, case, gender, animate)
        parts = []
        for exponent in sorted(_SCALE_NOM, reverse=True):
            scale = 10**exponent
            if value >= scale:
                group, value = divmod(value, scale)
                scale_nom = _SCALE_NOM[exponent][0]
                scale_gender = "f" if exponent == 3 else "m"
                parts.append(self._integer(group, case, scale_gender, animate))
                parts.append(self._scale(group, scale_nom, case))
        if value:
            parts.append(self._integer(value, case, gender, animate))
        return " ".join(parts)

    def _scale(self, group: int, name: str, case: int) -> str:
        forms = _SCALE_CASES.get(name)
        if forms is None:
            return name
        category = (
            0
            if group % 10 == 1 and group % 100 != 11
            else 1
            if group % 10 in (2, 3, 4) and not 12 <= group % 100 <= 14
            else 2
        )
        return forms[case][category]

    def _under(self, value: int, case: int, gender: str, animate: bool) -> str:
        if value < 20:
            if 10 <= value < 20:
                if case == 0 or (case == 3 and not animate):
                    return _UNDER_20[value]
                if case in (1, 2, 5):
                    return _UNDER_20[value] + "и" if value != 10 else "десяти"
                if case == 3:
                    return _UNDER_20[value] + "и"
                return _UNDER_20[value] + "ю"
            entry = _ONES.get(value, _ONES_SIMPLE.get(value))
            if isinstance(entry, dict):
                entry = entry[gender]
            if isinstance(entry, tuple) and len(entry) == 6:
                item = entry[case]
                return (
                    item[0]
                    if isinstance(item, tuple) and animate
                    else item[1]
                    if isinstance(item, tuple)
                    else item
                )
            return str(entry)
        if value < 100:
            tens, ones = divmod(value, 10)
            words = [_TENS_CASES[tens][case]]
            if ones:
                words.append(self._under(ones, case, gender, animate))
            return " ".join(words)
        hundreds, remainder = divmod(value, 100)
        words = [_HUNDRED_CASES[hundreds][case]]
        if remainder:
            words.append(self._under(remainder, case, gender, animate))
        return " ".join(words)

    def _ordinal(self, value: int, morphology) -> str:
        if value < 0:
            raise InvalidValueError("Russian ordinal requires a non-negative integer")
        case = _case_index(morphology.case)
        gender = _gender_key(
            morphology.gender, morphology.grammatical_number == "plural"
        )
        animate = getattr(morphology.animacy, "value", morphology.animacy) == "animate"
        if value < 20:
            if value == 3:
                special = {
                    "m": (
                        "третий",
                        "третьего",
                        "третьему",
                        "третьего" if animate else "третий",
                        "третьим",
                        "третьем",
                    ),
                    "f": (
                        "третья",
                        "третьей",
                        "третьей",
                        "третью",
                        "третьей",
                        "третьей",
                    ),
                    "n": (
                        "третье",
                        "третьего",
                        "третьему",
                        "третье",
                        "третьим",
                        "третьем",
                    ),
                    "p": (
                        "третьи",
                        "третьих",
                        "третьим",
                        "третьих" if animate else "третьи",
                        "третьими",
                        "третьих",
                    ),
                }
                return special[gender][case]
            return self._ordinal_word(value, case, gender, animate)
        if value < 100:
            tens, ones = divmod(value, 10)
            if ones:
                if ones == 3 and case == 0 and gender == "m":
                    return f"{_TENS_CASES[tens][0]} третий"
                return f"{_TENS_CASES[tens][0]} {self._ordinal_word(ones, case, gender, animate)}"
            return self._ordinal_tens(tens, case, gender, animate)
        for exponent in sorted(_SCALE_NOM, reverse=True):
            scale = 10**exponent
            if value >= scale:
                group, remainder = divmod(value, scale)
                scale_name = _SCALE_NOM[exponent][0]
                if remainder:
                    scale_gender = "f" if exponent == 3 else "m"
                    prefix = self._integer(group, 0, scale_gender, animate)
                    return f"{prefix} {self._scale(group, scale_name, 0)} {self._ordinal(remainder, morphology)}"
                if group == 1:
                    return self._ordinal_scale(scale_name, case, gender)
                return self._integer(group, 1, "m", animate) + self._ordinal_scale(
                    scale_name, case, gender
                )
        hundreds, remainder = divmod(value, 100)
        prefix = _HUNDRED_CASES[hundreds][0]
        return (
            f"{prefix} {self._ordinal(remainder, morphology)}"
            if remainder
            else self._ordinal_hundred(hundreds, case, gender, animate)
        )

    def _ordinal_word(self, value: int, case: int, gender: str, animate: bool) -> str:
        stem, ending = _ORD_STEMS.get(value, (str(_UNDER_20[value]), "ый"))
        endings = {
            "m": (ending, "ого", "ому", "ого" if animate else ending, "ым", "ом"),
            "f": (
                "яя" if stem.endswith("ь") else "ая",
                "ей" if stem.endswith("ь") else "ой",
                "ей" if stem.endswith("ь") else "ой",
                "юю" if stem.endswith("ь") else "ую",
                "ей" if stem.endswith("ь") else "ой",
                "ей" if stem.endswith("ь") else "ой",
            ),
            "n": (
                "ее" if stem.endswith("ь") else "ое",
                "его" if stem.endswith("ь") else "ого",
                "ему" if stem.endswith("ь") else "ому",
                "ее" if stem.endswith("ь") else "ое",
                "им" if stem.endswith("ь") else "ым",
                "ем" if stem.endswith("ь") else "ом",
            ),
            "p": (
                "ие" if stem.endswith("ь") else "ые",
                "их",
                "им",
                "их" if animate else ("ие" if stem.endswith("ь") else "ые"),
                "ими",
                "их",
            ),
        }
        return stem + endings[gender][case]

    def _ordinal_tens(self, tens: int, case: int, gender: str, animate: bool) -> str:
        stems = {
            2: "двадцат",
            3: "тридцат",
            4: "сороков",
            5: "пятидесят",
            6: "шестидесят",
            7: "семидесят",
            8: "восьмидесят",
            9: "девяност",
        }
        return self._ordinal_from_stem(
            stems[tens], case, gender, animate, "ый" if tens not in (4, 9) else "ой"
        )

    def _ordinal_from_stem(self, stem, case, gender, animate, ending):
        return (
            self._ordinal_word(1, case, gender, animate).replace(
                "первый", stem + ending
            )
            if case == 0 and gender == "m"
            else stem
            + {
                "m": (ending, "ого", "ому", "ого", "ым", "ом"),
                "f": ("ая", "ой", "ой", "ую", "ой", "ой"),
                "n": ("ое", "ого", "ому", "ое", "ым", "ом"),
                "p": ("ые", "ых", "ым", "ые", "ыми", "ых"),
            }[gender][case]
        )

    def _ordinal_scale(self, name, case, gender):
        stem = name.removesuffix("а")
        return self._ordinal_from_stem(stem + "н", case, gender, False, "ый")

    def _ordinal_hundred(self, hundreds, case, gender, animate):
        stem = {
            1: "сот",
            2: "двухсот",
            3: "трёхсот",
            4: "четырёхсот",
            5: "пятисот",
            6: "шестисот",
            7: "семисот",
            8: "восьмисот",
            9: "девятисот",
        }[hundreds]
        return self._ordinal_from_stem(stem, case, gender, animate, "ый")

    def _digits(self, value) -> str:
        if isinstance(value, DigitSequence):
            digits, negative = value.digits, False
        elif isinstance(value, int) and not isinstance(value, bool):
            negative, digits = value < 0, str(abs(value))
        else:
            raise InvalidValueError("digits form requires an integer or DigitSequence")
        return ("минус " if negative else "") + " ".join(
            _DIGITS[int(d)] for d in digits
        )

    def _decimal(self, value) -> str:
        if not isinstance(value, DecimalNumber):
            raise InvalidValueError("decimal form requires DecimalNumber or Decimal")
        sign = "минус " if value.negative else ""
        return (
            f"{sign}{self._integer(int(value.integer), 0, 'm', False)} точка "
            + " ".join(_DIGITS[int(d)] for d in value.fraction)
        )

    def _fraction(self, value) -> str:
        if not isinstance(value, FractionNumber):
            raise InvalidValueError("fraction form requires FractionNumber or Fraction")
        if value.numerator < 0:
            return "минус " + self._fraction(
                FractionNumber(-value.numerator, value.denominator)
            )
        denominator = {
            2: "вторая",
            3: "третья",
            4: "четвёртая",
            5: "пятая",
            6: "шестая",
            7: "седьмая",
            8: "восьмая",
            9: "девятая",
            10: "десятая",
        }.get(
            value.denominator,
            self._ordinal(value.denominator, Morphology(gender=Gender.FEMININE)),
        )
        return f"{self._integer(value.numerator, 0, 'f', False)} {denominator if value.numerator == 1 else denominator[:-1] + 'ых'}"
