"""
FastAPI entry point for the Vision parcel API.  This module proxies search
queries to the NSW and QLD ArcGIS services, generates KML and Shapefile
downloads and serves the compiled React front‑end when deployed.  The API
supports CORS and expects the front‑end origin in the `VISION_FRONTEND`
environment variable.

Compared to the original implementation, the `search` endpoint here lives at
`/search` instead of `/api/search`, and accepts either an `inputs` list or a
legacy `query` list in its request body for backwards compatibility.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError

from .constants import NSW_PARCEL_URL, QLD_PARCEL_URL
from .utils import parse_user_input
from ..kml_utils import generate_kml, generate_shapefile

# Determine absolute paths so the app works regardless of the working directory
BASE_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = BASE_DIR / "frontend" / "dist"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Vision Parcel API")

# ── CORS ──────────────────────────────────────────────────────────────
frontend_origin = os.getenv("VISION_FRONTEND") or "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── static SPA ────────────────────────────────────────────────────────
# When the front‑end is built via `npm run build`, Vite outputs files
# into `frontend/dist`.  We serve those files here.  Static assets under
# `/static` can be used for e.g. custom icons.
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="spa")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/ping")
async def ping() -> dict[str, bool]:
    """Health check endpoint."""
    return {"pong": True}


# ── models ────────────────────────────────────────────────────────────
class SearchBody(BaseModel):
    """Request body for the search endpoint."""

    inputs: List[str] | None = Field(
        None, description="List of lot/plan strings e.g. '3RP123456' or '43/DP12345'",
    )
    query: List[str] | None = Field(
        None, description="Alias for `inputs` for backwards compatibility",
    )

    def clean_inputs(self) -> List[str]:
        if self.inputs is not None:
            return self.inputs
        if self.query is not None:
            return self.query
        raise ValidationError("No inputs provided", SearchBody)


class DownloadBody(BaseModel):
    """Request body for download endpoints.

    In addition to the feature list and optional folder/file names, clients may
    supply styling parameters for KML downloads.  These match the names used
    in the front‑end QueryPanel.  All fields are optional and will fall back
    to sensible defaults if omitted.
    """

    features: List[dict] = Field(
        ..., description="List of GeoJSON feature dicts. Each should include a `geometry` and `properties` field."
    )
    folderName: str | None = Field(
        None, description="Folder name used in KML documents and as the base name for shapefile components"
    )
    fileName: str | None = Field(
        None, description="Desired filename for the returned archive. Extensions `.kml` or `.zip` are appended as appropriate."
    )
    style: dict | None = Field(
        None,
        description="Optional styling directives for KML. Keys may include `fill` (hex string), `outline` (hex string), `opacity` (0–1 float) and `weight` (outline width).",
    )


# ── internal helpers ─────────────────────────────────────────────────
async def _fetch_geojson(url: str, params: dict) -> list[dict]:
    """Internal helper to perform a GET request and return features from GeoJSON."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        return data.get("features", []) or []


def _region_from_features(flist: list[dict]) -> str:
    """Determine the region based on the presence of certain properties."""
    return "QLD" if any("lot" in f.get("properties", {}) for f in flist) else "NSW"


# ── routes ───────────────────────────────────────────────────────────
@app.post("/search")
async def search(body: SearchBody):
    """
    Search parcels by lot/plan strings.

    The request body may include either an `inputs` list or a legacy `query`
    list.  Each string is parsed with `parse_user_input` to determine the
    region, lot, section and plan.  Unknown or malformed inputs are skipped.

    Returns a dict with a list of features and a parallel list of regions.
    """
    features: list[dict] = []
    regions: list[str] = []
    for raw in body.clean_inputs():
        region, lot, section, plan = parse_user_input(raw)
        if not region:
            continue
        feats = await _search_one(region, lot, section, plan)
        features.extend(feats)
        regions.extend([region] * len(feats))
    return {"features": features, "regions": regions}


async def _search_one(region: str, lot: str, section: str, plan: str) -> list[dict]:
    """Search a single lot/plan combination for a given region."""
    if region == "NSW":
        # NSW lot numbers may include a section.  We strip non‑digits from the
        # plan label for the service query.
        plannum = int(re.sub(r"[^\d]", "", plan))
        where = [
            f"lotnumber='{lot}'",
            f"plannumber={plannum}",
            "(sectionnumber IS NULL OR sectionnumber='')" if not section else f"sectionnumber='{section}'",
        ]
        return await _fetch_geojson(
            NSW_PARCEL_URL,
            {"where": " AND ".join(where), "outFields": "*", "outSR": "4326", "f": "geoJSON"},
        )
    # QLD uses `lot` and `plan` fields directly
    return await _fetch_geojson(
        QLD_PARCEL_URL,
        {"where": f"lot='{lot}' AND plan='{plan}'", "outFields": "*", "outSR": "4326", "f": "geoJSON"},
    )


@app.post("/download/kml")
async def download_kml(body: DownloadBody):
    """Create a KML file for a list of features and return it as a response."""
    if not body.features:
        raise HTTPException(400, "No features provided")
    region = _region_from_features(body.features)
    # Pull styling overrides from the request body if provided.  The
    # generate_kml helper accepts fill/outline colours, opacity and
    # outline weight.  When keys are missing the defaults from
    # generate_kml will be used.
    style = body.style or {}
    kml = generate_kml(
        body.features,
        region,
        fill_hex=style.get("fill", "#FF0000"),
        fill_opacity=float(style.get("opacity", 0.5)),
        outline_hex=style.get("outline", "#000000"),
        outline_weight=int(style.get("weight", 2)),
        folder_name=body.folderName or "Parcels",
    )
    # Derive a safe filename.  If the user did not supply one, fall back
    # to `parcels.kml`.  Remove any path separators to prevent directory
    # traversal issues.
    fname = (body.fileName or "parcels.kml").replace("/", "_")
    if not fname.lower().endswith(".kml"):
        fname += ".kml"
    return Response(
        content=kml,
        media_type="application/vnd.google-earth.kml+xml",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.post("/download/shp")
async def download_shp(body: DownloadBody):
    """Create a zipped Shapefile for a list of features and return it as a response."""
    if not body.features:
        raise HTTPException(400, "No features provided")
    region = _region_from_features(body.features)
    # For shapefiles, the folder/base name influences the internal
    # component names (e.g. .shp, .dbf files).  Use the folderName if
    # provided, otherwise default to "parcels".  Clean any path
    # separators to avoid writing files outside the temp directory.
    base_name = (body.folderName or "parcels").replace("/", "_")
    shp_zip = generate_shapefile(body.features, region, base_name=base_name)
    # Determine the output filename from fileName or base_name.  When
    # absent, default to base_name + ".zip".  Append .zip if missing.
    out_name = (body.fileName or f"{base_name}.zip").replace("/", "_")
    if not out_name.lower().endswith(".zip"):
        out_name += ".zip"
    return Response(
        content=shp_zip,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'},
    )
