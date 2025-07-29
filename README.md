# Vision Parcel Viewer – Kepler Edition

This project is a **beta re‑implementation** of the parcel viewer you provided.  It
combines a small FastAPI back‑end with a modern React + Vite front‑end.  The
front‑end uses **Kepler.gl** instead of Leaflet/Maplibre and exposes a custom
query panel through Kepler’s `injectComponents` API.  The app lets you search
for parcels in **Queensland (QLD)** and **New South Wales (NSW)** by lot/plan
codes, renders the returned boundaries on an interactive map, and supports
client‑side KML and Shapefile exports.  Folder names, file names and visual
styles (fill colour, outline colour, opacity and stroke weight) are all
customisable from the UI.

## Structure

* `app/` – a FastAPI back‑end that proxies requests to the NSW and QLD parcel
  services.  It exposes the following endpoints:
  * `POST /search` – accepts `{inputs: ["LOTPLAN", "LOT/PLAN", ...]}` and
    returns a GeoJSON `FeatureCollection` for each valid query.
  * `POST /download/kml` and `POST /download/shp` – generate KML or Shapefile
    archives for an array of features.  The request body accepts optional
    `folderName` and `fileName` properties which are used in the output files.
    For KML exports you may also supply a `style` object (e.g. `{ fill:
    '#00ff00', outline: '#0000ff', opacity: 0.4, weight: 3 }`) to set the
    polygon fill colour, outline colour, transparency and stroke width.  For
    Shapefile exports the `folderName` controls the base name of the
    component files (e.g. `myparcels.shp`, `myparcels.dbf` etc.).
  * `GET /` – serves the built React application from `frontend/dist` when
    deployed.

* `frontend/` – a Vite project written in React.  It uses
  `@kepler.gl/components` and `@kepler.gl/react` to embed the Kepler map.  A
  custom query panel is injected next to the standard *Layers* and *Filters*
  tabs via `injectComponents`.  The panel allows bulk entry of lot/plan codes,
  performs searches against the back‑end and adds results as a layer on the
  map.  It also exposes a download section to export the selected parcels as
  KML or Shapefile.

This repository is ready to be deployed on [Render](https://render.com/): push
to GitHub and create a new web service pointing at the repo.  The included
`Procfile` will run `uvicorn app.main:app` on the provided port.

## Local Development

1. Install the Python dependencies and start the back‑end:

   ```bash
   pip install -r requirements.txt
   uvicorn vision69.app.main:app --reload
   ```

2. Install the front‑end dependencies and start Vite in development mode.  The
   React app expects an environment variable named `VITE_API_BASE` that
   points to the back‑end; by default it falls back to `http://localhost:8000`:

   ```bash
   npm --prefix vision69/frontend install
   VITE_API_BASE=http://localhost:8000 npm --prefix vision69/frontend run dev
   ```

3. Navigate to `http://localhost:5173` in your browser.  You should see the
   Kepler map with a *Search* tab alongside the native Layers and Filters
   panels.  Paste one or more lot/plan identifiers (e.g. `3RP123456` or
   `43/DP12345`) into the search box and click **Search**.  Matching parcels
   will appear on the map and are listed in the results table.  Selecting
   parcels and clicking **Download KML** or **Download SHP** will trigger a
   download of the specified file types.

## Testing

Basic unit tests live in `tests/`.  Run them with `pytest`:

```bash
pytest -q
```

## Notes

* This beta implementation uses Kepler.gl’s programmatic API.  When injecting
  components via `injectComponents`, you must provide a Redux store that mounts
  the `keplerGl` reducer and applies the `react-palm` task middleware.  See
  `frontend/src/store.js` for the minimal store configuration used in this
  project.
* The back‑end proxies requests to two external ArcGIS services.  If the
  external services change or become unavailable, searches will fail.
* The Shapefile export relies on the [pyshp](https://pypi.org/project/pyshp/)
  package; ensure it is listed in `requirements.txt` when deploying.
