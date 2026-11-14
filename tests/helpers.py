from engine.crops import Crop


def make_crop(**kw):
    base = dict(
        name="x", role="main", season="kharif", sow_start_doy=166, sow_end_doy=196,
        duration_min=90.0, duration_max=110.0, water_need_mm_min=450.0, water_need_mm_max=650.0,
        water_need="medium", legume=True, n_fixation="medium", ground_cover="medium", residue="low",
        fodder_value="low", equipment="basic", unverified=frozenset(),
    )
    base.update(kw)
    return Crop(**base)
