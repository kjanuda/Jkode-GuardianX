import {
  AlertTriangle,
  CheckCircle2,
  Siren,
} from "lucide-react";

import AlertCard from "@/components/alerts/AlertCard";
import RetryButton from "@/components/layout/RetryButton";
import SectionPage from "@/components/layout/SectionPage";

import {
  getActiveAlerts,
  getAlertHistory,
} from "@/lib/api";

import type {
  GuardianAlertCollection,
} from "@/types/guardian";


async function loadAlertData() {
  const [
    activeResult,
    historyResult,
  ] = await Promise.allSettled([
    getActiveAlerts(),
    getAlertHistory(),
  ]);

  return {
    active:
      activeResult.status ===
      "fulfilled"
        ? activeResult.value
        : null,

    history:
      historyResult.status ===
      "fulfilled"
        ? historyResult.value
        : null,
  };
}


function ErrorPanel({
  title,
  retryLabel,
}: {
  title: string;
  retryLabel: string;
}) {
  return (
    <div className="rounded-xl border border-red-400/15 bg-red-400/5 p-4">
      <div className="flex items-center gap-2 text-xs text-red-300">
        <AlertTriangle className="h-4 w-4" />
        {title}
      </div>

      <p className="mt-2 text-xs leading-5 text-white/35">
        This section could not be loaded from the Guardian X API.
      </p>

      <div className="mt-4">
        <RetryButton
          label={retryLabel}
        />
      </div>
    </div>
  );
}


function HistoryTable({
  history,
}: {
  history: GuardianAlertCollection;
}) {
  if (
    history.items.length === 0
  ) {
    return (
      <div className="rounded-xl border border-white/10 bg-black/10 p-5 text-sm text-white/35">
        No historical alerts available.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-white/10">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[900px] text-left">
          <thead>
            <tr className="border-b border-white/10 bg-white/[0.025] text-[10px] uppercase tracking-[0.14em] text-white/30">
              <th className="px-4 py-3 font-medium">
                Alert
              </th>

              <th className="px-4 py-3 font-medium">
                Device
              </th>

              <th className="px-4 py-3 font-medium">
                Status
              </th>

              <th className="px-4 py-3 font-medium">
                Severity
              </th>

              <th className="px-4 py-3 font-medium">
                Root Cause
              </th>

              <th className="px-4 py-3 font-medium">
                Risk
              </th>

              <th className="px-4 py-3 font-medium">
                Occurrences
              </th>

              <th className="px-4 py-3 font-medium">
                Resolved
              </th>
            </tr>
          </thead>

          <tbody>
            {history.items.map(
              (alert) => (
                <tr
                  key={alert.id}
                  className="border-b border-white/5 text-xs last:border-0"
                >
                  <td className="px-4 py-4 text-white/70">
                    #{alert.id}
                  </td>

                  <td className="px-4 py-4 text-white/55">
                    {alert.device_id}
                  </td>

                  <td className="px-4 py-4">
                    <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] text-white/55">
                      {alert.status}
                    </span>
                  </td>

                  <td className="px-4 py-4 text-red-300">
                    {alert.severity}
                  </td>

                  <td className="max-w-[240px] truncate px-4 py-4 text-white/55">
                    {alert.primary_cause}
                  </td>

                  <td className="px-4 py-4 font-medium text-white/70">
                    {alert.risk_score.toFixed(
                      2
                    )}
                  </td>

                  <td className="px-4 py-4 text-white/55">
                    {alert.occurrence_count}
                  </td>

                  <td className="px-4 py-4 text-white/40">
                    {alert.resolved_at
                      ? "Yes"
                      : "—"}
                  </td>
                </tr>
              )
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}


export default async function AlertsPage() {
  const {
    active,
    history,
  } = await loadAlertData();

  return (
    <SectionPage
      eyebrow="Operations"
      title="Alerts"
      description="Live Guardian X alert lifecycle with severity, device context, risk score and evidence-derived root cause."
      icon={Siren}
    >
      <div className="space-y-8">
        <section>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-medium text-white">
                Active Alerts
              </h2>

              <p className="mt-1 text-xs text-white/35">
                Open operational incidents requiring attention
              </p>
            </div>

            {active ? (
              <span className="rounded-full border border-red-400/15 bg-red-400/5 px-3 py-1 text-[11px] text-red-300">
                {active.count} active
              </span>
            ) : null}
          </div>

          {!active ? (
            <ErrorPanel
              title="Active alerts unavailable"
              retryLabel="Retry active alerts"
            />
          ) : active.items.length ===
            0 ? (
            <div className="flex items-center gap-3 rounded-xl border border-emerald-400/15 bg-emerald-400/5 p-5">
              <CheckCircle2 className="h-5 w-5 text-emerald-300" />

              <div>
                <p className="text-sm text-emerald-200">
                  No active alerts
                </p>

                <p className="mt-1 text-xs text-white/35">
                  Guardian X currently reports no active network incidents.
                </p>
              </div>
            </div>
          ) : (
            <div className="grid gap-4">
              {active.items.map(
                (alert) => (
                  <AlertCard
                    key={alert.id}
                    alert={alert}
                  />
                )
              )}
            </div>
          )}
        </section>

        <section>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-medium text-white">
                Alert History
              </h2>

              <p className="mt-1 text-xs text-white/35">
                Current and previously resolved alert records
              </p>
            </div>

            {history ? (
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] text-white/40">
                {history.count} records
              </span>
            ) : null}
          </div>

          {!history ? (
            <ErrorPanel
              title="Alert history unavailable"
              retryLabel="Retry alert history"
            />
          ) : (
            <HistoryTable
              history={history}
            />
          )}
        </section>
      </div>
    </SectionPage>
  );
}
