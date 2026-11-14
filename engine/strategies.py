"""The four rotation strategies, defined as data (not code).

kind: 'sequence' = crops one after the other in the same year
      'mixed'    = crops grown together (intercrop)
      'single'   = one crop
S3 has one default second crop; `variants` are alternatives shown on the card.
"""
from dataclasses import dataclass

EXISTING = {
    "soybean_fallow": ("sequence", ("soybean", "fallow")),
    "cotton": ("single", ("cotton",)),
    "soybean_chickpea": ("sequence", ("soybean", "chickpea")),
}


@dataclass(frozen=True)
class Strategy:
    id: str
    name: str
    kind: str
    crops: tuple
    variants: tuple = ()
    note: str = ""
    duplicate_of: str | None = None


def get_strategies(current_rotation):
    if current_rotation not in EXISTING:
        raise ValueError(f"unknown rotation: {current_rotation}")
    kind, crops = EXISTING[current_rotation]
    s1 = Strategy("S1", "Soybean then chickpea", "sequence", ("soybean", "chickpea"))
    s0 = Strategy("S0", "Your current rotation", kind, crops,
                  duplicate_of="S1" if crops == s1.crops else None)
    s2_note = "adds pigeon pea to your cotton" if crops == ("cotton",) else "cotton with pigeon pea grown between the rows"
    s2 = Strategy("S2", "Cotton with pigeon pea", "mixed", ("cotton", "pigeon_pea"), note=s2_note)
    s3 = Strategy("S3", "Soybean then sorghum (or a cover crop)", "sequence", ("soybean", "sorghum_rabi"),
                  variants=("sunn_hemp", "horse_gram"))
    return [s0, s1, s2, s3]
