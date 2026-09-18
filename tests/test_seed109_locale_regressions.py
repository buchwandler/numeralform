"""Seed-109 locale grammar regressions, independent of num2words.

Expected strings are the reviewed canonical surfaces for each locale, taken
from the audited grammar rules in 01_todo.md. They must not be regenerated
from the oracle.
"""

from __future__ import annotations

import pytest

from numeralform import DecimalNumber, render


def decimal(text: str) -> DecimalNumber:
    negative = text.startswith("-")
    integer, _, fraction = text.lstrip("-").partition(".")
    return DecimalNumber(integer, fraction, negative)


def test_amharic_decimal_negative_uses_native_prefix():
    assert render(decimal("-0.01"), locale="am", form="decimal") == (
        "አሉታዊ ዜሮ ነጥብ ዜሮ አንድ"
    )


def test_catalan_negative_prefix_is_native():
    assert render(-3, locale="ca", form="cardinal") == "menys tres"
    assert render(-1000, locale="ca", form="cardinal") == "menys mil"
    assert render(decimal("-1.5"), locale="ca", form="decimal") == (
        "menys un punt cinc"
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (1000, "seribu"),
        (1001, "seribu satu"),
        (1005, "seribu lima"),
        (1100, "seribu seratus"),
        (2000, "dua ribu"),
        (21000, "dua puluh satu ribu"),
        (1000000, "satu juta"),
        (1001000, "satu juta satu ribu"),
        (1100000, "satu juta seratus ribu"),
        (
            123456789,
            (
                "seratus dua puluh tiga juta empat ratus lima puluh enam ribu "
                "tujuh ratus delapan puluh sembilan"
            ),
        ),
        (
            549001460,
            "lima ratus empat puluh sembilan juta satu ribu empat ratus enam puluh",
        ),
        (
            693101356,
            (
                "enam ratus sembilan puluh tiga juta seratus satu ribu "
                "tiga ratus lima puluh enam"
            ),
        ),
    ],
)
def test_indonesian_scale_contraction(value, expected):
    assert render(value, locale="id", form="cardinal") == expected


def test_indonesian_negative_prefix_is_min():
    assert render(-1000, locale="id", form="cardinal") == "min seribu"
    assert render(decimal("-2.5"), locale="id", form="decimal") == ("min dua koma lima")


def test_indonesian_year_reads_thousands_with_contraction():
    assert render(1899, locale="id", form="year") == (
        "seribu delapan ratus sembilan puluh sembilan"
    )


def test_czech_decimal_uses_cela_marker_and_keeps_sign():
    assert render(decimal("1.20"), locale="cs", form="decimal") == ("jedna celá dvacet")
    assert render(decimal("-0.75"), locale="cs", form="decimal") == (
        "mínus nula celá sedmdesát pět"
    )


def test_chechen_decimal_uses_native_conjunction():
    assert render(decimal("12.50"), locale="ce", form="decimal") == (
        "шийтта а пхиъ ноль"
    )
    assert render(decimal("-0.01"), locale="ce", form="decimal") == (
        "тӀехьара ноль а ноль цхьаъ"
    )


@pytest.mark.parametrize(
    ("locale", "value", "expected"),
    [
        ("hi", 14, "चौदह"),
        ("hi", 19, "उन्नीस"),
        ("hi", 42, "बयालीस"),
        ("hi", 99, "निन्यानवे"),
        ("hi", 100, "एक सौ"),
        ("hi", 1000, "एक हज़ार"),
        ("hi", 1999, "एक हज़ार नौ सौ निन्यानवे"),
        ("hi", 100000, "एक लाख"),
        ("hi", 10000000, "एक करोड़"),
        ("hi", 292284101, "उनतीस करोड़ बाईस लाख चौरासी हज़ार एक सौ एक"),
        ("hy", 14, "տասնչորս"),
        ("hy", 19, "տասնինը"),
        ("hy", 42, "քառասուներկու"),
        ("hy", 99, "իննսուն ինը"),
        ("hy", 100, "հարյուր"),
        ("hy", 1000, "հազար"),
        ("hy", 1000000, "մեկ միլիոն"),
        ("hy", 999, "ինը հարյուր իննսուն ինը"),
        ("hy", 123456, "հարյուր քսաներեք հազար չորս հարյուր հիսունվեց"),
        ("mn", 14, "арван дөрөв"),
        ("mn", 19, "арван ес"),
        ("mn", 42, "дөчин хоёр"),
        ("mn", 99, "ерэн ес"),
        ("mn", 100, "зуу"),
        ("mn", 1234, "нэг мянга хоёр зуун гучин дөрөв"),
        ("mn", 100000, "зуун мянга"),
        ("mn", 123456, "зуун хорин гурван мянга дөрвөн зуун тавин зургаа"),
        ("mn", 999999, "есөн зуун ерэн есөн мянга есөн зуун ерэн ес"),
        (
            "mn",
            386897916,
            (
                "гурван зуун наян зургаан сая найман зуун ерэн "
                "долоон мянга есөн зуун арван зургаа"
            ),
        ),
    ],
)
def test_sparse_renderer_cardinals(locale, value, expected):
    assert render(value, locale=locale, form="cardinal") == expected


