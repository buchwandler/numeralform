from benchmarks.randomized.run import build_parser


def test_randomized_cli_options_are_explicit():
    args = build_parser().parse_args(
        [
            "--cases",
            "3",
            "--seed",
            "auto",
            "--profile",
            "stress",
            "--locale",
            "de",
            "--kind",
            "currency",
            "--target",
            "compat",
            "--record-all",
            "--fail-on-diff",
            "--fail-on-unaccepted",
            "--fail-on-coverage-gap",
        ]
    )
    assert args.cases == 3
    assert args.seed >= 0
    assert args.profile == "stress"
    assert args.locales == ["de"]
    assert args.target == "compat"
    assert args.kinds == ["currency"]
    assert args.record_all
    assert args.fail_on_diff
    assert args.fail_on_unaccepted
    assert args.fail_on_coverage_gap
