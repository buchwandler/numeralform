from decimal import Decimal

from numeralform import render, render_currency


def test_english_regional_cardinal_policy():
    assert render(105, locale="en") == "one hundred five"
    assert render(105, locale="en-US") == "one hundred five"
    assert render(105, locale="en-GB") == "one hundred and five"
    assert render(1001, locale="en-US") == "one thousand one"
    assert render(1001, locale="en-GB") == "one thousand and one"
    assert (
        render(40062400, locale="en-US")
        == "forty million sixty-two thousand four hundred"
    )
    assert (
        render(40062400, locale="en-GB")
        == "forty million sixty-two thousand four hundred"
    )


def test_english_regional_decimal_policy():
    assert render(Decimal("98100.3"), locale="en-US", form="decimal") == (
        "ninety-eight thousand one hundred point three"
    )
    assert render(Decimal("98100.3"), locale="en-GB", form="decimal") == (
        "ninety-eight thousand one hundred point three"
    )
    assert render(Decimal("582378.922"), locale="en-US", form="decimal") == (
        "five hundred eighty-two thousand three hundred seventy-eight point nine two two"
    )
    assert render(Decimal("582378.922"), locale="en-GB", form="decimal") == (
        "five hundred and eighty-two thousand three hundred and seventy-eight point nine two two"
    )


def test_english_regional_currency_policy():
    assert render_currency(Decimal("531.84"), locale="en-US", currency="USD") == (
        "five hundred thirty-one dollars and eighty-four cents"
    )
    assert render_currency(Decimal("531.84"), locale="en-GB", currency="USD") == (
        "five hundred and thirty-one dollars and eighty-four cents"
    )
    assert render_currency(Decimal("928.11"), locale="en-US", currency="GBP") == (
        "nine hundred twenty-eight pounds and eleven pence"
    )
    assert render_currency(Decimal("928.11"), locale="en-GB", currency="GBP") == (
        "nine hundred and twenty-eight pounds and eleven pence"
    )


def test_english_regional_boundaries_and_styles():
    assert render(100, locale="en-GB") == "one hundred"
    assert render(110, locale="en-GB") == "one hundred and ten"
    assert render(1000, locale="en-GB") == "one thousand"
    assert render(1100, locale="en-GB") == "one thousand one hundred"
    assert render(1101, locale="en-GB") == "one thousand one hundred and one"
    assert render(98100, locale="en-GB") == "ninety-eight thousand one hundred"
    assert render(1000001, locale="en-GB") == "one million and one"
    assert render(101, locale="en-US") == "one hundred one"
    assert render(1001, locale="en-US") == "one thousand one"
    assert render(1000001, locale="en-US") == "one million one"
    assert render(105, locale="en", style="british-and") == "one hundred and five"
    assert render(105, locale="en-US", style="british-and") == "one hundred and five"
    assert render(105, locale="en-GB", style="default") == "one hundred and five"
    assert render(105, locale="en-GB", style="british-and") == "one hundred and five"


def test_existing_english_regional_currency_behavior_is_not_changed():
    expected = "five hundred and thirty-one dollars and eighty-four cents"
    assert (
        render_currency(Decimal("531.84"), locale="en-IN", currency="USD") == expected
    )
    assert (
        render_currency(Decimal("531.84"), locale="en-NG", currency="USD") == expected
    )