@pytest.mark.parametrize(
    ("locale", "value", "expected"),
    [
        ("hi", 1635, "एक हज़ार छः सौ पैंतीस"),
        ("hy", 1450, "հազար չորս հարյուր հիսուն թվական"),
        ("mn", 7845, "долоон мянга найман зуун дөчин таван он"),
        ("mn", 2000, "хоёр мянган он"),
    ],
)
def test_sparse_renderer_years(locale, value, expected):
    assert render(value, locale=locale, form="year") == expected


def test_sparse_renderers_never_spell_cardinals_digit_by_digit():
    from numeralform.registry import resolve

    for locale in ("hi", "hy", "mn"):
        digits = resolve(locale).data.digits
        for value in (14, 19, 42, 76, 99, 472):
            text = render(value, locale=locale, form="cardinal")
            spelled = " ".join(digits[int(d)] for d in str(value))
            assert text != spelled, (locale, value, text)


def test_no_registered_cardinal_spells_subgroups_digit_by_digit():
    from numeralform.registry import registered_locales, resolve
    from numeralform.renderers._fixtures import CARDINALS
    from numeralform.renderers._shared import (
        LexicalRenderer,
        contiguous_integer_domain,
    )

    checked = 0
    for locale in registered_locales():
        renderer = resolve(locale)
        target = getattr(renderer, "_delegate", renderer)
        if not isinstance(target, LexicalRenderer):
            continue
        if locale not in CARDINALS:
            continue
        block = contiguous_integer_domain(CARDINALS[locale])
        # Sparse tables are owned by dedicated per-locale tests (hi, hy, mn).
        if block is None or block[1] < 100:
            continue
        digits = target.data.digits
        for value in (42, 76, 99):
            text = render(value, locale=locale, form="cardinal")
            spelled = target.data.compound.join(digits[int(d)] for d in str(value))
            assert text != spelled, (locale, value, text)
            checked += 1
    assert checked > 0


@pytest.mark.parametrize(
    ("locale", "value", "expected"),
    [
        # Arabic: dual/plural/case scale morphology and conjunctions.
        ("ar", 3000, "ثلاثة آلاف"),
        ("ar", 2001, "ألفان و واحد"),
        ("ar", 1999, "ألف و تسعمائة و تسعة و تسعون"),
        (
            "ar",
            179409368,
            "مائة و تسعة و سبعون مليوناً و أربعمائة و تسعة ألفاً و ثلاثمائة و ثمانية و ستون",
        ),
        ("ar", 200000, "مئتا ألف"),
        # Belarusian / Ukrainian / Serbian: feminine thousand + x1 singular.
        ("be", 21000, "дваццаць адна тысяча"),
        ("be", 21000000, "дваццаць адзін мільён"),
        ("uk", 22000, "двадцять дві тисячі"),
        ("uk", 101000000, "сто один мільйон"),
        ("sr", 21000, "dvadeset jedna hiljada"),
        ("sr", 101000000, "sto jedan milion"),
        # Slovenian: masculine prefixes, tisoč without inflection.
        ("sl", 2001, "dva tisoč ena"),
        ("sl", 101000, "sto en tisoč"),
        ("sl", 3000000, "trije milijoni"),
        ("sl", 2000000, "dva milijona"),
        # Lithuanian / Latvian.
        ("lt", 21000, "dvidešimt vienas tūkstantis"),
        ("lt", 100000, "vienas šimtas tūkstančių"),
        ("lv", 21000, "divdesmit viens tūkstotis"),
        ("lv", 101, "simtu viens"),
        ("lv", 110, "simts desmit"),
        # Romanian: o mie / de mii / feminine agreement.
        ("ro", 1000, "o mie"),
        ("ro", 21000, "douăzeci și unu de mii"),
        ("ro", 2000000, "două milioane"),
        ("ro", 100000, "o sută de mii"),
        # Slovak: compound thousands, spaced millions.
        ("sk", 3000, "tritisíc"),
        ("sk", 22000, "dvadsaťdvatisíc"),
        ("sk", 2000000, "dva milióny"),
        ("sk", 23000000, "dvadsaťtri miliónov"),
        # Hebrew: gender, construct, and vav.
        ("he", 3000, "שלושת אלפים"),
        ("he", 2001, "אלפיים ואחת"),
        ("he", 3000000, "שלושה מיליון"),
        # Icelandic: gender agreement and coordinating og.
        ("is", 3000, "þrjú þúsund"),
        ("is", 21000, "tuttugu og eitt þúsund"),
        ("is", 2001, "tvö þúsund og einn"),
        ("is", 2000000, "tvær milljónir"),
        # Telugu: scale pluralization.
        ("te", 3001, "మూడు వేయిల ఒకటి"),
        ("te", 100001, "ఒకటి లక్షల ఒకటి"),
        ("te", 10000000, "ఒకటి కోట్ల"),
        # Welsh: feminine and mutation.
        ("cy", 3000, "tair mil"),
        ("cy", 4000, "pedair mil"),
        ("cy", 2000000, "dau filiwn"),
        ("cy", 2345, "dwy fil tri chant a phump a deugain"),
        # Chechen: attributive prefixes.
        ("ce", 2000, "ши эзар"),
        ("ce", 25000, "ткъе пхи эзар"),
        ("ce", 440000, "ди бӀе шовзткъе эзар"),
        # Hungarian: hyphenation and két.
        ("hu", 2000, "kétezer"),
        ("hu", 2001, "kétezer-egy"),
        ("hu", 95193, "kilencvenötezer-százkilencvenhárom"),
        ("hu", 2000000, "kétmillió"),
        ("hu", 1002, "ezerkét"),
        # Kannada: explicit one and connective glue.
        ("kn", 1000, "ಒಂದು ಸಾವಿರ"),
        ("kn", 2001, "ಎರಡು ಸಾವಿರದ ಒಂದು"),
        ("kn", 1074, "ಒಂದು ಸಾವಿರದ ಎಪ್ಪತ್ತ್ ನಾಲ್ಕು"),
        ("kn", 100001, "ಒಂದು ಲಕ್ಷದ ಒಂದು"),
        # Bengali: explicit one-thousand.
        ("bn", 1002, "এক হাজার দুই"),
    ],
)
def test_morphology_renderer_cardinals(locale, value, expected):
    assert render(value, locale=locale, form="cardinal") == expected


