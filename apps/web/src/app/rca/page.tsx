import Link from "next/link";

import {
  BrainCircuit,
  ChevronRight,
  ShieldCheck,
} from "lucide-react";

import RetryButton from "@/components/layout/RetryButton";
import SectionPage from "@/components/layout/SectionPage";
import StatusBadge from "@/components/rca/StatusBadge";

import {
  getDashboardIncidents,
} from "@/lib/api";


export default async function RCAPage() {
  const result =
    await Promise.allSettled([
      getDashboardIncidents(
        25
      ),
    ]);

  const incidents =
    result[0].status ===
    "fulfilled"
      ? result[0].value
      : null;

  return (
    <SectionPage
      eyebrow="Evidence Intelligence"
      title="Root Cause Analysis"
      description="Deterministic RCA remains authoritative. ML and LLM signals are displayed as supporting evidence and are subject to verification."
      icon={BrainCircuit}
    >
      {!incidents ? (
        <div className="rounded-xl border border-red-400/15 bg-red-400/5 p-5">
          <p className="text-sm text-red-200">
            RCA incident data is currently unavailable.
          </p>

          <p className="mt-2 text-xs text-white/35">
            Guardian X could not load recent RCA cases from the backend.
          </p>

          <div className="mt-4">
            <RetryButton
              label="Retry RCA data"
            />
          </div>
        </div>
      ) : incidents.items.length === 0 ? (
        <div className="rounded-xl border border-white/10 bg-black/10 p-6">
          <p className="text-sm text-white/60">
            No RCA cases available.
          </p>

          <p className="mt-2 text-xs text-white/30">
            RCA cases will appear after Guardian X creates evidence-backed diagnostic records.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-medium text-white">
                Recent RCA Cases
              </h2>

              <p className="mt-1 text-xs text-white/35">
                Select a case to inspect evidence and verifier history.
              </p>
            </div>

            <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] text-white/40">
              {incidents.count} shown
            </span>
          </div>

          <div className="overflow-hidden rounded-2xl border border-white/10">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[900px] text-left">
                <thead>
                  <tr className="border-b border-white/10 bg-white/[0.025] text-[10px] uppercase tracking-[0.14em] text-white/30">
                    <th className="px-4 py-3 font-medium">
                      Case
                    </th>

                    <th className="px-4 py-3 font-medium">
                      Scope
                    </th>

                    <th className="px-4 py-3 font-medium">
                      Diagnosis
                    </th>

                    <th className="px-4 py-3 font-medium">
                      Confidence
                    </th>

                    <th className="px-4 py-3 font-medium">
                      Verifier
                    </th>

                    <th className="px-4 py-3 font-medium">
                      Action
                    </th>

                    <th className="px-4 py-3 font-medium" />
                  </tr>
                </thead>

                <tbody>
                  {incidents.items.map(
                    (incident) => (
                      <tr
                        key={
                          incident.case.id
                        }
                        className="border-b border-white/5 text-xs last:border-0"
                      >
                        <td className="px-4 py-4">
                          <div className="font-medium text-white/75">
                            RCA-
                            {
                              incident.case.id
                            }
                          </div>

                          <div className="mt-1 text-[10px] text-white/25">
                            {
                              incident.case
                                .trigger_type
                            }
                          </div>
                        </td>

                        <td className="px-4 py-4 text-white/55">
                          {
                            incident.case
                              .scope_ref
                          }
                        </td>

                        <td className="max-w-[260px] truncate px-4 py-4 text-white/65">
                          {
                            incident
                              .diagnosis
                              .primary_cause
                          }
                        </td>

                        <td className="px-4 py-4 text-white/60">
                          {incident
                            .diagnosis
                            .confidence ===
                          null
                            ? "—"
                            : `${Math.round(
                                incident
                                  .diagnosis
                                  .confidence *
                                  100
                              )}%`}
                        </td>

                        <td className="px-4 py-4">
                          <StatusBadge
                            value={
                              incident
                                .diagnosis
                                .verifier_status
                            }
                          />
                        </td>

                        <td className="px-4 py-4">
                          {incident.action ? (
                            <StatusBadge
                              value={
                                incident
                                  .action
                                  .status
                              }
                            />
                          ) : (
                            <span className="text-white/25">
                              —
                            </span>
                          )}
                        </td>

                        <td className="px-4 py-4">
                          <Link
                            href={`/rca/${incident.case.id}`}
                            className="inline-flex items-center gap-1 text-cyan-300/70 transition hover:text-cyan-200"
                          >
                            Inspect
                            <ChevronRight className="h-3.5 w-3.5" />
                          </Link>
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex items-start gap-3 rounded-xl border border-emerald-400/15 bg-emerald-400/5 p-4">
            <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300" />

            <p className="text-xs leading-5 text-white/40">
              Guardian X does not treat an LLM proposal as a final root cause.
              Structured deterministic verification remains authoritative.
            </p>
          </div>
        </div>
      )}
    </SectionPage>
  );
}
