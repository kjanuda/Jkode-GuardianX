import Link from "next/link";

import {
  Activity,
  Clock3,
  RadioTower,
  ShieldAlert,
} from "lucide-react";

import type {
  GuardianAlert,
} from "@/types/guardian";


interface AlertCardProps {
  alert: GuardianAlert;
}


function formatDate(
  value: string | null
) {
  if (!value) {
    return "—";
  }

  return new Date(
    value
  ).toLocaleString(
    "en-LK",
    {
      dateStyle: "medium",
      timeStyle: "short",
    }
  );
}


function statusClass(
  status: string
) {
  if (
    status === "REOPENED"
  ) {
    return "border-amber-400/20 bg-amber-400/10 text-amber-300";
  }

  if (
    status === "RESOLVED"
  ) {
    return "border-emerald-400/20 bg-emerald-400/10 text-emerald-300";
  }

  if (
    status === "MITIGATING"
  ) {
    return "border-violet-400/20 bg-violet-400/10 text-violet-300";
  }

  return "border-red-400/20 bg-red-400/10 text-red-300";
}


export default function AlertCard({
  alert,
}: AlertCardProps) {
  return (
    <article className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-red-400/15 bg-red-400/[0.07]">
            <ShieldAlert className="h-5 w-5 text-red-300" />
          </div>

          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-white/30">
                ALERT #{alert.id}
              </span>

              <span
                className={[
                  "rounded-full border px-2.5 py-1 text-[10px]",
                  statusClass(
                    alert.status
                  ),
                ].join(" ")}
              >
                {alert.status}
              </span>

              <span className="rounded-full border border-red-400/20 bg-red-400/10 px-2.5 py-1 text-[10px] text-red-300">
                {alert.severity}
              </span>
            </div>

            <h2 className="mt-3 truncate text-sm font-medium text-white">
              {alert.title}
            </h2>

            <p className="mt-1 text-xs text-white/35">
              {alert.primary_cause}
            </p>
          </div>
        </div>

        <div className="shrink-0 text-left sm:text-right">
          <div className="text-[10px] uppercase tracking-[0.14em] text-white/30">
            Risk score
          </div>

          <div className="mt-1 text-2xl font-semibold text-white">
            {alert.risk_score.toFixed(
              2
            )}
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-xl border border-white/5 bg-black/20 p-3">
          <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-white/30">
            <RadioTower className="h-3.5 w-3.5" />
            Device
          </div>

          <p className="mt-2 text-xs text-white/70">
            {alert.device_id}
          </p>
        </div>

        <div className="rounded-xl border border-white/5 bg-black/20 p-3">
          <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-white/30">
            <Activity className="h-3.5 w-3.5" />
            Occurrences
          </div>

          <p className="mt-2 text-xs text-white/70">
            {alert.occurrence_count}
          </p>
        </div>

        <div className="rounded-xl border border-white/5 bg-black/20 p-3">
          <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-white/30">
            <Clock3 className="h-3.5 w-3.5" />
            First seen
          </div>

          <p className="mt-2 text-xs text-white/70">
            {formatDate(
              alert.first_seen_at
            )}
          </p>
        </div>

        <div className="rounded-xl border border-white/5 bg-black/20 p-3">
          <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-white/30">
            <Clock3 className="h-3.5 w-3.5" />
            Last seen
          </div>

          <p className="mt-2 text-xs text-white/70">
            {formatDate(
              alert.last_seen_at
            )}
          </p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Link
          href="/rca"
          className="rounded-lg border border-cyan-400/15 bg-cyan-400/5 px-3 py-2 text-[11px] text-cyan-300 transition hover:bg-cyan-400/10"
        >
          View RCA Intelligence
        </Link>

        <Link
          href="/map"
          className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-[11px] text-white/50 transition hover:text-white"
        >
          Locate Device
        </Link>
      </div>
    </article>
  );
}