@pytest.mark.parametrize(
    ("locale", "value", "expected"),
    [
        ("hu", "1.20", "egy egész húsz század"),
        ("hu", "-0.75", "mínusz nulla egész hetvenöt század"),
        ("hu", "0.067", "nulla egész hatvanhét ezred"),
        ("be", "1.20", "адзін коска дваццаць"),
        ("be", "0.079", "нуль коска нуль семдзесят дзевяць"),
        ("sk", "1.10", "jeden celých desať"),
        ("sk", "9.99", "deväť celých deväťdesiatdeväť"),
        ("lv", "99.99", "deviņdesmit deviņi komats deviņdesmit deviņi"),
        ("lt", "0.10", "nulis kablelis dešimt"),
    ],
)
def test_morphology_renderer_decimals(locale, value, expected):
    assert render(decimal(value), locale=locale, form="decimal") == expected


def test_morphology_renderer_years_follow_cardinal_composition():
    assert render(1999, locale="ar", form="year") == ("ألف و تسعمائة و تسعة و تسعون")
    assert render(7845, locale="mn", form="year") == (
        "долоон мянга найман зуун дөчин таван он"
    )
    assert render(1074, locale="kn", form="year") == ("ಒಂದು ಸಾವಿರದ ಎಪ್ಪತ್ತ್ ನಾಲ್ಕು")


@pytest.mark.parametrize(
    ("locale", "value", "expected"),
    [
        # Danish: compound thousands, spaced millions, ettusind.
        ("da", 1000, "ettusind"),
        ("da", 1001, "ettusinde og et"),
        ("da", 2034, "totusinde og fireogtredive"),
        ("da", 25000, "femogtyvetusind"),
        ("da", 278482, "tohundrede og otteoghalvfjerdstusindfirehundrede og toogfirs"),
        ("da", 2000000, "to millioner"),
        # Norwegian: spaced groups, singular million, og before sub-hundred.
        ("no", 3001, "tre tusen og en"),
        ("no", 99876, "nittini tusen åtte hundre og syttiseks"),
        ("no", 2000000, "to million"),
        # Tetum: scale-first order and resin conjunction.
        ("tet", 5000, "rihun lima"),
        ("tet", 1005, "rihun ida lima"),
        ("tet", 15001, "rihun sanulu resin lima resin ida"),
        ("tet", 2000000, "miliaun rua"),
        # Tajik: у conjunction between scale groups.
        ("tg", 99876, "наваду нӯҳ ҳазору ҳаштсаду ҳафтоду шаш"),
        ("tg", 8100, "ҳашт ҳазору яксад"),
        (
            "tg",
            451278482,
            "чорсаду панҷову як миллиону дусаду ҳафтоду ҳашт ҳазору чорсаду ҳаштоду ду",
        ),
        # Dutch: compound thousands, spaced miljoen.
        ("nl", 2000000, "twee miljoen"),
        (
            "nl",
            451278482,
            "vierhonderdeenenvijftig miljoen tweehonderdachtenzeventigduizendvierhonderdtweeëntachtig",
        ),
        # Persian: و conjunction across scale boundaries.
        ("fa", 99876, "نود و نه هزار و هشتصد و هفتاد و شش"),
        (
            "fa",
            451278482,
            "چهارصد و پنجاه و یک میلیون و دویست و هفتاد و هشت هزار و چهارصد و هشتاد و دو",
        ),
    ],
)
def test_join_order_renderer_cardinals(locale, value, expected):
    assert render(value, locale=locale, form="cardinal") == expected
