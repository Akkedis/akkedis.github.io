# Trail mapper

Turns a written route description (a hiking booklet) into an accurate, bilingual
trail map page. It was built for the Citrusdal → Tulbagh trail
(`citrusdal-tulbagh.html` in the site root) and is meant to be reused.

## Idea

Neither map source is complete, so the route is found on **both at once**:

| Source | What it gives |
|---|---|
| **NGI 1:50 000 topo scans** (`htonl.dev.openstreetmap.org/ngi-tiles`, z15) | farm names, building symbols, dashed tracks, fences, dam walls, roads |
| **OpenStreetMap export** (from overpass-turbo, GeoJSON) | tracks, paths and roads, often newer than the 2010 NGI sheets |
| **Esri satellite imagery** | confirms buildings, dam walls, track positions |
| **SRTM 30 m** (OpenTopoData) | elevation profile, climb and descent |

`router.py` builds an 8 m cost grid along the route corridor:

* OSM way → cost 0.85 (preferred where both maps agree)
* NGI line (black or red pixels: tracks, roads, fences, dam walls) → cost 1
* open country → cost 10; open water (blue fill) → cost 300
* removed from the NGI layer: sheet edges and grid lines (long straight black runs), and black text
  and building squares (compact round blobs, as opposed to elongated track dashes)

It routes A* between consecutive waypoints, removes out-and-back spurs, and labels every
piece `o` (OSM), `n` (NGI only) or `h` (open country, drawn dashed on the page).

## NGI 1:50 000 legend (what the router relies on)

| Symbol | Meaning |
|---|---|
| black dashed line | Track and Hiking Trail (Dowwe Pad en Voetslaanpad) |
| double thin black line | Other Road |
| thin solid black line / thick | Fence / Wall |
| black line with dots | **Power Line**, not a track |
| blue fill with thick black bar | Perennial Water with dam wall |
| small solid black squares | Buildings: put farm and stop markers here, **not on the label** |
| grey large letters + grey outlines | original farm names and boundaries (ignored) |
| green dots in a box | Orchard or Vineyard |

## Workflow for a new trail

1. **Booklet → waypoints.** For each day write `segs.py`: a list of segments per day,
   `("r"|"n"|"l"|"t", [(lat, lon), ...])`. Put a waypoint at each booklet instruction
   (junction, gate, dam wall, farmstead). Find places with Nominatim, the NGI scans
   (`ngi.py mosaic(...)` then `px2ll(...)` to turn map pixels into coordinates) and listings online.
2. **OSM export.** On overpass-turbo, export the area's `highway=*`, `place`, `tourism`, `natural=water` and `power`
   features as GeoJSON and save it as `osm-export.geojson` (or set `OSM_EXPORT`).
3. **Route:** `python3 run_router.py` writes `tracks_new.json` → copy it to `tracks.json`.
4. **Check** (all automatic):
   * `spurs.py`: out-and-back detours
   * `wetngi.py tracks.json`: stretches over NGI water (only dam walls should remain)
   * open-country (`h`) pieces longer than 100 m, printed by `run_router.py`
   * `overlay.py lat lon 15 1 out.png DAY` (NGI) and `sat.py mosaic(..., day=DAY)` (satellite) to look at any flagged spot
   * `buildings.py farmstead(lat, lon)`: moves farm and stop markers onto the building symbols
5. **Elevation and landmarks:** `elev.py` then `data.py` (landmarks: `(day, EN name, AF name, lat, lon, source)`).
6. **Page:** fill `template.html` (`__DATA__`) and `af.js` (`__AF__`); Afrikaans is the default, `?lang=en` gives English.

`trails/citrusdal-tulbagh/` holds the inputs used for the first trail.

Network notes: Overpass API was unreachable from the cloud environment, so the OSM data came from
an overpass-turbo export made in a browser. Nominatim, routing.openstreetmap.de, OpenTopoData, the NGI tiles and Esri imagery were reachable.
