import argparse
import random
import time
from datetime import datetime, timezone

import requests


API_URL = "http://127.0.0.1:8000/api/v1/telemetry"

DEVICE_ID = "GX-DEVICE-001"
CELL_ID = "GX-CELL-001"

SEND_INTERVAL_SECONDS = 5

VALID_SCENARIOS = {
    "normal",
    "congestion",
    "interference",
    "coverage",
    "outage",
}


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def generate_normal():
    rsrp = random.gauss(-88, 4)
    rsrq = random.gauss(-9, 1.5)
    sinr = random.gauss(18, 3)

    download = random.uniform(45, 85)
    upload = random.uniform(12, 30)

    latency = random.uniform(20, 40)
    jitter = random.uniform(2, 7)
    packet_loss = random.uniform(0, 0.4)

    return (
        rsrp,
        rsrq,
        sinr,
        download,
        upload,
        latency,
        jitter,
        packet_loss,
    )


def generate_congestion():
    # Radio remains reasonably good,
    # but data-path performance becomes bad.
    rsrp = random.gauss(-88, 4)
    rsrq = random.gauss(-10, 2)
    sinr = random.gauss(16, 3)

    download = random.uniform(5, 20)
    upload = random.uniform(2, 8)

    latency = random.uniform(80, 160)
    jitter = random.uniform(15, 35)
    packet_loss = random.uniform(1, 4)

    return (
        rsrp,
        rsrq,
        sinr,
        download,
        upload,
        latency,
        jitter,
        packet_loss,
    )


def generate_interference():
    # Signal strength may be acceptable,
    # but quality drops due to interference.
    rsrp = random.gauss(-88, 5)
    rsrq = random.gauss(-16, 2)
    sinr = random.gauss(3, 3)

    download = random.uniform(8, 25)
    upload = random.uniform(3, 10)

    latency = random.uniform(60, 130)
    jitter = random.uniform(12, 30)
    packet_loss = random.uniform(1, 5)

    return (
        rsrp,
        rsrq,
        sinr,
        download,
        upload,
        latency,
        jitter,
        packet_loss,
    )


def generate_coverage():
    # Weak received signal + poor SINR.
    rsrp = random.gauss(-116, 5)
    rsrq = random.gauss(-17, 2)
    sinr = random.gauss(2, 3)

    download = random.uniform(2, 12)
    upload = random.uniform(1, 5)

    latency = random.uniform(90, 180)
    jitter = random.uniform(18, 40)
    packet_loss = random.uniform(2, 8)

    return (
        rsrp,
        rsrq,
        sinr,
        download,
        upload,
        latency,
        jitter,
        packet_loss,
    )


def generate_outage():
    rsrp = random.gauss(-130, 3)
    rsrq = random.gauss(-22, 2)
    sinr = random.gauss(-5, 2)

    download = random.uniform(0, 1)
    upload = random.uniform(0, 0.5)

    latency = random.uniform(200, 500)
    jitter = random.uniform(40, 100)
    packet_loss = random.uniform(50, 100)

    return (
        rsrp,
        rsrq,
        sinr,
        download,
        upload,
        latency,
        jitter,
        packet_loss,
    )


def calculate_radio_details(rsrp, sinr):
    rssi = clamp(
        rsrp + random.uniform(15, 28),
        -150,
        -20,
    )

    if sinr < 0:
        cqi = random.randint(0, 2)

    elif sinr < 5:
        cqi = random.randint(2, 5)

    elif sinr < 10:
        cqi = random.randint(5, 8)

    elif sinr < 18:
        cqi = random.randint(8, 12)

    else:
        cqi = random.randint(12, 15)

    mcs = int(
        clamp(
            cqi * 2 + random.uniform(-2, 2),
            0,
            31,
        )
    )

    return rssi, cqi, mcs


