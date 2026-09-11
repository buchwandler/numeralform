# Currency API

Currency rendering is a sibling canonical subsystem. It preserves structured
money values, applies locale-owned terminology, and reports unsupported requests
with Numeralform errors.

## Values and units

`MoneyAmount(major, minor, currency)` treats an integer input as major units.
The currency is normalized to an uppercase three-letter code. `minor_units` must
match the supported currency scale at rendering time: JPY and KRW use zero
decimals, ordinary currencies use two, and KWD/BHD use three. A mismatched
structured scale is rejected rather than silently reinterpreted.

```python
from numeralform import MoneyAmount, render_currency, realize_currency

amount = MoneyAmount(1, 50, "usd")
render_currency(amount)  # "one dollar and fifty cents"
realize_currency(amount).request.amount.currency  # "USD"
```

When a primitive integer/decimal/string/float is supplied without `currency`,
EUR is the default. A `MoneyAmount` owns its currency; an explicit conflicting
currency raises `InvalidRequestError`.

## Decimal conversion and rounding

Decimal, string, and float inputs are converted to the currency's minor scale
using `ROUND_HALF_UP`. Values are finite and invalid numeric values raise
`InvalidValueError`. Negative values retain their sign and use the locale's
negative currency prefix.

`cents=True` renders the minor value as words. `cents=False` renders zero-padded
minor digits. A custom `separator` replaces the locale connector.

## Requests and capabilities

`CurrencyRequest` contains a `MoneyAmount`, locale, `cents` boolean, and optional
separator. `CurrencyResult` contains the rendered text, request, and resolved
locale. `supports_currency(locale, currency, allow_fallback=False)` first
canonicalizes and resolves the locale, then checks regional and language
terminology. With `allow_fallback=True`, it may use lexical English terminology;
an unrenderable locale still returns `False`.

Unknown currencies, unsupported terminology, invalid scales, and invalid request
fields use the canonical `NumeralFormError` hierarchy, including
`UnsupportedCurrencyError`.

## Compatibility difference

Canonical integer currency semantics interpret `5` as five major units. The
`numeralform.compat.num2words` adapter preserves the pinned legacy behavior where
integer currency values are minor units, and translates its legacy options and
exceptions only inside the compatibility namespace.
