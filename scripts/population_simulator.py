import argparse
import random
import time

import requests


API_BASE = "http://127.0.0.1:8000"

CELL_ID = "GX-CELL-001"

BASE_LATITUDE = 7.2800
BASE_LONGITUDE = 80.6600


# ==========================================================
# Coverage geo anchors
# ==========================================================
#
# Fixed, previously validated anchors used for
# deterministic placement of affected coverage devices.

COVERAGE_GEO_ANCHORS = {
    "a": {
        "latitude": 7.280272,
        "longitude": 80.657798,
    },
    "b": {
        "latitude": 7.279228,
        "longitude": 80.658015,
    },
    "c": {
        "latitude": 7.282273,
        "longitude": 80.658695,
    },
}


COVERAGE_GEO_ANCHOR_ORDER = (
    "a",
    "b",
    "c",
)


def get_coverage_geo_anchor(
    anchor_name: str,
) -> dict:
    if (
        anchor_name
        not in COVERAGE_GEO_ANCHORS
    ):
        raise ValueError(
            "Unknown coverage geo anchor: "
            f"{anchor_name}"
        )

    return {
        **COVERAGE_GEO_ANCHORS[
            anchor_name
        ],
        "name": anchor_name,
    }


def get_coverage_geo_for_index(
    affected_index: int,
    anchor_mode: str,
) -> dict:
    if anchor_mode == "cycle":
        anchor_name = (
            COVERAGE_GEO_ANCHOR_ORDER[
                affected_index
                % len(
                    COVERAGE_GEO_ANCHOR_ORDER
                )
            ]
        )
    else:
        anchor_name = anchor_mode

    anchor = get_coverage_geo_anchor(
        anchor_name
    )

    return anchor


# ==========================================================
# Scenario severity profiles
# ==========================================================

SCENARIO_PROFILES = {
    "mild": {
        "affected_ratio": 0.60,
        "severity": 0.60,
        "background_ratio": 0.05,
    },
    "moderate": {
        "affected_ratio": 0.80,
        "severity": 0.75,
        "background_ratio": 0.08,
    },
    "severe": {
        "affected_ratio": 0.90,
        "severity": 0.90,
        "background_ratio": 0.10,
    },
}


def get_scenario_profile(
    profile_name: str,
) -> dict:
    if profile_name not in SCENARIO_PROFILES:
        raise ValueError(
            f"Unknown scenario profile: {profile_name}"
        )

    profile = SCENARIO_PROFILES[
        profile_name
    ].copy()

    profile["name"] = profile_name

    return profile


def affected_limit(
    count_per_model: int,
    affected_ratio: float,
) -> int:
    limit = round(
        count_per_model
        * affected_ratio
    )

    return max(
        1,
        min(
            count_per_model,
            limit,
        ),
    )


MODELS = [
    {
        "manufacturer": "Samsung",
        "model": "Galaxy A55",
        "os_name": "Android",
        "os_version": "16",
        "firmware": "A55-DEMO-1.0",
        "modem": "EXYNOS-DEMO",
    },
    {
        "manufacturer": "Apple",
        "model": "iPhone 15",
        "os_name": "iOS",
        "os_version": "20",
        "firmware": "IOS-DEMO-1.0",
        "modem": "APPLE-DEMO",
    },
    {
        "manufacturer": "Xiaomi",
        "model": "Redmi Note 14",
        "os_name": "Android",
        "os_version": "16",
        "firmware": "RN14-DEMO-1.0",
        "modem": "MTK-DEMO",
    },
    {
        "manufacturer": "Guardian",
        "model": "DemoPhone X1",
        "os_name": "Android",
        "os_version": "16",
        "firmware": "X1-DEMO-1.0",
        "modem": "GX-MODEM-X1",
    },
]


def request_json(
    method: str,
    path: str,
    *,
    json=None,
):
    url = f"{API_BASE}{path}"

    return requests.request(
        method,
        url,
        json=json,
        timeout=30,
    )


