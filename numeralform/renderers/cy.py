"""Welsh canonical numeral renderer."""

from ._fixtures import CARDINALS, ORDINALS
from ._shared import LexicalRenderer, locale_data

_FEMININE_THOUSAND = {
    "tri": "tair",
    "thri": "thair",
    "pedwar": "pedair",
    "phedwar": "phedair",
    "dau": "dwy",
}


class WelshRenderer(LexicalRenderer):
    locale = "cy"
    cardinals = CARDINALS[locale]
    ordinals = ORDINALS[locale]
    data = locale_data(
        "cy", tuple(CARDINALS["cy"][i] for i in range(10)), negative="meinws"
    )

    def _scale_prefix(self, scale: int, quotient: int) -> str:
        prefix = super()._scale_prefix(scale, quotient)
        if scale != 1_000:
            return prefix
        words = prefix.split(" ")
        start = 0
        for index, word in enumerate(words):
            if word in ("cant", "gant", "chant"):
                start = index + 1
        for index in range(start, len(words)):
            word = words[index]
            if word in _FEMININE_THOUSAND and words[index + 1 : index + 2] != ["ugain"]:
                words[index] = _FEMININE_THOUSAND[word]
                break
        return " ".join(words)

    def _join_scale(
        self,
        *,
        scale: int,
        quotient: int,
        prefix: str,
        scale_name: str,
        remainder: int,
        suffix: str,
    ) -> str:
        if scale == 1_000_000 and quotient == 1:
            # One million drops the leading un.
            prefix = ""
        words = prefix.split()
        if words:
            last = words[-1]
            if scale == 1_000 and last == "dwy":
                # Soft mutation after "dwy": mil -> fil.
                scale_name = "fil"
            elif scale == 1_000_000 and last == "dau":
                # Soft mutation after "dau": miliwn -> filiwn.
                scale_name = "filiwn"
        return super()._join_scale(
            scale=scale,
            quotient=quotient,
            prefix=prefix,
            scale_name=scale_name,
            remainder=remainder,
            suffix=suffix,
        )
