from benchmarks.validation.num2words2 import compare_overlap, load_config


def test_num2words2_is_a_separate_pinned_secondary_suite():
    config = load_config()
    assert config["oracle"]["commit"] == "d6d47ec55728bb724eff8277ea683ab4915618bc"
    assert config["oracle"]["legacy_oracle"].startswith("savoirfairelinux/num2words@")
    assert "fraction" in config["suites"]["extended"]["forms"]


def test_secondary_overlap_counts_do_not_change_legacy_metrics():
    cases = [(1, {"lang": "en", "to": "cardinal"})]
    assert compare_overlap(cases, lambda value, **kwargs: "one", lambda value, **kwargs: "one") == {"match": 1, "mismatch": 0}