def create_if_missing(
    path: str,
    payload: dict,
):
    response = request_json(
        "POST",
        path,
        json=payload,
    )

    if response.status_code in {
        200,
        201,
    }:
        return

    # Existing synthetic records can safely
    # be reused on later simulator runs.
    if response.status_code in {
        400,
        409,
    }:
        return

    raise RuntimeError(
        f"{path} failed "
        f"({response.status_code}): "
        f"{response.text}"
    )


def create_customer_and_device(
    index: int,
    model_info: dict,
):
    customer_code = (
        f"GX-POP-CUST-{index:03d}"
    )

    device_id = (
        f"GX-POP-DEVICE-{index:03d}"
    )

    sim_id = (
        f"GX-POP-SIM-{index:03d}"
    )

    # ----------------------------------
    # Customer
    # ----------------------------------

    create_if_missing(
        "/api/v1/customers",
        {
            "customer_code": customer_code,
            "name": (
                "Synthetic Population "
                f"Customer {index:03d}"
            ),
            "status": "ACTIVE",
        },
    )

    # ----------------------------------
    # Device
    # ----------------------------------

    create_if_missing(
        "/api/v1/devices",
        {
            "device_id": device_id,
            "customer_code": customer_code,
            "current_cell_id": CELL_ID,
            "model": model_info["model"],
            "manufacturer": model_info[
                "manufacturer"
            ],
            "software_version": model_info[
                "firmware"
            ],
            "antenna_type": "INTERNAL",
            "status": "ACTIVE",
        },
    )

    # ----------------------------------
    # SIM
    # ----------------------------------

    create_if_missing(
        "/api/v1/sims",
        {
            "sim_id": sim_id,
            "device_id": device_id,
            "operator": "Synthetic Operator",
            "plan_type": "PREPAID",
            "status": "ACTIVE",
        },
    )

    # ----------------------------------
    # Correlation / RCA profile
    # ----------------------------------

    profile_response = request_json(
        "PUT",
        (
            f"/api/v1/correlation/device/"
            f"{device_id}/profile"
        ),
        json={
            "manufacturer": model_info[
                "manufacturer"
            ],
            "model_name": model_info[
                "model"
            ],
            "os_name": model_info[
                "os_name"
            ],
            "os_version": model_info[
                "os_version"
            ],
            "firmware_version": model_info[
                "firmware"
            ],
            "modem_version": model_info[
                "modem"
            ],
        },
    )

    if profile_response.status_code != 200:
        raise RuntimeError(
            f"Device profile failed for "
            f"{device_id}: "
            f"{profile_response.text}"
        )

    return device_id


# ==========================================================
# Healthy population sample
# ==========================================================


def healthy_sample():
    rsrp = random.uniform(
        -94,
        -82,
    )

    return {
        "scenario": "population_normal",
        "rsrp": round(
            rsrp,
            2,
        ),
        "rsrq": round(
            random.uniform(
                -11,
                -7,
            ),
            2,
        ),
        "rssi": round(
            rsrp
            + random.uniform(
                20,
                28,
            ),
            2,
        ),
        "sinr": round(
            random.uniform(
                14,
                24,
            ),
            2,
        ),
        "cqi": random.randint(
            10,
            15,
        ),
        "mcs": random.randint(
            18,
            28,
        ),
        "dl_speed_mbps": round(
            random.uniform(
                40,
                90,
            ),
            2,
        ),
        "up_speed_mbps": round(
            random.uniform(
                10,
                30,
            ),
            2,
        ),
        "latency_ms": round(
            random.uniform(
                20,
                45,
            ),
            2,
        ),
        "jitter_ms": round(
            random.uniform(
                2,
                10,
            ),
            2,
        ),
        "packet_loss_pct": round(
            random.uniform(
                0,
                0.4,
            ),
            2,
        ),
    }


# ==========================================================
# Network / congestion degradation
# ==========================================================


