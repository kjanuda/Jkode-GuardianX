from __future__ import annotations

from collections import Counter
from math import pi
import re
import time

import requests

from app.core.config import settings


class OSMContextError(Exception):
    pass


VEGETATION_LANDUSE = {
    "forest",
    "orchard",
    "vineyard",
    "meadow",
    "grass",
}

VEGETATION_NATURAL = {
    "wood",
    "scrub",
    "grassland",
    "heath",
}


# -------------------------------------------------
# Simple in-memory cache
#
# OSM land/building context does not change every
# second. This avoids repeatedly calling Overpass
# from Risk / Environment endpoints.
# -------------------------------------------------

_CACHE: dict[tuple, dict] = {}

CACHE_TTL_SECONDS = 1800


def classify_built_environment(
    density_per_km2: float,
) -> str:
    if density_per_km2 < 50:
        return "LOW"

    if density_per_km2 < 200:
        return "MODERATE"

    return "HIGH"


def classify_vegetation_context(
    feature_count: int,
) -> str:
    if feature_count == 0:
        return "LOW"

    if feature_count < 5:
        return "MODERATE"

    return "HIGH"


def get_cache_key(
    latitude: float,
    longitude: float,
    radius_m: int,
) -> tuple:
    # ~100 m spatial bucket.
    # Fine for our 500 m context window and
    # prevents simulator GPS jitter from causing
    # a new Overpass request every packet.
    return (
        round(latitude, 3),
        round(longitude, 3),
        radius_m,
    )


def get_cached_context(
    key: tuple,
) -> dict | None:
    cached = _CACHE.get(key)

    if cached is None:
        return None

    age = (
        time.time()
        - cached["cached_at"]
    )

    if age > CACHE_TTL_SECONDS:
        _CACHE.pop(
            key,
            None,
        )

        return None

    return cached["data"]


def save_to_cache(
    key: tuple,
    data: dict,
) -> None:
    _CACHE[key] = {
        "cached_at": time.time(),
        "data": data,
    }


def build_overpass_query(
    latitude: float,
    longitude: float,
    radius_m: int,
) -> str:
    return f"""
    [out:json][timeout:25];

    (
      nwr["building"]
        (around:{radius_m},{latitude},{longitude});

      nwr["landuse"~"forest|orchard|vineyard|meadow|grass"]
        (around:{radius_m},{latitude},{longitude});

      nwr["natural"~"wood|scrub|grassland|heath"]
        (around:{radius_m},{latitude},{longitude});
    );

    out tags center;
    """


def request_overpass(
    url: str,
    query: str,
    retries: int = 2,
) -> dict:
    last_error = None

    for attempt in range(
        retries + 1
    ):
        try:
            response = requests.post(
                url,
                data={
                    "data": query,
                },
                headers={
                    "User-Agent":
                        "GuardianX-Network-Research/0.1",
                },
                timeout=35,
            )

            if response.status_code in {
                429,
                502,
                503,
                504,
            }:
                last_error = (
                    f"HTTP "
                    f"{response.status_code}"
                )

                if attempt < retries:
                    time.sleep(
                        1.5
                        * (
                            attempt + 1
                        )
                    )

                    continue

            response.raise_for_status()

            payload = response.json()

            if not isinstance(
                payload,
                dict,
            ):
                raise ValueError(
                    "Invalid Overpass payload"
                )

            return payload

        except (
            requests.RequestException,
            ValueError,
        ) as exc:
            last_error = str(exc)

            if attempt < retries:
                time.sleep(
                    1.5
                    * (
                        attempt + 1
                    )
                )

    raise OSMContextError(
        f"Overpass request failed: "
        f"{last_error}"
    )


def fetch_overpass_payload(
    query: str,
) -> dict:
    endpoints = [
        settings.overpass_api_url,
        settings.overpass_fallback_url,
    ]

    errors = []

    for endpoint in endpoints:
        try:
            return request_overpass(
                url=endpoint,
                query=query,
            )

        except OSMContextError as exc:
            errors.append(
                f"{endpoint}: {exc}"
            )

    raise OSMContextError(
        "All configured Overpass "
        "endpoints failed. "
        + " | ".join(errors)
    )


