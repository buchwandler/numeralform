"""Command-line wrapper for the numeralform API."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal

from . import (
    DecimalNumber,
    DigitSequence,
    FractionNumber,
    capabilities,
    locales,
    render,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render an already-interpreted numeric value."
    )
    parser.add_argument(
        "value",
        nargs="?",
        help="integer, digit sequence, decimal, or numerator/denominator",
    )
    parser.add_argument("--locale", help="BCP-47 locale identifier")
    parser.add_argument(
        "--form",
        choices=("cardinal", "ordinal", "digits", "decimal", "fraction", "year"),
        default="cardinal",
    )
    parser.add_argument("--syntax", default="standalone")
    parser.add_argument("--gender")
    parser.add_argument("--case", dest="case_")
    parser.add_argument("--animacy")
    parser.add_argument("--style")
    parser.add_argument(
        "--digits", action="store_true", help="treat value as a digit sequence"
    )
    parser.add_argument(
        "--decimal", action="store_true", help="preserve the decimal surface digits"
    )
    parser.add_argument(
        "--fraction", action="store_true", help="treat value as numerator/denominator"
    )
    parser.add_argument("--list-locales", action="store_true")
    parser.add_argument("--capabilities", metavar="LOCALE")
    return parser


def _parse_value(args: argparse.Namespace):
    if args.value is None:
        raise ValueError("a value is required")
    if args.digits:
        return DigitSequence(args.value)
    if args.fraction:
        try:
            numerator, denominator = args.value.split("/", 1)
            return FractionNumber(int(numerator), int(denominator))
        except (ValueError, TypeError) as exc:
            raise ValueError("fraction value must be NUMERATOR/DENOMINATOR") from exc
    if args.decimal:
        try:
            return DecimalNumber.from_decimal(Decimal(args.value))
        except Exception as exc:
            raise ValueError("decimal value is invalid") from exc
    try:
        return int(args.value)
    except ValueError as exc:
        raise ValueError(
            "value must be an integer unless --digits, --decimal, or --fraction is used"
        ) from exc


def _print_capabilities(locale: str) -> None:
    caps = capabilities(locale)
    profiles = sorted(caps.profiles, key=lambda profile: profile.form.value)
    profile_data = [
        {
            "form": profile.form.value,
            "syntaxes": sorted(syntax.value for syntax in profile.syntaxes),
            "genders": sorted(gender.value for gender in profile.genders),
            "cases": sorted(getattr(case, "value", case) for case in profile.cases),
            "animacies": sorted(profile.animacies),
            "grammatical_numbers": sorted(profile.grammatical_numbers),
            "noun_classes": sorted(profile.noun_classes),
            "definitenesses": sorted(profile.definitenesses),
            "states": sorted(profile.states),
            "features": [{"name": feature.name, "values": sorted(feature.values), "boolean": feature.boolean} for feature in profile.features],
            "domain": {"minimum": profile.domain.minimum, "maximum": profile.domain.maximum, "allow_negative": profile.domain.allow_negative, "decimals": profile.domain.decimals, "fractions": profile.domain.fractions},
            "styles": sorted(profile.styles),
        }
        for profile in profiles
    ]
    print(
        json.dumps(
            {
                "locale": locale,
                "forms": sorted(form.value for form in caps.forms),
                "syntaxes": sorted(syntax.value for syntax in caps.syntaxes),
                "genders": sorted(gender.value for gender in caps.genders),
                "cases": sorted(getattr(case, "value", case) for case in caps.cases),
                "animacies": sorted(caps.animacies),
                "grammatical_numbers": sorted(caps.grammatical_numbers),
                "noun_classes": sorted(caps.noun_classes),
                "definitenesses": sorted(caps.definitenesses),
                "states": sorted(caps.states),
                "styles": sorted(caps.styles),
                "profiles": profile_data,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.list_locales:
            print("\n".join(locales()))
            return 0
        if args.capabilities:
            _print_capabilities(args.capabilities)
            return 0
        if args.locale is None:
            parser.error("--locale is required when rendering")
        value = _parse_value(args)
        print(
            render(
                value,
                locale=args.locale,
                form=args.form,
                syntax=args.syntax,
                gender=args.gender,
                case=args.case_,
                animacy=args.animacy,
                style=args.style,
            )
        )
        return 0
    except (ValueError, TypeError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