def network_degraded_sample(
    profile_name: str = "moderate",
):
    """
    Healthy-ish radio with degraded network KPIs.

    Profiles vary congestion/backhaul severity
    while preserving the same RCA family.
    """

    profiles = {
        "mild": {
            "dl": (10.0, 14.5),
            "ul": (4.0, 8.0),
            "latency": (85.0, 110.0),
            "jitter": (10.0, 25.0),
            "loss": (2.2, 4.0),
        },
        "moderate": {
            "dl": (6.0, 10.0),
            "ul": (2.0, 5.0),
            "latency": (110.0, 150.0),
            "jitter": (20.0, 40.0),
            "loss": (4.0, 7.0),
        },
        "severe": {
            "dl": (2.0, 6.0),
            "ul": (0.8, 3.0),
            "latency": (150.0, 220.0),
            "jitter": (35.0, 65.0),
            "loss": (7.0, 12.0),
        },
    }

    config = profiles[
        profile_name
    ]

    rsrp = random.uniform(
        -94,
        -82,
    )

    return {
        "scenario": (
            f"population_network_"
            f"{profile_name}"
        ),

        # Healthy / usable radio.
        "rsrp": round(
            rsrp,
            2,
        ),
        "rsrq": round(
            random.uniform(
                -11,
                -7,
            ),
            2,
        ),
        "rssi": round(
            rsrp
            + random.uniform(
                20,
                28,
            ),
            2,
        ),
        "sinr": round(
            random.uniform(
                13,
                23,
            ),
            2,
        ),
        "cqi": random.randint(
            9,
            14,
        ),
        "mcs": random.randint(
            15,
            25,
        ),

        # Profile-dependent network degradation.
        "dl_speed_mbps": round(
            random.uniform(
                *config["dl"]
            ),
            2,
        ),
        "up_speed_mbps": round(
            random.uniform(
                *config["ul"]
            ),
            2,
        ),
        "latency_ms": round(
            random.uniform(
                *config["latency"]
            ),
            2,
        ),
        "jitter_ms": round(
            random.uniform(
                *config["jitter"]
            ),
            2,
        ),
        "packet_loss_pct": round(
            random.uniform(
                *config["loss"]
            ),
            2,
        ),
    }


# ==========================================================
# Device-model-specific degradation
# ==========================================================


def device_model_fault_sample():
    """
    Device-specific RF/modem-like
    degradation pattern.

    Network location is shared with
    healthy control devices.
    """

    rsrp = random.uniform(
        -95,
        -84,
    )

    return {
        "scenario": "device_model_fault",
        "rsrp": round(
            rsrp,
            2,
        ),
        "rsrq": round(
            random.uniform(
                -18,
                -13,
            ),
            2,
        ),
        "rssi": round(
            rsrp
            + random.uniform(
                20,
                27,
            ),
            2,
        ),
        "sinr": round(
            random.uniform(
                -2,
                6,
            ),
            2,
        ),
        "cqi": random.randint(
            2,
            7,
        ),
        "mcs": random.randint(
            3,
            12,
        ),
        "dl_speed_mbps": round(
            random.uniform(
                3,
                14,
            ),
            2,
        ),
        "up_speed_mbps": round(
            random.uniform(
                1,
                6,
            ),
            2,
        ),
        "latency_ms": round(
            random.uniform(
                75,
                140,
            ),
            2,
        ),
        "jitter_ms": round(
            random.uniform(
                10,
                35,
            ),
            2,
        ),
        "packet_loss_pct": round(
            random.uniform(
                2.2,
                6,
            ),
            2,
        ),
    }


# ==========================================================
# Coverage degradation
# ==========================================================


