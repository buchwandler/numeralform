"""Small, explicit ``num2words``-shaped adapter over Numeralform."""

from __future__ import annotations

from .. import render
from ..errors import InvalidRequestError

_SUPPORTED_OPTIONS = frozenset(
    {
        "syntax",
        "gender",
        "case",
        "animacy",
        "grammatical_number",
        "noun_class",
        "style",
    }
)
_FORM_MAP = {
    "cardinal": "cardinal",
    "ordinal": "ordinal",
    "year": "year",
}


def num2words(
    value: object, *, lang: str = "en", to: str = "cardinal", **kwargs
) -> str:
    """Render a reviewed legacy-compatible request through Numeralform.

    Only options with direct semantic equivalents are accepted. Legacy options
    such as ``ordinal_num`` and ``currency`` deliberately fail rather than
    being silently discarded.
    """
    if not isinstance(lang, str) or not lang.strip():
        raise InvalidRequestError("lang must be a non-empty locale identifier")
    if not isinstance(to, str) or to not in _FORM_MAP:
        supported = ", ".join(sorted(_FORM_MAP))
        raise InvalidRequestError(
            f"unsupported num2words to={to!r}; supported: {supported}"
        )
    unknown = sorted(set(kwargs) - _SUPPORTED_OPTIONS)
    if unknown:
        raise InvalidRequestError(
            "unsupported num2words options: " + ", ".join(unknown)
        )
    return render(value, locale=lang, form=_FORM_MAP[to], **kwargs)
