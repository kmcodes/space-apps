"""Which GPS points we can serve, and at what level for each data layer.

Data-driven: the TILES registry lists every covered tile; adding a tile (and its data) later means adding
one entry, no code change. A point is served if it is inside a tile AND within MAX_SNAP_KM of a preset
point, because weather and NDVI exist only at the presets for now (soil is tile-wide, 250 m).
"""
import csv
import math
from dataclasses import dataclass, field
from pathlib import Path

MAX_SNAP_KM = 50
POINTS_CSV = Path(__file__).resolve().parent.parent / "data/points.csv"


@dataclass(frozen=True)
class Tile:
    name: str
    west: float
    south: float
    east: float
    north: float
    resolution_m: int

    def contains(self, lat, lon):
        return self.south <= lat <= self.north and self.west <= lon <= self.east


# SoilGrids download (manual, 14 Nov 2026): 208 km x 221 km, ~250 m pixels, covers all three presets.
TILES = [Tile("soilgrids-vidarbha-1", west=76.058, south=19.75, east=78.058, north=21.75, resolution_m=250)]


@dataclass
class Located:
    served: bool
    nearest: str | None
    distance_km: float
    reason: str
    layers: dict = field(default_factory=dict)


def presets(path=POINTS_CSV):
    with open(path) as f:
        return {r["name"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(f)}


def _km(a, b):
    mid = math.radians((a[0] + b[0]) / 2)
    return math.hypot((a[1] - b[1]) * 111.32 * math.cos(mid), (a[0] - b[0]) * 110.57)


def locate(lat, lon, tiles=None, max_snap_km=MAX_SNAP_KM):
    tiles = TILES if tiles is None else tiles
    pts = presets()
    nearest, dist = min(((n, _km((lat, lon), p)) for n, p in pts.items()), key=lambda x: x[1])
    tile = next((t for t in tiles if t.contains(lat, lon)), None)
    names = ", ".join(n.capitalize() for n in sorted(pts))
    if tile is None:
        return Located(False, nearest, dist, f"This spot is outside the areas we have data for yet ({names}).")
    if dist > max_snap_km:
        return Located(False, nearest, dist,
                       f"This spot is {dist:.0f} km from the nearest place we have built data for "
                       f"({names}); the limit is {max_snap_km:.0f} km.")
    layers = {
        "soil": {"scope": "your spot", "resolution_m": tile.resolution_m, "tile": tile.name},
        "weather": {"scope": "area", "snapped_to": nearest, "distance_km": round(dist, 1), "grid_km": "25-50"},
        "ndvi": {"scope": "area", "snapped_to": nearest, "distance_km": round(dist, 1)},
        "prices": {"scope": "district", "snapped_to": nearest},
    }
    return Located(True, nearest, dist, "served", layers)
