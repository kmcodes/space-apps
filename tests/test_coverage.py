import pytest

from engine.coverage import MAX_SNAP_KM, Tile, locate

AKOLA = (20.582591, 77.051776)
WASHIM = (20.208788, 77.119615)


def test_a_preset_point_is_served_with_zero_distance():
    r = locate(*AKOLA)
    assert r.served is True
    assert r.nearest == "akola"
    assert r.distance_km == pytest.approx(0, abs=0.1)


def test_point_in_tile_and_near_a_preset_snaps_to_it_and_reports_distance():
    r = locate(WASHIM[0] + 0.15, WASHIM[1])  # about 17 km north of Washim
    assert r.served is True
    assert r.nearest == "washim"
    assert 14 < r.distance_km < 20


def test_point_in_tile_but_far_from_every_preset_is_not_served_yet():
    r = locate(21.7, 76.1)
    assert r.served is False
    assert "Akola" in r.reason and "Washim" in r.reason and "Buldhana" in r.reason


def test_point_outside_the_tile_is_not_served():
    r = locate(19.07, 72.88)  # Mumbai
    assert r.served is False
    assert "outside" in r.reason


def test_the_snap_limit_can_be_changed():
    assert locate(21.0, 76.7, max_snap_km=200).served is True
    assert locate(21.0, 76.7, max_snap_km=5).served is False


def test_adding_a_tile_extends_coverage_without_code_changes():
    far = Tile("test-tile", west=70.0, south=15.0, east=75.0, north=25.0, resolution_m=250)
    assert locate(19.07, 72.88).served is False
    r = locate(19.07, 72.88, tiles=[far], max_snap_km=10000)
    assert r.served is True


def test_layers_state_which_level_each_one_has():
    r = locate(*AKOLA)
    assert r.layers["soil"]["resolution_m"] == 250
    assert r.layers["weather"]["scope"] == "area"
    assert r.layers["prices"]["scope"] == "district"


def test_default_snap_limit_is_fifty_km():
    assert MAX_SNAP_KM == 50