def generate_telemetry(scenario):
    if scenario == "normal":
        values = generate_normal()

    elif scenario == "congestion":
        values = generate_congestion()

    elif scenario == "interference":
        values = generate_interference()

    elif scenario == "coverage":
        values = generate_coverage()

    elif scenario == "outage":
        values = generate_outage()

    else:
        raise ValueError(
            f"Unknown scenario: {scenario}"
        )

    (
        rsrp,
        rsrq,
        sinr,
        download,
        upload,
        latency,
        jitter,
        packet_loss,
    ) = values

    rsrp = clamp(rsrp, -160, -20)
    rsrq = clamp(rsrq, -40, 0)
    sinr = clamp(sinr, -30, 60)

    rssi, cqi, mcs = calculate_radio_details(
        rsrp,
        sinr,
    )

    latitude = 7.2800 + random.uniform(
        -0.001,
        0.001,
    )

    longitude = 80.6600 + random.uniform(
        -0.001,
        0.001,
    )

    return {
        "device_id": DEVICE_ID,
        "cell_id": CELL_ID,
        "scenario": scenario,

        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "radio": {
            "rsrp": round(rsrp, 2),
            "rsrq": round(rsrq, 2),
            "rssi": round(rssi, 2),
            "sinr": round(sinr, 2),
            "cqi": cqi,
            "mcs": mcs,
        },

        "network": {
            "download_mbps": round(
                download,
                2,
            ),
            "upload_mbps": round(
                upload,
                2,
            ),
            "latency_ms": round(
                latency,
                2,
            ),
            "jitter_ms": round(
                jitter,
                2,
            ),
            "packet_loss": round(
                packet_loss,
                2,
            ),
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


def send_telemetry(scenario):
    payload = generate_telemetry(
        scenario
    )

    try:
        response = requests.post(
            API_URL,
            json=payload,
            timeout=5,
        )

        if response.status_code == 201:
            result = response.json()

            print(
                f"[{scenario.upper():12}] "
                f"ID={result['id']} | "
                f"RSRP={payload['radio']['rsrp']:7} | "
                f"RSRQ={payload['radio']['rsrq']:6} | "
                f"SINR={payload['radio']['sinr']:6} | "
                f"DL={payload['network']['download_mbps']:6} Mbps | "
                f"LAT={payload['network']['latency_ms']:6} ms | "
                f"LOSS={payload['network']['packet_loss']}%"
            )

        else:
            print(
                f"[FAILED] "
                f"HTTP {response.status_code}"
            )

            print(
                response.text
            )

    except requests.RequestException as exc:
        print(
            "[ERROR] Could not connect "
            "to Guardian X API"
        )

        print(exc)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Guardian X scenario-based "
            "telemetry simulator"
        )
    )

    parser.add_argument(
        "--scenario",
        default="normal",
        choices=sorted(
            VALID_SCENARIOS
        ),
        help="Network scenario to simulate",
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=SEND_INTERVAL_SECONDS,
        help="Seconds between telemetry packets",
    )

    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help=(
            "Number of packets to send. "
            "0 means run continuously."
        ),
    )

    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 72)
    print(
        "Guardian X Scenario Telemetry Simulator"
    )
    print("=" * 72)

    print(
        f"Device       : {DEVICE_ID}"
    )

    print(
        f"Cell         : {CELL_ID}"
    )

    print(
        f"Scenario     : "
        f"{args.scenario.upper()}"
    )

    print(
        f"Interval     : "
        f"{args.interval} seconds"
    )

    print(
        f"Packet count : "
        f"{'continuous' if args.count == 0 else args.count}"
    )

    print("=" * 72)

    sent = 0

    try:
        while True:
            send_telemetry(
                args.scenario
            )

            sent += 1

            if (
                args.count > 0
                and sent >= args.count
            ):
                break

            time.sleep(
                args.interval
            )

    except KeyboardInterrupt:
        print()
        print(
            "Telemetry simulator stopped."
        )

    print(
        f"Packets sent: {sent}"
    )


if __name__ == "__main__":
    main()