import pytest

from engine.strategies import get_strategies


def by_id(strategies):
    return {s.id: s for s in strategies}


def test_always_returns_four_strategies():
    assert [s.id for s in get_strategies("soybean_fallow")] == ["S0", "S1", "S2", "S3"]


def test_default_existing_rotation_is_soybean_then_fallow():
    s0 = by_id(get_strategies("soybean_fallow"))["S0"]
    assert s0.crops == ("soybean", "fallow")
    assert s0.kind == "sequence"


def test_s1_is_soybean_then_chickpea_sequence():
    s1 = by_id(get_strategies("soybean_fallow"))["S1"]
    assert (s1.kind, s1.crops) == ("sequence", ("soybean", "chickpea"))


def test_s2_is_cotton_plus_pigeon_pea_mixed():
    s2 = by_id(get_strategies("soybean_fallow"))["S2"]
    assert (s2.kind, s2.crops) == ("mixed", ("cotton", "pigeon_pea"))


def test_s3_has_one_default_crop_and_two_variants():
    s3 = by_id(get_strategies("soybean_fallow"))["S3"]
    assert s3.crops == ("soybean", "sorghum_rabi")
    assert s3.variants == ("sunn_hemp", "horse_gram")


def test_cotton_baseline_is_cotton_alone_and_s2_adds_pigeon_pea():
    s = by_id(get_strategies("cotton"))
    assert s["S0"].crops == ("cotton",)
    assert s["S0"].kind == "single"
    assert "adds pigeon pea" in s["S2"].note


def test_existing_soybean_chickpea_is_flagged_duplicate_of_s1():
    s = by_id(get_strategies("soybean_chickpea"))
    assert s["S0"].crops == s["S1"].crops
    assert s["S0"].duplicate_of == "S1"


def test_other_rotations_are_not_flagged_duplicate():
    assert by_id(get_strategies("soybean_fallow"))["S0"].duplicate_of is None


def test_unknown_rotation_is_rejected():
    with pytest.raises(ValueError):
        get_strategies("banana")
