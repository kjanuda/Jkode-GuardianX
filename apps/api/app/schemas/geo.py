
from pydantic import BaseModel


class GeoContextResult(BaseModel):
    device_id: str
    telemetry_id: int

    cell_id: str
    sector_code: str
    tower_code: str

    device_latitude: float
    device_longitude: float

    tower_latitude: float
    tower_longitude: float

    distance_m: float
    distance_km: float

    bearing_deg: float | None

    sector_azimuth_deg: float | None
    azimuth_difference_deg: float | None

    sector_alignment: str


class ElevationProfilePoint(BaseModel):
    latitude: float
    longitude: float
    elevation_m: float


class ElevationContextResult(BaseModel):
    device_id: str
    tower_code: str

    distance_km: float

    tower_elevation_m: float
    device_elevation_m: float

    elevation_difference_m: float

    path_min_elevation_m: float
    path_max_elevation_m: float
    path_mean_elevation_m: float

    terrain_relief_m: float

    endpoint_slope_percent: float

    sample_count: int

    profile: list[ElevationProfilePoint]

    source: str
    resolution_m: int

