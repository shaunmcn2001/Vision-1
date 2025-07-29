"""
Very small KML + Shapefile helpers (no third‑party deps except `pyshp`).

This module contains two primary functions used by the back‑end:

* `generate_kml` – convert a list of GeoJSON features into a KML string.
  Each parcel is exported as a Placemark with a simple HTML pop‑up table
  describing its properties.  Colours are specified in the ABGR format
  required by KML (using `_hex_to_kml_color`).

* `generate_shapefile` – convert a list of GeoJSON features into a zipped
  ESRI Shapefile.  The function uses the `pyshp` package to write SHP,
  SHX, DBF and PRJ files into a temporary directory and returns the
  contents of the zip file as bytes.

These helpers are deliberately light‑weight to avoid pulling in heavy
dependencies into the back‑end.  They can be extended to include
additional attributes or geometry types if needed.
"""

from __future__ import annotations

import html
import io
import os
import tempfile
import zipfile
from typing import List


# ── internal colour helper ────────────────────────────────────────────────
def _hex_to_kml_color(hex_color: str, opacity: float) -> str:
    """
    Convert a CSS hex colour + alpha to the ABGR format expected by KML.

    Args:
        hex_color: A string like "#RRGGBB" (with or without leading '#').
        opacity: A float between 0 and 1.

    Returns:
        An 8‑character string in the order AABBGGRR.
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        hex_color = "FFFFFF"
    r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
    alpha = int(opacity * 255)
    return f"{alpha:02x}{b}{g}{r}"


# ── public API – KML ──────────────────────────────────────────────────────
def generate_kml(
    features: List[dict],
    region: str,
    fill_hex: str = "#FF0000",
    fill_opacity: float = 0.5,
    outline_hex: str = "#000000",
    outline_weight: int = 2,
    folder_name: str = "Parcels",
) -> str:
    """
    Return a KML string with <Placemark> pop‑ups and a user‑defined folder name.

    Args:
        features: A list of GeoJSON feature dictionaries.
        region: "QLD" or "NSW" – used to pick which properties to display.
        fill_hex: Fill colour for polygons as a hex string.
        fill_opacity: Opacity for polygon fills (0–1).
        outline_hex: Outline colour as a hex string.
        outline_weight: Line width for polygon outlines.
        folder_name: Name of the folder in the KML document.

    Returns:
        A KML document as a string.
    """
    fill_kml = _hex_to_kml_color(fill_hex, fill_opacity)
    out_kml = _hex_to_kml_color(outline_hex, 1.0)

    out: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<kml xmlns='http://www.opengis.net/kml/2.2'>",
        f"  <Document><name>{html.escape(folder_name)}</name>",
        f"    <Style id=\"parcel\">",
        f"      <LineStyle><color>{out_kml}</color><width>{outline_weight}</width></LineStyle>",
        f"      <PolyStyle><color>{fill_kml}</color></PolyStyle>",
        f"    </Style>",
    ]

    for feat in features:
        p = feat.get("properties", {})
        if region == "QLD":
            lot, plan = p.get("lot"), p.get("plan")
            name = f"Lot {lot} Plan {plan}"
        else:
            lot = p.get("lotnumber")
            sec = p.get("sectionnumber") or ""
            plan = p.get("planlabel")
            name = f"Lot {lot} {'Section ' + sec + ' ' if sec else ''}{plan}"

        # simple HTML table for pop‑up
        desc_rows = "".join(
            f"<tr><th>{html.escape(str(k))}</th><td>{html.escape(str(v))}</td></tr>"
            for k, v in p.items()
            if v not in ("", None)
        )
        description = f"<![CDATA[<table>{desc_rows}</table>]]>"

        out.extend([
            "    <Placemark>",
            f"      <name>{html.escape(name)}</name>",
            "      <styleUrl>#parcel</styleUrl>",
            f"      <description>{description}</description>",
        ])

        geom = feat.get("geometry", {})
        polygons = (
            [geom.get("coordinates")] if geom.get("type") == "Polygon" else geom.get("coordinates", []) if geom.get("type") == "MultiPolygon" else []
        )

        if len(polygons) > 1:
            out.append("      <MultiGeometry>")

        for poly in polygons:
            out.append("        <Polygon>")
            out.append("          <outerBoundaryIs><LinearRing>")
            _write_ring(out, poly[0])
            out.append("          </LinearRing></outerBoundaryIs>")
            for hole in poly[1:]:
                out.append("          <innerBoundaryIs><LinearRing>")
                _write_ring(out, hole)
                out.append("          </LinearRing></innerBoundaryIs>")
            out.append("        </Polygon>")

        if len(polygons) > 1:
            out.append("      </MultiGeometry>")

        out.append("    </Placemark>")

    out.append("  </Document></kml>")
    return "\n".join(out)


def _write_ring(buf: list[str], ring: list):
    """Write a coordinate ring into the KML buffer, closing it if necessary."""
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    buf.append("            <coordinates>")
    buf.extend(f"              {x},{y},0" for x, y in ring)
    buf.append("            </coordinates>")


# ── public API – Shapefile (unchanged) ────────────────────────────────────
def generate_shapefile(features: List[dict], region: str, base_name: str = "parcels") -> bytes:
    """Return a `.zip` containing SHP/SHX/DBF/PRJ files for the parcels.

    Args:
        features: List of GeoJSON feature dictionaries to encode.
        region: "QLD" or "NSW"; used to select which properties populate
            the output attribute table.
        base_name: Base name for the shapefile components.  The returned
            zip archive will contain files named ``{base_name}.shp``,
            ``{base_name}.shx``, ``{base_name}.dbf`` and ``{base_name}.prj``.

    Returns:
        Bytes of a zip archive containing the shapefile components.
    """
    import shapefile  # pyshp

    # Use a temporary directory because shapefile writes multiple files
    with tempfile.TemporaryDirectory() as tmp:
        # Sanitize the base name to avoid path separators and spaces
        safe_base = base_name.replace("/", "_").replace(" ", "_") or "parcels"
        base_path = os.path.join(tmp, safe_base)
        w = shapefile.Writer(base_path)
        w.field("LOT", "C", size=10)
        w.field("SEC", "C", size=10)
        w.field("PLAN", "C", size=15)
        w.autoBalance = 1

        for feat in features:
            p = feat.get("properties", {})
            if region == "QLD":
                lot, sec, plan = p.get("lot", ""), "", p.get("plan", "")
            else:
                lot = p.get("lotnumber", "")
                sec = p.get("sectionnumber", "")
                plan = p.get("planlabel", "")
            w.record(lot, sec, plan)

            geom = feat.get("geometry", {})
            # Flatten MultiPolygon geometry into individual rings.  For a single
            # Polygon, ``coordinates`` is a list of rings.  For a MultiPolygon,
            # ``coordinates`` is a list of polygons, each of which is a list
            # of rings.  Flatten accordingly.  Skip unsupported types.
            parts = (
                geom.get("coordinates")
                if geom.get("type") == "Polygon"
                else [ring for poly in geom.get("coordinates", []) for ring in poly]
                if geom.get("type") == "MultiPolygon"
                else []
            )
            if parts:
                w.poly(parts)

        w.close()

        # Write WGS84 projection file
        with open(base_path + ".prj", "w") as f:
            f.write(
                'GEOGCS["WGS 84",DATUM["WGS_1984",'
                'SPHEROID["WGS 84",6378137,298.257223563]],'
                'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'
            )

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for ext in (".shp", ".shx", ".dbf", ".prj"):
                zf.write(base_path + ext, f"{safe_base}{ext}")
        return buf.getvalue()
