"""Finnish numeral rendering with an extensible fifteen-case inventory."""

from __future__ import annotations

from ..errors import InvalidValueError
from ..locale import CapabilityProfile, LocaleCapabilities, NumericDomain
from ..model import NumeralForm, NumeralRequest, NumeralResult, Syntax
from .base import validate_request

_UNDER_20 = ("nolla", "yksi", "kaksi", "kolme", "neljä", "viisi", "kuusi", "seitsemän", "kahdeksan", "yhdeksän", "kymmenen", "yksitoista", "kaksitoista", "kolmetoista", "neljätoista", "viisitoista", "kuusitoista", "seitsemäntoista", "kahdeksantoista", "yhdeksäntoista")
_TENS = ("", "", "kaksikymmentä", "kolmekymmentä", "neljäkymmentä", "viisikymmentä", "kuusikymmentä", "seitsemänkymmentä", "kahdeksankymmentä", "yhdeksänkymmentä")
_ORDINALS = {0: "nolla", 1: "ensimmäinen", 2: "toinen", 3: "kolmas", 4: "neljäs", 5: "viides", 6: "kuudes", 7: "seitsemäs", 8: "kahdeksas", 9: "yhdeksäs", 10: "kymmenes"}
_CASES = frozenset({"nominative", "genitive", "accusative", "partitive", "inessive", "elative", "illative", "adessive", "ablative", "allative", "essive", "translative", "instructive", "abessive", "comitative"})
_SMALL_CASES = {
    1: {"genitive": "yhden", "accusative": "yhden", "partitive": "yhtä", "inessive": "yhdessä", "elative": "yhdestä", "illative": "yhteen", "adessive": "yhdellä", "ablative": "yhdeltä", "allative": "yhdelle", "essive": "yhtenä", "translative": "yhdeksi", "instructive": "yksin", "abessive": "yhdettä", "comitative": "yksine"},
    2: {"genitive": "kahden", "accusative": "kahden", "partitive": "kahta", "inessive": "kahdessa", "elative": "kahdesta", "illative": "kahteen", "adessive": "kahdella", "ablative": "kahdelta", "allative": "kahdelle", "essive": "kahtena", "translative": "kahdeksi", "instructive": "kaksin", "abessive": "kahdetta", "comitative": "kaksine"},
    3: {"genitive": "kolmen", "accusative": "kolmen", "partitive": "kolmea", "inessive": "kolmessa", "elative": "kolmesta", "illative": "kolmeen", "adessive": "kolmella", "ablative": "kolmelta", "allative": "kolmelle", "essive": "kolmena", "translative": "kolmeksi", "instructive": "kolmin", "abessive": "kolmetta", "comitative": "kolmine"},
}


def _case_name(case) -> str:
    return getattr(case, "value", case) or "nominative"


class FinnishRenderer:
    locale = "fi"

    @staticmethod
    def capabilities() -> LocaleCapabilities:
        common = dict(cases=_CASES, grammatical_numbers=frozenset({"singular", "plural"}), domain=NumericDomain(maximum=10**18 - 1))
        return LocaleCapabilities(profiles=(
            CapabilityProfile(NumeralForm.CARDINAL, syntaxes=frozenset({Syntax.STANDALONE, Syntax.ATTRIBUTIVE}), **common),
            CapabilityProfile(NumeralForm.ORDINAL, syntaxes=frozenset({Syntax.STANDALONE, Syntax.ORDINAL_ADJECTIVAL}), **common),
            CapabilityProfile(NumeralForm.ORDINAL_NUMERIC, **common),
            CapabilityProfile(NumeralForm.DIGITS), CapabilityProfile(NumeralForm.YEAR),
        ), notes=("Finnish advertises the full reviewed fifteen-case inventory.",))

    def render(self, request: NumeralRequest) -> NumeralResult:
        validate_request(request, self.capabilities())
        if request.form is NumeralForm.CARDINAL:
            text = self._cardinal(request.value, request.morphology)
        elif request.form is NumeralForm.ORDINAL:
            text = self._ordinal(request.value, request.morphology)
        elif request.form is NumeralForm.ORDINAL_NUMERIC:
            text = f"{request.value}."
        elif request.form is NumeralForm.DIGITS:
            text = " ".join(_UNDER_20[int(d)] if int(d) < 20 else str(d) for d in str(request.value))
        elif request.form is NumeralForm.YEAR:
            text = self._cardinal(request.value, request.morphology)
        else:
            raise InvalidValueError(f"Finnish does not implement {request.form.value}")
        return NumeralResult(text, request.locale, request.form, request.style, request.morphology)

    def _cardinal(self, value: int, morphology) -> str:
        if value < 0:
            return "miinus " + self._cardinal(-value, morphology)
        if value < 20:
            text = _UNDER_20[value]
            case = _case_name(morphology.case)
            if value in _SMALL_CASES and case != "nominative" and morphology.grammatical_number != "plural":
                return _SMALL_CASES[value][case]
        elif value < 100:
            tens, ones = divmod(value, 10)
            text = _TENS[tens] + (" " + _UNDER_20[ones] if ones else "")
        elif value < 1000:
            hundreds, rest = divmod(value, 100)
            text = ("sata" if hundreds == 1 else _UNDER_20[hundreds] + "sataa")
            if rest:
                text += " " + self._cardinal(rest, morphology)
        else:
            scale, name = self._scale(value)
            group, rest = divmod(value, scale)
            text = (name if group == 1 else self._cardinal(group, morphology) + " " + name)
            if rest:
                text += " " + self._cardinal(rest, morphology)
        return self._inflect(text, _case_name(morphology.case), morphology.grammatical_number == "plural")

    @staticmethod
    def _scale(value: int):
        for scale, name in ((10**18, "triljoona"), (10**15, "kvadriljoona"), (10**12, "biljoona"), (10**9, "miljardi"), (10**6, "miljoona"), (1000, "tuhat")):
            if value >= scale:
                return scale, name
        return 1, ""

    def _ordinal(self, value: int, morphology) -> str:
        if value < 0:
            raise InvalidValueError("Finnish ordinal requires a non-negative integer")
        if value in _ORDINALS:
            text = _ORDINALS[value]
        elif value < 100:
            tens, ones = divmod(value, 10)
            text = (_TENS[tens].replace("kymmentä", "kymmenes") if not ones else _TENS[tens] + " " + self._ordinal(ones, morphology))
        else:
            hundreds, rest = divmod(value, 100)
            text = ("sadas" if hundreds == 1 else _UNDER_20[hundreds] + "sadas")
            if rest:
                text += " " + self._ordinal(rest, morphology)
        return self._inflect(text, _case_name(morphology.case), morphology.grammatical_number == "plural")

    @staticmethod
    def _inflect(text: str, case: str, plural: bool) -> str:
        if case == "nominative" and not plural:
            return text
        suffixes = {"genitive": "n", "accusative": "n", "partitive": "a", "inessive": "ssa", "elative": "sta", "illative": "an", "adessive": "lla", "ablative": "lta", "allative": "lle", "essive": "na", "translative": "ksi", "instructive": "n", "abessive": "tta", "comitative": "ne"}
        suffix = suffixes.get(case, "")
        if plural:
            suffix = {"nominative": "t", "genitive": "en", "accusative": "t", "partitive": "a", "inessive": "ssa", "elative": "sta", "illative": "in", "adessive": "lla", "ablative": "lta", "allative": "lle", "essive": "na", "translative": "ksi", "instructive": "n", "abessive": "tta", "comitative": "ne"}.get(case, suffix)
        words = text.split(" ")
        words[-1] += suffix
        return " ".join(words)