def coverage_degraded_sample(
    profile_name: str = "moderate",
    coverage_subtype: str = "generic",
):
    """
    Population-wide RF coverage / propagation degradation.

    Profiles vary RF severity while keeping
    the scenario inside the same coverage family.
    """

    profiles = {
        "mild": {
            "rsrp": (-112.0, -106.0),
            "rsrq": (-15.5, -13.5),
            "sinr": (3.0, 6.5),
            "cqi": (4, 8),
            "mcs": (7, 14),
            "dl": (8.0, 14.0),
            "ul": (3.0, 7.0),
            "latency": (80.0, 115.0),
            "jitter": (12.0, 28.0),
            "loss": (2.2, 4.5),
        },

        "moderate": {
            "rsrp": (-118.0, -112.0),
            "rsrq": (-18.0, -15.0),
            "sinr": (-1.0, 4.0),
            "cqi": (2, 6),
            "mcs": (4, 10),
            "dl": (4.0, 10.0),
            "ul": (1.5, 5.0),
            "latency": (110.0, 155.0),
            "jitter": (20.0, 40.0),
            "loss": (4.0, 7.0),
        },

        "severe": {
            "rsrp": (-124.0, -118.0),
            "rsrq": (-21.0, -17.0),
            "sinr": (-5.0, 1.0),
            "cqi": (1, 4),
            "mcs": (1, 7),
            "dl": (1.0, 5.0),
            "ul": (0.5, 3.0),
            "latency": (150.0, 220.0),
            "jitter": (35.0, 65.0),
            "loss": (7.0, 12.0),
        },
    }

    config = profiles[
        profile_name
    ]

    rsrp = random.uniform(
        *config["rsrp"]
    )

    return {
        "scenario": (
            f"population_coverage_"
            f"{coverage_subtype}_"
            f"{profile_name}"
        ),

        "rsrp": round(
            rsrp,
            2,
        ),
        "rsrq": round(
            random.uniform(
                *config["rsrq"]
            ),
            2,
        ),
        "rssi": round(
            rsrp
            + random.uniform(
                18,
                25,
            ),
            2,
        ),
        "sinr": round(
            random.uniform(
                *config["sinr"]
            ),
            2,
        ),
        "cqi": random.randint(
            *config["cqi"]
        ),
        "mcs": random.randint(
            *config["mcs"]
        ),

        "dl_speed_mbps": round(
            random.uniform(
                *config["dl"]
            ),
            2,
        ),
        "up_speed_mbps": round(
            random.uniform(
                *config["ul"]
            ),
            2,
        ),
        "latency_ms": round(
            random.uniform(
                *config["latency"]
            ),
            2,
        ),
        "jitter_ms": round(
            random.uniform(
                *config["jitter"]
            ),
            2,
        ),
        "packet_loss_pct": round(
            random.uniform(
                *config["loss"]
            ),
            2,
        ),
    }


# ==========================================================
# Population-wide interference degradation
# ==========================================================
#
# All interference RSRP ranges stay >= -100 so the
# interference detector's usable-RSRP condition is
# preserved. The coverage signature's weak-RSRP
# threshold is < -105, so these profiles stay safely
# away from it.

INTERFERENCE_PROFILES = {
    "mild": {
        "rsrp": (-96, -86),
        "rsrq": (-16.5, -14.0),
        "sinr": (2.0, 6.0),
        "cqi": (5, 9),
        "mcs": (8, 16),
        "dl": (16, 25),
        "ul": (6, 11),
        "latency": (45, 75),
        "jitter": (8, 18),
        "loss": (0.8, 2.0),
    },
    "moderate": {
        "rsrp": (-98, -86),
        "rsrq": (-19.0, -16.0),
        "sinr": (-1.0, 4.0),
        "cqi": (3, 7),
        "mcs": (5, 12),
        "dl": (10, 18),
        "ul": (4, 8),
        "latency": (65, 105),
        "jitter": (15, 30),
        "loss": (1.5, 3.5),
    },
    "severe": {
        "rsrp": (-99, -87),
        "rsrq": (-22.0, -18.0),
        "sinr": (-5.0, 1.0),
        "cqi": (1, 5),
        "mcs": (2, 8),
        "dl": (5, 12),
        "ul": (2, 6),
        "latency": (90, 140),
        "jitter": (25, 45),
        "loss": (3.0, 6.0),
    },
}


