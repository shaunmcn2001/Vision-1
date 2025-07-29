"""
Centralised constants for external data sources.

The NSW and QLD parcel services are ArcGIS REST endpoints.  They return
GeoJSON when the `f=geoJSON` parameter is supplied.  Note that these URLs
could change in the future – keep them in a single place to make updates
easier.
"""

# NSW Lot layer (ID 9) – returns GeoJSON when f=geoJSON
NSW_PARCEL_URL: str = (
    "https://maps.six.nsw.gov.au/arcgis/rest/services/public/"
    "NSW_Cadastre/MapServer/9/query"
)

# QLD Land Parcel framework layer (ID 4)
QLD_PARCEL_URL: str = (
    "https://spatial-gis.information.qld.gov.au/arcgis/rest/services/"
    "PlanningCadastre/LandParcelPropertyFramework/MapServer/4/query"
)
