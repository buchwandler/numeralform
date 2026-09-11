from decimal import Decimal
from fractions import Fraction

from numeralform import (
    DecimalNumber,
    DigitSequence,
    Morphology,
    NumeralRequest,
    realize,
    render,
)


def typed_examples() -> tuple[str, str, str]:
    cardinal: str = render(42, locale="en")
    digits: str = render(DigitSequence("0042"), locale="en")
    decimal: str = render(DecimalNumber("1", "20"), locale="en")
    fraction: str = render(Fraction(1, 2), locale="en")
    result = realize(Decimal("1.20"), locale="en")
    request = NumeralRequest(42, "en", morphology=Morphology())
    assert result.text and request.locale
    return cardinal, digits, decimal + fraction
