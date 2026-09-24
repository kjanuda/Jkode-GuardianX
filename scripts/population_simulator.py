import argparse
import random
import time

import requests


API_BASE = "http://127.0.0.1:8000"

CELL_ID = "GX-CELL-001"

BASE_LATITUDE = 7.2800
BASE_LONGITUDE = 80.6600


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


def network_degraded_sample():
    """
    Healthy-ish radio +
    poor network KPIs.

    This looks more like congestion /
    backhaul degradation than simple
    coverage loss.
    """

    rsrp = random.uniform(
        -94,
        -82,
    )

    return {
        "scenario": "population_network",
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
        "dl_speed_mbps": round(
            random.uniform(
                3,
                13,
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
                90,
                180,
            ),
            2,
        ),
        "jitter_ms": round(
            random.uniform(
                15,
                45,
            ),
            2,
        ),
        "packet_loss_pct": round(
            random.uniform(
                2.5,
                6,
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


def coverage_degraded_sample():
    """
    Population-wide coverage /
    propagation degradation.

    Strongly degraded radio KPIs:
        RSRP  -> very weak
        RSRQ  -> poor
        SINR  -> poor

    Network KPIs also degrade as a
    consequence of weak radio quality.
    """

    rsrp = random.uniform(
        -121,
        -111,
    )

    return {
        "scenario": "population_coverage",
        "rsrp": round(
            rsrp,
            2,
        ),
        "rsrq": round(
            random.uniform(
                -19,
                -14,
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
                -3,
                5,
            ),
            2,
        ),
        "cqi": random.randint(
            1,
            6,
        ),
        "mcs": random.randint(
            2,
            10,
        ),
        "dl_speed_mbps": round(
            random.uniform(
                2,
                12,
            ),
            2,
        ),
        "up_speed_mbps": round(
            random.uniform(
                1,
                5,
            ),
            2,
        ),
        "latency_ms": round(
            random.uniform(
                90,
                180,
            ),
            2,
        ),
        "jitter_ms": round(
            random.uniform(
                15,
                45,
            ),
            2,
        ),
        "packet_loss_pct": round(
            random.uniform(
                2.5,
                8,
            ),
            2,
        ),
    }


# ==========================================================
# Population-wide interference degradation
# ==========================================================


def interference_degraded_sample():
    """
    Usable signal strength but poor radio quality.

    Designed to represent interference rather than
    simple weak-coverage propagation loss.
    """

    rsrp = random.uniform(
        -98,
        -84,
    )

    return {
        "scenario": "population_interference",

        "rsrp": round(
            rsrp,
            2,
        ),

        "rsrq": round(
            random.uniform(
                -20,
                -15,
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
                -4,
                5,
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
                8,
                25,
            ),
            2,
        ),

        "up_speed_mbps": round(
            random.uniform(
                3,
                10,
            ),
            2,
        ),

        "latency_ms": round(
            random.uniform(
                50,
                110,
            ),
            2,
        ),

        "jitter_ms": round(
            random.uniform(
                10,
                30,
            ),
            2,
        ),

        "packet_loss_pct": round(
            random.uniform(
                1,
                4,
            ),
            2,
        ),
    }


# ==========================================================
# Population-wide outage degradation
# ==========================================================


def outage_degraded_sample():
    """
    Healthy-ish radio conditions but near-total
    service failure.

    Designed to produce an outage/network failure
    signature rather than propagation degradation.

    Radio KPIs are intentionally kept healthy
    (RSRP -94..-82, RSRQ -11..-7, SINR 14..23)
    so this scenario is not mistaken for a
    coverage or interference problem.
    """

    rsrp = random.uniform(
        -94,
        -82,
    )

    return {
        "scenario": "population_outage",

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
                0.02,
                0.40,
            ),
            2,
        ),

        "up_speed_mbps": round(
            random.uniform(
                0.01,
                0.20,
            ),
            2,
        ),

        "latency_ms": round(
            random.uniform(
                400,
                900,
            ),
            2,
        ),

        "jitter_ms": round(
            random.uniform(
                100,
                300,
            ),
            2,
        ),

        "packet_loss_pct": round(
            random.uniform(
                70,
                95,
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
):
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
):
    print()
    print("NETWORK-WIDE TEST")
    print("-" * 72)

    # Around 80% of every model cohort
    # becomes degraded.
    for device in population:
        affected = (
            device["model_index"] < 8
        )

        if affected:
            sample = (
                network_degraded_sample()
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
):
    print()
    print("DEVICE-MODEL TEST")
    print("-" * 72)

    target_model = "DemoPhone X1"

    for device in population:
        is_target = (
            device["model"]
            == target_model
        )

        # 90% of DemoPhone X1 fails.
        if (
            is_target
            and device["model_index"] < 9
        ):
            sample = (
                device_model_fault_sample()
            )
            state = "AFFECTED"

        # Small background failure in
        # non-target control cohorts.
        elif (
            not is_target
            and device["model_index"] == 0
        ):
            sample = (
                network_degraded_sample()
            )
            state = "BACKGROUND_AFFECTED"

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
):
    print()
    print("POPULATION COVERAGE TEST")
    print("-" * 72)

    # Around 80% of every model cohort
    # experiences the same coverage /
    # propagation degradation.
    #
    # The remaining devices act as
    # healthy controls.
    for device in population:
        affected = (
            device["model_index"] < 8
        )

        if affected:
            sample = (
                coverage_degraded_sample()
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
# Interference population test
# ==========================================================


def run_interference_test(
    population: list[dict],
):
    print()
    print(
        "POPULATION INTERFERENCE TEST"
    )

    print(
        "-" * 72
    )

    # 80% of every model cohort is affected.
    for device in population:
        affected = (
            device["model_index"] < 8
        )

        if affected:
            sample = (
                interference_degraded_sample()
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
):
    print()
    print(
        "POPULATION OUTAGE TEST"
    )

    print(
        "-" * 72
    )

    # 80% of every model cohort is affected.
    for device in population:
        affected = (
            device["model_index"] < 8
        )

        if affected:
            sample = (
                outage_degraded_sample()
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
        "--seed",
        type=int,
        default=None,
        help=(
            "Optional random seed for "
            "reproducible synthetic telemetry"
        ),
    )

    args = parser.parse_args()

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
            population
        )

    elif args.mode == "device-model":
        run_device_model_test(
            population
        )

    elif args.mode == "coverage":
        run_coverage_test(
            population
        )

    elif args.mode == "interference":
        run_interference_test(
            population
        )

    elif args.mode == "outage":
        run_outage_test(
            population
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