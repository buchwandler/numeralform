"""Lithuanian canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import IntegerFractionDecimalRenderer, locale_data


class LithuanianRenderer(IntegerFractionDecimalRenderer):
    locale = "lt"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "lt",
        tuple(CARDINALS["lt"][i] for i in range(10)),
        omit_one_scales=frozenset(),
    )

    def _scale_name(self, scale: int, quotient: int) -> str:
        forms = self.data.scale_forms.get(scale)
        if not forms or len(forms) != 3:
            return super()._scale_name(scale, quotient)
        last = quotient % 10
        if last == 1 and quotient % 100 != 11:
            return forms[0]
        if 2 <= last <= 9 and not 11 <= quotient % 100 <= 19:
            return forms[1]
        return forms[2]