def fetch_osm_environment_context(
    latitude: float,
    longitude: float,
    radius_m: int = 500,
) -> dict:
    cache_key = get_cache_key(
        latitude=latitude,
        longitude=longitude,
        radius_m=radius_m,
    )

    cached = get_cached_context(
        cache_key
    )

    if cached is not None:
        return {
            **cached,
            "cache_hit": True,
        }

    query = build_overpass_query(
        latitude=latitude,
        longitude=longitude,
        radius_m=radius_m,
    )

    payload = fetch_overpass_payload(
        query
    )

    elements = payload.get(
        "elements",
        [],
    )

    unique_elements = {}

    for element in elements:
        key = (
            element.get("type"),
            element.get("id"),
        )

        unique_elements[
            key
        ] = element

    building_count = 0
    vegetation_feature_count = 0

    vegetation_tags = Counter()

    for element in (
        unique_elements.values()
    ):
        tags = element.get(
            "tags",
            {},
        )

        if "building" in tags:
            building_count += 1

        landuse = tags.get(
            "landuse"
        )

        natural = tags.get(
            "natural"
        )

        vegetation_match = False

        if (
            landuse
            in VEGETATION_LANDUSE
        ):
            vegetation_tags[
                landuse
            ] += 1

            vegetation_match = True

        if (
            natural
            in VEGETATION_NATURAL
        ):
            vegetation_tags[
                natural
            ] += 1

            vegetation_match = True

        if vegetation_match:
            vegetation_feature_count += 1

    radius_km = (
        radius_m / 1000
    )

    area_km2 = (
        pi
        * radius_km
        * radius_km
    )

    if area_km2 > 0:
        building_density = (
            building_count
            / area_km2
        )

    else:
        building_density = 0

    result = {
        "radius_m":
            radius_m,

        "area_km2":
            round(
                area_km2,
                4,
            ),

        "building_count":
            building_count,

        "building_density_per_km2":
            round(
                building_density,
                2,
            ),

        "built_environment_level":
            classify_built_environment(
                building_density
            ),

        "vegetation_feature_count":
            vegetation_feature_count,

        "vegetation_context_level":
            classify_vegetation_context(
                vegetation_feature_count
            ),

        "forest_feature_count":
            vegetation_tags[
                "forest"
            ],

        "wood_feature_count":
            vegetation_tags[
                "wood"
            ],

        "scrub_feature_count":
            vegetation_tags[
                "scrub"
            ],

        "grass_feature_count":
            (
                vegetation_tags[
                    "grass"
                ]
                + vegetation_tags[
                    "grassland"
                ]
                + vegetation_tags[
                    "meadow"
                ]
            ),

        "orchard_feature_count":
            (
                vegetation_tags[
                    "orchard"
                ]
                + vegetation_tags[
                    "vineyard"
                ]
            ),

        "source":
            "OpenStreetMap / Overpass API",

        "note": (
            "Counts depend on OpenStreetMap "
            "mapping completeness and are "
            "context indicators, not exact "
            "physical coverage percentages."
        ),

        "cache_hit":
            False,
    }

    save_to_cache(
        cache_key,
        result,
    )

    return result


# =================================================
# OSM BUILDING HEIGHT
# =================================================


def parse_osm_height_m(
    value: str | None,
) -> float | None:
    """
    Parse an OSM height value into metres.

    Examples:

        "12"       -> 12.0 m
        "12 m"     -> 12.0 m
        "12.5m"    -> 12.5 m
        "30 ft"    -> 9.14 m
        "30'"      -> 9.14 m

    Invalid or non-positive values return None.
    """

    if not value:
        return None

    text = (
        str(value)
        .strip()
        .lower()
    )

    # ---------------------------------------------
    # Feet / imperial.
    #
    # We intentionally treat values containing
    # "ft" or "'" as feet.
    # ---------------------------------------------

    if (
        "ft" in text
        or "'" in text
    ):
        numbers = re.findall(
            r"-?\d+(?:\.\d+)?",
            text,
        )

        if not numbers:
            return None

        feet = float(
            numbers[0]
        )

        if feet <= 0:
            return None

        return round(
            feet * 0.3048,
            2,
        )

    # ---------------------------------------------
    # Metric / plain numeric values.
    # ---------------------------------------------

    numbers = re.findall(
        r"-?\d+(?:\.\d+)?",
        text,
    )

    if not numbers:
        return None

    height = float(
        numbers[0]
    )

    if height <= 0:
        return None

    return round(
        height,
        2,
    )


