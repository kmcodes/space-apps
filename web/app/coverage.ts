// Is a phone's location inside the area the engine can serve? The same rule as engine/coverage.py, so the call can
// say so BEFORE showing a map and asking eight questions, instead of ending in a dead end on the results screen.
// tests/test_web_coverage.py runs this file and the engine on the same points and requires the same answer.
// If the engine's tiles, preset points or limit change, change them here too (the test will fail until you do).

/** The farm points the weather and satellite data stand in for (data/points.csv). */
export const PRESETS: Record<string, { lat: number; lon: number }> = {
  akola: { lat: 20.582591, lon: 77.051776 },
  buldhana: { lat: 20.471969, lon: 76.249219 },
  washim: { lat: 20.208788, lon: 77.119615 },
};

/** The soil data tile (engine/coverage.py TILES). */
const TILE = { west: 76.058, south: 19.75, east: 78.058, north: 21.75 };

/** A point farther than this from every preset is not served (engine MAX_SNAP_KM). */
const MAX_SNAP_KM = 50;

// Flat-earth distance, as in the engine: good to a fraction of a percent over tens of kilometres.
function km(aLat: number, aLon: number, bLat: number, bLon: number): number {
  const mid = (((aLat + bLat) / 2) * Math.PI) / 180;
  return Math.hypot((aLon - bLon) * 111.32 * Math.cos(mid), (aLat - bLat) * 110.57);
}

export function isServed(lat: number, lon: number): boolean {
  const inside = TILE.south <= lat && lat <= TILE.north && TILE.west <= lon && lon <= TILE.east;
  if (!inside) return false;
  const nearest = Math.min(...Object.values(PRESETS).map((p) => km(lat, lon, p.lat, p.lon)));
  return nearest <= MAX_SNAP_KM;
}
