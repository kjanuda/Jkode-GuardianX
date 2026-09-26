"use client";

import Link from "next/link";

import {
  Activity,
  AlertTriangle,
  BrainCircuit,
  MapPin,
  RadioTower,
  Smartphone,
  Wrench,
  X,
} from "lucide-react";

import type {
  GuardianMapPayload,
  GuardianMapPoint,
} from "@/types/map";


interface Props {
  point: GuardianMapPoint;
  data: GuardianMapPayload;
  onClose: () => void;
}


function Metric({
  label,
  value,
}: {
  label: string;
  value:
    | string
    | number
    | null
    | undefined;
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/15 p-3">
      <p className="text-[10px] uppercase tracking-wider text-white/30">
        {label}
      </p>

      <p className="mt-2 break-words text-xs text-white/70">
        {value ?? "—"}
      </p>
    </div>
  );
}


export default function MapDetailPanel({
  point,
  data,
  onClose,
}: Props) {
  const tower =
    point.point_type === "TOWER"
      ? data.towers.find(
          (item) =>
            item.tower_code ===
            point.id
        ) ?? null
      : null;

  const cell =
    point.point_type === "CELL"
      ? data.cells.find(
          (item) =>
            item.cell_id ===
            point.id
        ) ?? null
      : null;

  const device =
    point.point_type === "DEVICE"
      ? data.devices.find(
          (item) =>
            item.device_id ===
            point.id
        ) ?? null
      : null;

  return (
    <aside className="w-full rounded-2xl border border-white/10 bg-[#080d17] p-5 xl:w-[390px]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[10px] uppercase tracking-[0.15em] text-cyan-300/60">
            Selected {point.point_type}
          </p>

          <h2 className="mt-2 break-words text-base font-medium text-white">
            {point.id}
          </h2>

          <p className="mt-1 text-xs text-white/35">
            {point.latitude.toFixed(6)},{" "}
            {point.longitude.toFixed(6)}
          </p>
        </div>

        <button
          type="button"
          onClick={onClose}
          className="rounded-lg border border-white/10 bg-white/5 p-2 text-white/40 transition hover:text-white"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {tower ? (
        <div className="mt-6 space-y-4">
          <div className="flex items-center gap-2 text-xs text-cyan-300">
            <RadioTower className="h-4 w-4" />
            Tower Context
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Metric
              label="Name"
              value={tower.name}
            />

            <Metric
              label="Status"
              value={tower.status}
            />

            <Metric
              label="Elevation"
              value={
                tower.elevation_m !== null
                  ? `${tower.elevation_m} m`
                  : null
              }
            />

            <Metric
              label="Coordinates"
              value={tower.coordinate_source}
            />
          </div>
        </div>
      ) : null}

      {cell ? (
        <div className="mt-6 space-y-5">
          <div className="flex items-center gap-2 text-xs text-violet-300">
            <RadioTower className="h-4 w-4" />
            Cell Intelligence
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Metric
              label="Technology"
              value={cell.technology}
            />

            <Metric
              label="Band"
              value={cell.band}
            />

            <Metric
              label="PCI"
              value={cell.pci}
            />

            <Metric
              label="EARFCN"
              value={cell.earfcn}
            />

            <Metric
              label="Bandwidth"
              value={
                cell.bandwidth_mhz !== null
                  ? `${cell.bandwidth_mhz} MHz`
                  : null
              }
            />

            <Metric
              label="Azimuth"
              value={
                cell.sector?.azimuth_deg !==
                null
                  ? `${cell.sector?.azimuth_deg}°`
                  : null
              }
            />
          </div>

          {cell.rca ? (
            <div className="rounded-xl border border-violet-400/10 bg-violet-400/[0.04] p-4">
              <div className="flex items-center gap-2">
                <BrainCircuit className="h-4 w-4 text-violet-300" />

                <p className="text-xs font-medium text-white">
                  RCA Context
                </p>
              </div>

              <p className="mt-3 break-words text-xs text-white/65">
                {cell.rca.primary_cause}
              </p>

              <p className="mt-1 text-[11px] text-white/35">
                Confidence:{" "}
                {cell.rca.confidence !== null
                  ? `${(
                      cell.rca.confidence *
                      100
                    ).toFixed(2)}%`
                  : "—"}
              </p>

              <Link
                href={`/rca/${cell.rca.case_id}`}
                className="mt-3 inline-block text-[11px] text-cyan-300"
              >
                Open RCA case →
              </Link>
            </div>
          ) : null}

          {cell.action ? (
            <div className="rounded-xl border border-emerald-400/10 bg-emerald-400/[0.04] p-4">
              <div className="flex items-center gap-2">
                <Wrench className="h-4 w-4 text-emerald-300" />

                <p className="text-xs font-medium text-white">
                  Action State
                </p>
              </div>

              <p className="mt-3 text-xs text-white/65">
                {cell.action.action_code}
              </p>

              <p className="mt-1 text-[11px] text-white/35">
                {cell.action.status} ·{" "}
                {cell.action.execution_mode}
              </p>

              <Link
                href={`/actions/${cell.action.id}`}
                className="mt-3 inline-block text-[11px] text-cyan-300"
              >
                Open action plan →
              </Link>
            </div>
          ) : null}
        </div>
      ) : null}

      {device ? (
        <div className="mt-6 space-y-5">
          <div className="flex items-center gap-2 text-xs text-emerald-300">
            <Smartphone className="h-4 w-4" />
            Device Intelligence
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Metric
              label="Model"
              value={device.model}
            />

            <Metric
              label="Manufacturer"
              value={device.manufacturer}
            />

            <Metric
              label="Status"
              value={device.status}
            />

            <Metric
              label="Serving Cell"
              value={
                device.serving_cell?.cell_id
              }
            />
          </div>

          {device.latest_telemetry ? (
            <div>
              <div className="mb-3 flex items-center gap-2">
                <Activity className="h-4 w-4 text-cyan-300" />

                <p className="text-xs font-medium text-white">
                  Latest Telemetry
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Metric
                  label="RSRP"
                  value={
                    device.latest_telemetry.rsrp !==
                    null
                      ? `${device.latest_telemetry.rsrp} dBm`
                      : null
                  }
                />

                <Metric
                  label="RSRQ"
                  value={
                    device.latest_telemetry.rsrq !==
                    null
                      ? `${device.latest_telemetry.rsrq} dB`
                      : null
                  }
                />

                <Metric
                  label="SINR"
                  value={
                    device.latest_telemetry.sinr !==
                    null
                      ? `${device.latest_telemetry.sinr} dB`
                      : null
                  }
                />

                <Metric
                  label="Latency"
                  value={
                    device.latest_telemetry.latency_ms !==
                    null
                      ? `${device.latest_telemetry.latency_ms} ms`
                      : null
                  }
                />

                <Metric
                  label="Download"
                  value={
                    device.latest_telemetry.download_mbps !==
                    null
                      ? `${device.latest_telemetry.download_mbps} Mbps`
                      : null
                  }
                />

                <Metric
                  label="Packet Loss"
                  value={
                    device.latest_telemetry.packet_loss !==
                    null
                      ? `${device.latest_telemetry.packet_loss}%`
                      : null
                  }
                />
              </div>
            </div>
          ) : null}

          {device.active_alert ? (
            <div className="rounded-xl border border-red-400/15 bg-red-400/[0.05] p-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-red-300" />

                <p className="text-xs font-medium text-red-200">
                  Active Alert
                </p>
              </div>

              <p className="mt-3 text-xs text-white/65">
                {device.active_alert.title}
              </p>

              <p className="mt-1 text-[11px] text-white/35">
                Risk{" "}
                {device.active_alert.risk_score.toFixed(
                  2
                )}{" "}
                ·{" "}
                {device.active_alert.severity}
              </p>

              <p className="mt-2 break-words text-[11px] text-white/45">
                {
                  device.active_alert
                    .primary_cause
                }
              </p>

              <Link
                href="/alerts"
                className="mt-3 inline-block text-[11px] text-red-300"
              >
                Open alerts →
              </Link>
            </div>
          ) : null}

          {device.serving_cell_rca ? (
            <Link
              href={`/rca/${device.serving_cell_rca.case_id}`}
              className="block rounded-xl border border-violet-400/10 bg-violet-400/[0.04] p-4"
            >
              <div className="flex items-center gap-2">
                <BrainCircuit className="h-4 w-4 text-violet-300" />

                <p className="text-xs text-white/65">
                  {
                    device
                      .serving_cell_rca
                      .primary_cause
                  }
                </p>
              </div>
            </Link>
          ) : null}
        </div>
      ) : null}

      <div className="mt-6 flex items-start gap-2 rounded-xl border border-white/10 bg-black/10 p-3">
        <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0 text-white/30" />

        <p className="text-[10px] leading-5 text-white/30">
          Location source:{" "}
          {tower?.coordinate_source ??
            cell?.coordinate_source ??
            device?.coordinate_source ??
            "UNKNOWN"}
        </p>
      </div>
    </aside>
  );
}