def interference_degraded_sample(
    profile: dict,
):
    """
    Usable signal strength with degraded
    radio quality caused by interference.

    RSRP intentionally remains usable while
    RSRQ and SINR become progressively worse
    across mild/moderate/severe profiles.
    """

    profile_name = profile["name"]

    config = INTERFERENCE_PROFILES[
        profile_name
    ]

    rsrp = random.uniform(
        *config["rsrp"]
    )

    return {
        "scenario": (
            f"population_interference_"
            f"{profile_name}"
        ),

        "rsrp": round(
            rsrp,
            2,
        ),

        "rsrq": round(
            random.uniform(
                *config["rsrq"]
            ),
            2,
        ),

        "rssi": round(
            rsrp
            + random.uniform(
                20,
                27,
            ),
            2,
        ),

        "sinr": round(
            random.uniform(
                *config["sinr"]
            ),
            2,
        ),

        "cqi": random.randint(
            *config["cqi"]
        ),

        "mcs": random.randint(
            *config["mcs"]
        ),

        "dl_speed_mbps": round(
            random.uniform(
                *config["dl"]
            ),
            2,
        ),

        "up_speed_mbps": round(
            random.uniform(
                *config["ul"]
            ),
            2,
        ),

        "latency_ms": round(
            random.uniform(
                *config["latency"]
            ),
            2,
        ),

        "jitter_ms": round(
            random.uniform(
                *config["jitter"]
            ),
            2,
        ),

        "packet_loss_pct": round(
            random.uniform(
                *config["loss"]
            ),
            2,
        ),
    }


# ==========================================================
# Population-wide outage degradation
# ==========================================================


OUTAGE_PROFILES = {
    "mild": {
        "dl": (0.65, 0.95),
        "ul": (0.25, 0.55),
        "latency": (250, 420),
        "jitter": (60, 120),
        "loss": (55, 70),
    },
    "moderate": {
        "dl": (0.25, 0.60),
        "ul": (0.08, 0.30),
        "latency": (400, 650),
        "jitter": (100, 200),
        "loss": (70, 85),
    },
    "severe": {
        "dl": (0.02, 0.20),
        "ul": (0.01, 0.10),
        "latency": (650, 1000),
        "jitter": (180, 350),
        "loss": (85, 98),
    },
}


def outage_degraded_sample(
    profile: dict,
):
    """
    Healthy radio conditions with severe
    service-layer failure.

    Radio remains healthy so outage cases
    are not confused with coverage or
    interference failures.
    """

    profile_name = profile["name"]

    config = OUTAGE_PROFILES[
        profile_name
    ]

    rsrp = random.uniform(
        -94,
        -82,
    )

    return {
        "scenario": (
            f"population_outage_"
            f"{profile_name}"
        ),

        "rsrp": round(
            rsrp,
            2,
        ),

        "rsrq": round(
            random.uniform(
                -11,
                -7,
            ),
            2,
        ),

        "rssi": round(
            rsrp
            + random.uniform(
                20,
                28,
            ),
            2,
        ),

        "sinr": round(
            random.uniform(
                14,
                23,
            ),
            2,
        ),

        "cqi": random.randint(
            9,
            15,
        ),

        "mcs": random.randint(
            15,
            27,
        ),

        "dl_speed_mbps": round(
            random.uniform(
                *config["dl"]
            ),
            2,
        ),

        "up_speed_mbps": round(
            random.uniform(
                *config["ul"]
            ),
            2,
        ),

        "latency_ms": round(
            random.uniform(
                *config["latency"]
            ),
            2,
        ),

        "jitter_ms": round(
            random.uniform(
                *config["jitter"]
            ),
            2,
        ),

        "packet_loss_pct": round(
            random.uniform(
                *config["loss"]
            ),
            2,
        ),
    }



# ==========================================================
# Send telemetry
# ==========================================================


