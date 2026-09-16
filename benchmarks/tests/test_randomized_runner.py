from decimal import Decimal

from benchmarks.randomized.model import RandomCase, SerializedRandomValue
from benchmarks.randomized.oracle import OracleRunner, oracle_invocation_key
from benchmarks.randomized.run import build_parser, execute_case


def make_case(
    kind="cardinal",
    value=1,
    *,
    locale="en",
    oracle_locale=None,
    currency=None,
    options=None,
    call_variant=None,
    transport="native",
    case_id="probe",
    index=0,
    surface="",
):
    return RandomCase(
        schema_version=3,
        generator_version=3,
        seed=1,
        index=index,
        case_id=case_id,
        locale=locale,
        kind=kind,
        surface=surface,
        value=SerializedRandomValue.from_python(value),
        currency=currency,
        oracle_locale=oracle_locale or locale,
        options=options or {},
        call_variant=call_variant,
        transport=transport,
    )


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


def test_randomized_cli_supports_runtime_diagnostics_flags():
    args = build_parser().parse_args(["--profile-runtime", "--progress"])
    assert args.profile_runtime
    assert args.progress
    plain = build_parser().parse_args([])
    assert not plain.profile_runtime
    assert not plain.progress


def test_probe_plus_execution_runs_the_oracle_once():
    calls = []

    def fake(value, **kwargs):
        calls.append((value, kwargs))
        return "one"

    case = make_case()
    runner = OracleRunner(fake)
    assert runner.supports(case)
    result = execute_case(
        case, fake, target="compat", oracle_result=runner.execute(case)
    )
    assert result.status == "match"
    assert len(calls) == 1
    assert runner.stats.executions == 1
    assert runner.stats.accepted_cache_hits == 1


def test_execute_case_without_cached_result_runs_the_oracle():
    calls = []

    def fake(value, **kwargs):
        calls.append((value, kwargs))
        return "one"

    result = execute_case(make_case(), fake, target="compat")
    assert result.status == "match"
    assert len(calls) == 1


def test_rejected_results_are_cached_with_a_bound():
    calls = []

    def failing(value, **kwargs):
        calls.append(value)
        raise ValueError("unsupported")

    runner = OracleRunner(failing, rejected_cache_max=4)
    case = make_case()
    assert not runner.supports(case)
    assert not runner.supports(case)
    assert len(calls) == 1
    assert runner.stats.rejected_cache_hits == 1

    for value in range(10):
        runner.execute(make_case(value=value))
    assert len(calls) == 10
    assert len(runner.rejected) <= 4


def test_probe_and_accepted_cases_share_invocation_key():
    probe = make_case(case_id="probe", surface="", index=0)
    accepted = make_case(case_id="random-v3:20260910:000000", surface="1", index=0)
    assert oracle_invocation_key(probe) == oracle_invocation_key(accepted)


def test_cache_keys_do_not_collide_across_transports():
    native = make_case(transport="native")
    string = make_case(transport="string")
    as_float = make_case(transport="float")
    keys = {oracle_invocation_key(case) for case in (native, string, as_float)}
    assert len(keys) == 3


def test_cache_keys_distinguish_call_variants():
    via_to = make_case(kind="ordinal")
    via_bool = make_case(kind="ordinal", call_variant="ordinal-bool")
    assert oracle_invocation_key(via_to) != oracle_invocation_key(via_bool)


def test_cache_keys_distinguish_currencies():
    usd = make_case(kind="currency", value=Decimal("1.01"), currency="USD")
    eur = make_case(kind="currency", value=Decimal("1.01"), currency="EUR")
    assert oracle_invocation_key(usd) != oracle_invocation_key(eur)


def test_cache_keys_distinguish_options():
    masculine = make_case(options={"gender": "masculine"})
    feminine = make_case(options={"gender": "feminine"})
    assert oracle_invocation_key(masculine) != oracle_invocation_key(feminine)


def test_cache_keys_distinguish_oracle_locales():
    english = make_case(oracle_locale="en")
    german = make_case(oracle_locale="de")
    assert oracle_invocation_key(english) != oracle_invocation_key(german)


def test_cache_keys_preserve_decimal_spelling():
    one_point_zero = make_case(kind="decimal", value=Decimal("1.0"))
    one_point_zero_zero = make_case(kind="decimal", value=Decimal("1.00"))
    assert oracle_invocation_key(one_point_zero) != oracle_invocation_key(
        one_point_zero_zero
    )
