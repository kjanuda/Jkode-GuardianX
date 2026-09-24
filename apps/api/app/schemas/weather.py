from pydantic import BaseModel


class WeatherContextResult(BaseModel):
    device_id: str

    latitude: float
    longitude: float

    weather_time: str

    temperature_c: float
    relative_humidity_pct: float

    precipitation_mm: float
    rain_mm: float

    cloud_cover_pct: float

    surface_pressure_hpa: float

    wind_speed_kmh: float
    wind_direction_deg: float
    wind_gusts_kmh: float

    weather_code: int

    weather_context_score: float
    weather_context_level: str

    factors: list[str]

    source: str