def send_telemetry(
    device_id: str,
    sample: dict,
    geo: dict | None = None,
):
    if geo is None:
        latitude = (
            BASE_LATITUDE
            + random.uniform(
                -0.003,
                0.003,
            )
        )

        longitude = (
            BASE_LONGITUDE
            + random.uniform(
                -0.003,
                0.003,
            )
        )

    else:
        latitude = float(
            geo["latitude"]
        )

        longitude = float(
            geo["longitude"]
        )

    payload = {
        "device_id": device_id,
        "cell_id": CELL_ID,
        "scenario": sample[
            "scenario"
        ],
        "radio": {
            "rsrp": sample["rsrp"],
            "rsrq": sample["rsrq"],
            "rssi": sample["rssi"],
            "sinr": sample["sinr"],
            "cqi": sample["cqi"],
            "mcs": sample["mcs"],
        },
        # Simulator name -> API/DB name
        #
        # dl_speed_mbps   -> download_mbps
        # up_speed_mbps   -> upload_mbps
        # packet_loss_pct -> packet_loss
        "network": {
            "download_mbps": sample[
                "dl_speed_mbps"
            ],
            "upload_mbps": sample[
                "up_speed_mbps"
            ],
            "latency_ms": sample[
                "latency_ms"
            ],
            "jitter_ms": sample[
                "jitter_ms"
            ],
            "packet_loss": sample[
                "packet_loss_pct"
            ],
        },
        "geo": {
            "latitude": round(
                latitude,
                6,
            ),
            "longitude": round(
                longitude,
                6,
            ),
        },
    }

    response = request_json(
        "POST",
        "/api/v1/telemetry",
        json=payload,
    )

    if response.status_code not in {
        200,
        201,
    }:
        raise RuntimeError(
            f"Telemetry failed for "
            f"{device_id}: "
            f"{response.status_code} "
            f"{response.text}"
        )


# ==========================================================
# Build population
# ==========================================================


def build_population(
    count_per_model: int,
):
    population = []

    index = 1

    for model_info in MODELS:
        for model_number in range(
            count_per_model
        ):
            device_id = (
                create_customer_and_device(
                    index=index,
                    model_info=model_info,
                )
            )

            population.append(
                {
                    "device_id": device_id,
                    "manufacturer": (
                        model_info[
                            "manufacturer"
                        ]
                    ),
                    "model": (
                        model_info[
                            "model"
                        ]
                    ),
                    "model_index": (
                        model_number
                    ),
                }
            )

            index += 1

    return population


# ==========================================================
# Network-wide test
# ==========================================================


def run_network_test(
    population: list[dict],
    profile: dict,
    count_per_model: int,
):
    print()
    print("NETWORK-WIDE TEST")
    print("-" * 72)

    # Affected share of every model cohort
    # is controlled by the scenario profile
    # (mild ~60%, moderate ~80%, severe ~90%).
    limit = affected_limit(
        count_per_model=count_per_model,
        affected_ratio=profile[
            "affected_ratio"
        ],
    )

    for device in population:
        affected = (
            device["model_index"] < limit
        )

        if affected:
            sample = network_degraded_sample(
                profile["name"]
            )
            state = "AFFECTED"

        else:
            sample = healthy_sample()
            state = "HEALTHY"

        send_telemetry(
            device["device_id"],
            sample,
        )

        print(
            f"{device['device_id']} | "
            f"{device['model']:<16} | "
            f"{state}"
        )

        time.sleep(0.03)


# ==========================================================
# Device-model test
# ==========================================================


def run_device_model_test(
    population: list[dict],
    profile: dict,
    count_per_model: int,
    target_model: str,
):
    print()
    print("DEVICE-MODEL TEST")
    print("-" * 72)

    target_limit = affected_limit(
        count_per_model=count_per_model,
        affected_ratio=profile[
            "affected_ratio"
        ],
    )

    background_limit = affected_limit(
        count_per_model=count_per_model,
        affected_ratio=profile[
            "background_ratio"
        ],
    )

    print(
        f"Target model     : {target_model}"
    )
    print(
        "Target affected  : "
        f"{target_limit}/"
        f"{count_per_model}"
    )
    print(
        "Background/model : "
        f"{background_limit}/"
        f"{count_per_model}"
    )
    print("-" * 72)

    for device in population:
        is_target = (
            device["model"]
            == target_model
        )

        if (
            is_target
            and device["model_index"]
            < target_limit
        ):
            sample = (
                device_model_fault_sample()
            )

            state = "TARGET_AFFECTED"

        elif (
            not is_target
            and device["model_index"]
            < background_limit
        ):
            sample = (
                device_model_fault_sample()
            )

            state = (
                "BACKGROUND_AFFECTED"
            )

        else:
            sample = healthy_sample()
            state = "HEALTHY"

        send_telemetry(
            device["device_id"],
            sample,
        )

        print(
            f"{device['device_id']} | "
            f"{device['model']:<16} | "
            f"{state}"
        )

        time.sleep(0.03)


