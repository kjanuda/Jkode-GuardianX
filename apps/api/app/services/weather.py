import requests

from app.core.config import settings


class WeatherServiceError(Exception):
    pass


def clamp(
    value: float,
    minimum: float = 0,
    maximum: float = 100,
) -> float:
    return max(
        minimum,
        min(value, maximum),
    )


def score_precipitation(
    precipitation_mm: float,
) -> float:
    if precipitation_mm <= 0:
        return 0

    if precipitation_mm < 1:
        return 10

    if precipitation_mm < 5:
        return 25

    if precipitation_mm < 10:
        return 40

    return 60


def score_wind(
    wind_speed_kmh: float,
    wind_gusts_kmh: float,
) -> float:
    peak_wind = max(
        wind_speed_kmh,
        wind_gusts_kmh,
    )

    if peak_wind < 20:
        return 0

    if peak_wind < 40:
        return 10

    if peak_wind < 60:
        return 20

    return 30


def score_humidity(
    relative_humidity_pct: float,
) -> float:
    if relative_humidity_pct < 70:
        return 0

    if relative_humidity_pct < 85:
        return 5

    return 10


def classify_weather_context(
    score: float,
) -> str:
    if score < 10:
        return "LOW"

    if score < 25:
        return "MODERATE"

    return "ELEVATED"


def calculate_weather_context(
    current: dict,
) -> dict:
    precipitation = float(
        current.get(
            "precipitation",
            0,
        )
        or 0
    )

    humidity = float(
        current.get(
            "relative_humidity_2m",
            0,
        )
        or 0
    )

    wind_speed = float(
        current.get(
            "wind_speed_10m",
            0,
        )
        or 0
    )

    wind_gusts = float(
        current.get(
            "wind_gusts_10m",
            0,
        )
        or 0
    )

    precipitation_score = (
        score_precipitation(
            precipitation
        )
    )

    wind_score = score_wind(
        wind_speed_kmh=wind_speed,
        wind_gusts_kmh=wind_gusts,
    )

    humidity_score = (
        score_humidity(
            humidity
        )
    )

    # Weather is deliberately a supporting
    # context signal, not a dominant RF risk.
    context_score = (
        precipitation_score * 0.60
        + wind_score * 0.25
        + humidity_score * 0.15
    )

    context_score = round(
        clamp(
            context_score
        ),
        2,
    )

    factors = []

    if precipitation > 0:
        factors.append(
            f"Precipitation present: "
            f"{precipitation:.2f} mm"
        )

    if humidity >= 85:
        factors.append(
            f"High relative humidity: "
            f"{humidity:.1f}%"
        )

    if wind_gusts >= 40:
        factors.append(
            f"Strong wind gusts: "
            f"{wind_gusts:.1f} km/h"
        )

    if not factors:
        factors.append(
            "No strong weather stress "
            "indicator detected"
        )

    return {
        "weather_context_score":
            context_score,

        "weather_context_level":
            classify_weather_context(
                context_score
            ),

        "factors":
            factors,
    }


def fetch_current_weather(
    latitude: float,
    longitude: float,
) -> dict:
    current_variables = ",".join(
        [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "weather_code",
            "cloud_cover",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
        ]
    )

    try:
        response = requests.get(
            settings.weather_api_url,
            params={
                "latitude":
                    latitude,

                "longitude":
                    longitude,

                "current":
                    current_variables,

                "timezone":
                    "auto",
            },
            timeout=15,
        )

        response.raise_for_status()

        payload = response.json()

    except (
        requests.RequestException,
        ValueError,
    ) as exc:
        raise WeatherServiceError(
            "Could not retrieve weather data"
        ) from exc

    current = payload.get(
        "current"
    )

    if not isinstance(
        current,
        dict,
    ):
        raise WeatherServiceError(
            "Weather API returned "
            "an invalid response"
        )

    context = (
        calculate_weather_context(
            current
        )
    )

    return {
        "weather_time":
            current.get(
                "time",
                "UNKNOWN",
            ),

        "temperature_c":
            float(
                current.get(
                    "temperature_2m",
                    0,
                )
                or 0
            ),

        "relative_humidity_pct":
            float(
                current.get(
                    "relative_humidity_2m",
                    0,
                )
                or 0
            ),

        "precipitation_mm":
            float(
                current.get(
                    "precipitation",
                    0,
                )
                or 0
            ),

        "rain_mm":
            float(
                current.get(
                    "rain",
                    0,
                )
                or 0
            ),

        "cloud_cover_pct":
            float(
                current.get(
                    "cloud_cover",
                    0,
                )
                or 0
            ),

        "surface_pressure_hpa":
            float(
                current.get(
                    "surface_pressure",
                    0,
                )
                or 0
            ),

        "wind_speed_kmh":
            float(
                current.get(
                    "wind_speed_10m",
                    0,
                )
                or 0
            ),

        "wind_direction_deg":
            float(
                current.get(
                    "wind_direction_10m",
                    0,
                )
                or 0
            ),

        "wind_gusts_kmh":
            float(
                current.get(
                    "wind_gusts_10m",
                    0,
                )
                or 0
            ),

        "weather_code":
            int(
                current.get(
                    "weather_code",
                    0,
                )
                or 0
            ),

        **context,

        "source":
            "Open-Meteo Forecast API",
    }