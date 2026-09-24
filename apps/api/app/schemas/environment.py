
from pydantic import BaseModel


class EnvironmentContextResult(BaseModel):
    device_id: str

    latitude: float
    longitude: float

    radius_m: int
    area_km2: float

    building_count: int
    building_density_per_km2: float
    built_environment_level: str

    vegetation_feature_count: int
    vegetation_context_level: str

    forest_feature_count: int
    wood_feature_count: int
    scrub_feature_count: int
    grass_feature_count: int
    orchard_feature_count: int

    cache_hit: bool = False

    source: str

    note: str


class LandCoverClassStat(BaseModel):
    code: int
    class_name: str
    pixel_count: int
    percentage: float


class WorldCoverContextResult(BaseModel):
    device_id: str

    latitude: float
    longitude: float

    radius_m: int

    center_class_code: int
    center_class_name: str

    dominant_class: str
    dominant_percentage: float

    tree_cover_pct: float
    shrubland_pct: float
    grassland_pct: float
    cropland_pct: float
    built_up_pct: float
    water_pct: float
    wetland_pct: float

    class_distribution: list[LandCoverClassStat]

    tile_id: str
    year: int
    resolution_m: int
    source: str


class EnvironmentalRiskComponents(BaseModel):
    osm_building_risk: float
    satellite_built_up_risk: float

    building_vulnerability: float
    vegetation_vulnerability: float

    clutter_vulnerability: float
    terrain_vulnerability: float


class EnvironmentalVulnerabilityResult(BaseModel):
    device_id: str
    radius_m: int

    environment_type: str

    environmental_vulnerability_score: float
    environmental_vulnerability_level: str

    components: EnvironmentalRiskComponents

    built_up_pct: float
    tree_cover_pct: float
    shrubland_pct: float
    cropland_pct: float

    building_density_per_km2: float
    vegetation_context_level: str

    los_status: str
    propagation_risk: str

    evidence: list[str]