# ==========================================================
# Coverage test
# ==========================================================


def run_coverage_test(
    population: list[dict],
    profile: dict,
    count_per_model: int,
    geo_anchor_name: str,
    coverage_subtype: str,
):
    print()
    print("POPULATION COVERAGE TEST")
    print("-" * 72)

    affected_index = 0

    # Affected share of every model cohort
    # experiences the same coverage /
    # propagation degradation, controlled
    # by the scenario profile.
    #
    # The remaining devices act as
    # healthy controls.
    limit = affected_limit(
        count_per_model=count_per_model,
        affected_ratio=profile[
            "affected_ratio"
        ],
    )

    for device in population:
        affected = (
            device["model_index"] < limit
        )

        if affected:
            sample = coverage_degraded_sample(
                profile["name"],
                coverage_subtype,
            )

            if coverage_subtype == "terrain":
                geo = get_coverage_geo_for_index(
                    affected_index=affected_index,
                    anchor_mode=geo_anchor_name,
                )

                affected_index += 1

            else:
                # Generic coverage is intentionally not
                # pinned onto a known blocked terrain path.
                geo = None

            state = "AFFECTED"

        else:
            sample = healthy_sample()

            # Healthy controls remain spatially
            # varied instead of being forced onto
            # the blocked candidate path.
            geo = None

            state = "HEALTHY"

        send_telemetry(
            device["device_id"],
            sample,
            geo=geo,
        )

        if (
            affected
            and coverage_subtype == "terrain"
        ):
            location_label = (
                f"GEO-{geo['name'].upper()}"
            )

        elif affected:
            location_label = "GENERIC"

        else:
            location_label = "RANDOM"

        print(
            f"{device['device_id']} | "
            f"{device['model']:<16} | "
            f"{state:<8} | "
            f"{location_label}"
        )

        time.sleep(0.03)


# ==========================================================
# Interference population test
# ==========================================================


def run_interference_test(
    population: list[dict],
    profile: dict,
    count_per_model: int,
):
    print()
    print(
        "POPULATION INTERFERENCE TEST"
    )
    print("-" * 72)

    limit = affected_limit(
        count_per_model=count_per_model,
        affected_ratio=profile[
            "affected_ratio"
        ],
    )

    print(
        f"Profile          : "
        f"{profile['name']}"
    )
    print(
        f"Affected/model   : "
        f"{limit}/{count_per_model}"
    )
    print("-" * 72)

    for device in population:
        affected = (
            device["model_index"]
            < limit
        )

        if affected:
            sample = (
                interference_degraded_sample(
                    profile
                )
            )

            state = "AFFECTED"

        else:
            sample = (
                healthy_sample()
            )

            state = "HEALTHY"

        send_telemetry(
            device["device_id"],
            sample,
        )

        print(
            f"{device['device_id']} | "
            f"{device['model']:<16} | "
            f"{state}"
        )

        time.sleep(
            0.03
        )


# ==========================================================
# Outage population test
# ==========================================================


def run_outage_test(
    population: list[dict],
    profile: dict,
    count_per_model: int,
):
    print()
    print(
        "POPULATION OUTAGE TEST"
    )
    print("-" * 72)

    limit = affected_limit(
        count_per_model=count_per_model,
        affected_ratio=profile[
            "affected_ratio"
        ],
    )

    print(
        f"Profile          : "
        f"{profile['name']}"
    )

    print(
        f"Affected/model   : "
        f"{limit}/{count_per_model}"
    )

    print("-" * 72)

    for device in population:
        affected = (
            device["model_index"]
            < limit
        )

        if affected:
            sample = (
                outage_degraded_sample(
                    profile
                )
            )

            state = "AFFECTED"

        else:
            sample = (
                healthy_sample()
            )

            state = "HEALTHY"

        send_telemetry(
            device["device_id"],
            sample,
        )

        print(
            f"{device['device_id']} | "
            f"{device['model']:<16} | "
            f"{state}"
        )

        time.sleep(
            0.03
        )