def get_building_height_estimate(
    tags: dict,
) -> dict | None:
    """
    Determine a building's physical height.

    Height precedence:

    1. Explicit OSM `height`
    2. `building:levels` derived estimate
    3. Unknown

    Unknown-height buildings are NOT assigned
    an arbitrary physical height.

    This is important for Fresnel analysis:
    building density can be used as context,
    but an unknown building height should not
    become fake obstruction geometry.
    """

    # ---------------------------------------------
    # Highest confidence:
    # Explicit OSM height.
    # ---------------------------------------------

    explicit_height = (
        parse_osm_height_m(
            tags.get(
                "height"
            )
        )
    )

    if explicit_height is not None:
        return {
            "height_m":
                explicit_height,

            "height_source":
                "OSM_HEIGHT",

            "confidence":
                0.9,
        }

    # ---------------------------------------------
    # Second option:
    # Estimate from building levels.
    #
    # Approximation:
    # 1 level ~= 3 metres.
    #
    # This is explicitly marked as an estimate
    # and has lower confidence.
    # ---------------------------------------------

    levels_raw = tags.get(
        "building:levels"
    )

    if levels_raw:
        try:
            levels = float(
                levels_raw
            )

            if levels > 0:
                return {
                    "height_m":
                        round(
                            levels * 3.0,
                            2,
                        ),

                    "height_source":
                        "OSM_BUILDING_LEVELS_ESTIMATE",

                    "confidence":
                        0.65,
                }

        except (
            TypeError,
            ValueError,
        ):
            pass

    # ---------------------------------------------
    # No reliable height information.
    #
    # Do NOT invent a height.
    # ---------------------------------------------

    return None


def fetch_osm_building_features(
    latitude: float,
    longitude: float,
    radius_m: int = 2000,
) -> list[dict]:
    """
    Fetch OSM buildings with usable physical
    height information.

    Buildings with unknown height remain useful
    for general environmental/density context,
    but are NOT inserted into Fresnel geometry.

    Returned features contain:

        {
            "osm_type": "way",
            "osm_id": 123456,
            "latitude": ...,
            "longitude": ...,
            "building_type": "residential",
            "height_m": 12.0,
            "height_source": "OSM_HEIGHT",
            "confidence": 0.9,
            "source": "OpenStreetMap / Overpass API",
        }
    """

    query = f"""
    [out:json][timeout:25];

    (
      nwr["building"]
        (around:{radius_m},{latitude},{longitude});
    );

    out tags center;
    """

    payload = fetch_overpass_payload(
        query
    )

    elements = payload.get(
        "elements",
        [],
    )

    features = []

    seen = set()

    for element in elements:
        identity = (
            element.get(
                "type"
            ),
            element.get(
                "id"
            ),
        )

        if identity in seen:
            continue

        seen.add(
            identity
        )

        tags = element.get(
            "tags",
            {},
        )

        height_info = (
            get_building_height_estimate(
                tags
            )
        )

        # -----------------------------------------
        # Building exists but physical height is
        # unknown.
        #
        # Do not inject it into Fresnel geometry.
        # -----------------------------------------

        if height_info is None:
            continue

        latitude_value = (
            element.get(
                "lat"
            )
        )

        longitude_value = (
            element.get(
                "lon"
            )
        )

        # Ways/relations usually expose their
        # center coordinates rather than lat/lon
        # directly.
        center = element.get(
            "center",
            {},
        )

        if latitude_value is None:
            latitude_value = (
                center.get(
                    "lat"
                )
            )

        if longitude_value is None:
            longitude_value = (
                center.get(
                    "lon"
                )
            )

        if (
            latitude_value is None
            or longitude_value is None
        ):
            continue

        features.append(
            {
                "osm_type":
                    element.get(
                        "type"
                    ),

                "osm_id":
                    element.get(
                        "id"
                    ),

                "latitude":
                    float(
                        latitude_value
                    ),

                "longitude":
                    float(
                        longitude_value
                    ),

                "building_type":
                    tags.get(
                        "building"
                    ),

                **height_info,

                "source":
                    "OpenStreetMap / "
                    "Overpass API",
            }
        )

    return features