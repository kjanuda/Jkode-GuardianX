import Link from "next/link";

import {
  ChevronRight,
  ShieldCheck,
  Wrench,
} from "lucide-react";

import ActionStatusBadge from "@/components/actions/ActionStatusBadge";
import RetryButton from "@/components/layout/RetryButton";
import SectionPage from "@/components/layout/SectionPage";

import {
  getDashboardIncidents,
} from "@/lib/api";


export default async function ActionsPage() {
  const result =
    await Promise.allSettled([
      getDashboardIncidents(
        100
      ),
    ]);

  const incidents =
    result[0].status ===
    "fulfilled"
      ? result[0].value
      : null;

  const actionItems =
    incidents
      ? incidents.items.filter(
          (item) =>
            item.action !== null
        )
      : [];

  const blockedCount =
    actionItems.filter(
      (item) =>
        item.action?.status ===
        "BLOCKED"
    ).length;

  const verifiedCount =
    actionItems.filter(
      (item) =>
        item.action?.status ===
        "VERIFIED_SUCCESS"
    ).length;

  return (
    <SectionPage
      eyebrow="Guarded Remediation"
      title="Action Plans"
      description="Verified RCA findings are translated into guarded advisory plans. Real telecom execution remains disabled."
      icon={Wrench}
    >
      {!incidents ? (
        <div className="rounded-xl border border-red-400/15 bg-red-400/5 p-5">
          <p className="text-sm text-red-200">
            Action data unavailable
          </p>

          <p className="mt-2 text-xs text-white/35">
            Guardian X could not load the incident/action chain.
          </p>

          <div className="mt-4">
            <RetryButton label="Retry action data" />
          </div>
        </div>
      ) : actionItems.length ===
        0 ? (
        <div className="rounded-xl border border-white/10 bg-black/10 p-6">
          <p className="text-sm text-white/60">
            No action plans available.
          </p>

          <p className="mt-2 text-xs text-white/30">
            A plan will appear after an RCA case passes the required planning gates.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          <section className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-white/10 bg-black/15 p-4">
              <p className="text-[10px] uppercase tracking-wider text-white/30">
                Total Plans
              </p>

              <p className="mt-2 text-2xl font-semibold text-white">
                {
                  actionItems.length
                }
              </p>
            </div>

            <div className="rounded-xl border border-emerald-400/10 bg-emerald-400/[0.04] p-4">
              <p className="text-[10px] uppercase tracking-wider text-emerald-300/60">
                Verified Success
              </p>

              <p className="mt-2 text-2xl font-semibold text-white">
                {
                  verifiedCount
                }
              </p>
            </div>

            <div className="rounded-xl border border-red-400/10 bg-red-400/[0.04] p-4">
              <p className="text-[10px] uppercase tracking-wider text-red-300/60">
                Blocked
              </p>

              <p className="mt-2 text-2xl font-semibold text-white">
                {
                  blockedCount
                }
              </p>
            </div>
          </section>

          <section className="overflow-hidden rounded-2xl border border-white/10">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[1000px] text-left">
                <thead>
                  <tr className="border-b border-white/10 bg-white/[0.025] text-[10px] uppercase tracking-wider text-white/30">
                    <th className="px-4 py-3 font-medium">
                      Plan
                    </th>

                    <th className="px-4 py-3 font-medium">
                      RCA
                    </th>

                    <th className="px-4 py-3 font-medium">
                      Action
                    </th>

                    <th className="px-4 py-3 font-medium">
                      Target
                    </th>

                    <th className="px-4 py-3 font-medium">
                      Safety Gate
                    </th>

                    <th className="px-4 py-3 font-medium">
                      Lifecycle
                    </th>

                    <th className="px-4 py-3 font-medium">
                      Mode
                    </th>

                    <th className="px-4 py-3 font-medium" />
                  </tr>
                </thead>

                <tbody>
                  {actionItems.map(
                    (item) => {
                      const action =
                        item.action;

                      if (!action) {
                        return null;
                      }

                      return (
                        <tr
                          key={
                            action.id
                          }
                          className="border-b border-white/5 text-xs last:border-0"
                        >
                          <td className="px-4 py-4 font-medium text-white/75">
                            PLAN-
                            {
                              action.id
                            }
                          </td>

                          <td className="px-4 py-4">
                            <Link
                              href={`/rca/${item.case.id}`}
                              className="text-cyan-300/70 hover:text-cyan-200"
                            >
                              RCA-
                              {
                                item.case.id
                              }
                            </Link>
                          </td>

                          <td className="max-w-[280px] px-4 py-4">
                            <p className="truncate text-white/65">
                              {
                                action.title
                              }
                            </p>

                            <p className="mt-1 text-[10px] text-white/30">
                              {
                                action.action_code
                              }
                            </p>
                          </td>

                          <td className="px-4 py-4 text-white/55">
                            {
                              action.target_ref ??
                              "—"
                            }
                          </td>

                          <td className="px-4 py-4">
                            <ActionStatusBadge
                              value={
                                action.safety_gate_status
                              }
                            />
                          </td>

                          <td className="px-4 py-4">
                            <ActionStatusBadge
                              value={
                                action.status
                              }
                            />
                          </td>

                          <td className="px-4 py-4">
                            <ActionStatusBadge
                              value={
                                action.execution_mode
                              }
                            />
                          </td>

                          <td className="px-4 py-4">
                            <Link
                              href={`/actions/${action.id}`}
                              className="inline-flex items-center gap-1 text-cyan-300/70 hover:text-cyan-200"
                            >
                              Inspect

                              <ChevronRight className="h-3.5 w-3.5" />
                            </Link>
                          </td>
                        </tr>
                      );
                    }
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <div className="flex items-start gap-3 rounded-xl border border-emerald-400/15 bg-emerald-400/5 p-4">
            <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" />

            <p className="text-xs leading-5 text-white/40">
              Guardian X V1 is advisory only. No OSS, NMS, RAN or production network execution is exposed by this dashboard.
            </p>
          </div>
        </div>
      )}
    </SectionPage>
  );
}