# ==========================================================
# Main
# ==========================================================


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Guardian X multi-device "
            "population simulator"
        )
    )

    parser.add_argument(
        "--mode",
        choices=[
            "network",
            "device-model",
            "coverage",
            "interference",
            "outage",
        ],
        required=True,
    )

    parser.add_argument(
        "--count-per-model",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--profile",
        choices=[
            "mild",
            "moderate",
            "severe",
        ],
        default="moderate",
        help=(
            "Controlled synthetic scenario "
            "severity profile"
        ),
    )

    parser.add_argument(
        "--target-model",
        choices=[
            model["model"]
            for model in MODELS
        ],
        default="DemoPhone X1",
        help=(
            "Target device model for "
            "device-model scenario"
        ),
    )

    parser.add_argument(
        "--geo-anchor",
        choices=[
            "cycle",
            "a",
            "b",
            "c",
        ],
        default="cycle",
        help=(
            "Coverage geo placement. "
            "'cycle' rotates through "
            "validated historical anchors."
        ),
    )

    parser.add_argument(
        "--coverage-subtype",
        choices=[
            "generic",
            "terrain",
        ],
        default="generic",
        help=(
            "Coverage root-cause subtype. "
            "'generic' represents RF coverage/"
            "propagation degradation without "
            "terrain obstruction. "
            "'terrain' injects controlled "
            "synthetic terrain evidence."
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help=(
            "Optional random seed for "
            "reproducible synthetic telemetry"
        ),
    )

    args = parser.parse_args()

    profile = get_scenario_profile(
        args.profile
    )

    # ------------------------------------------------------
    # Reproducibility
    # ------------------------------------------------------
    #
    # When --seed is supplied, every random
    # value generated by this simulator
    # becomes deterministic for the same
    # execution path.
    #
    # This includes:
    #   - RSRP / RSRQ / RSSI
    #   - SINR
    #   - CQI / MCS
    #   - download / upload speed
    #   - latency / jitter
    #   - packet loss
    #   - telemetry latitude / longitude
    #
    # Without --seed, Python's normal
    # non-deterministic random initialization
    # is used.
    if args.seed is not None:
        random.seed(
            args.seed
        )

    total = (
        len(MODELS)
        * args.count_per_model
    )

    print("=" * 72)
    print("Guardian X Population Simulator")
    print("=" * 72)

    print(
        f"Cell            : {CELL_ID}"
    )

    print(
        f"Mode            : {args.mode}"
    )

    print(f"Profile         : {args.profile}")

    print(
        "Affected ratio : "
        f"{profile['affected_ratio']:.0%}"
    )

    if args.mode == "device-model":
        print(
            f"Target model     : "
            f"{args.target_model}"
        )

    if args.mode == "coverage":
        print(
            f"Geo anchor      : "
            f"{args.geo_anchor}"
        )

    print(
        f"Device models   : {len(MODELS)}"
    )

    print(
        f"Devices/model   : "
        f"{args.count_per_model}"
    )

    print(
        f"Total devices   : {total}"
    )

    if args.seed is None:
        print(
            "Random seed     : NONE"
        )
    else:
        print(
            f"Random seed     : "
            f"{args.seed}"
        )

    print("=" * 72)

    population = build_population(
        args.count_per_model
    )

    if args.mode == "network":
        run_network_test(
            population,
            profile,
            args.count_per_model,
        )

    elif args.mode == "device-model":
        run_device_model_test(
            population,
            profile,
            args.count_per_model,
            args.target_model,
        )

    elif args.mode == "coverage":
        run_coverage_test(
            population,
            profile,
            args.count_per_model,
            args.geo_anchor,
            args.coverage_subtype,
        )

    elif args.mode == "interference":
        run_interference_test(
            population,
            profile,
            args.count_per_model,
        )

    elif args.mode == "outage":
        run_outage_test(
            population,
            profile,
            args.count_per_model,
        )

    print()
    print("=" * 72)
    print("Telemetry generation complete")
    print("Run:")
    print(
        f"GET /api/v1/correlation/cell/"
        f"{CELL_ID}?window_minutes=10"
    )
    print("=" * 72)


if __name__ == "__main__":
    main()