from pydantic import BaseModel


class PropagationProfilePoint(BaseModel):
    latitude: float
    longitude: float

    terrain_elevation_m: float
    los_height_m: float

    terrain_clearance_m: float

    fresnel_radius_m: float
    fresnel_60_clearance_m: float

    obstructed: bool
    fresnel_obstructed: bool


class PropagationResult(BaseModel):
    device_id: str

    cell_id: str
    tower_code: str

    frequency_mhz: float
    distance_km: float

    tower_ground_elevation_m: float
    tower_antenna_height_m: float
    tower_radio_height_m: float

    device_ground_elevation_m: float
    device_antenna_height_m: float
    device_radio_height_m: float

    los_status: str

    terrain_obstructed: bool
    fresnel_60_obstructed: bool

    obstructed_points: int
    fresnel_obstructed_points: int

    minimum_terrain_clearance_m: float
    minimum_fresnel_60_clearance_m: float

    obstruction_score: float
    propagation_risk: str

    sample_count: int

    profile: list[PropagationProfilePoint]