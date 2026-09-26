import Link from "next/link";
import {
  ArrowLeft,
  BrainCircuit,
  Database,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
} from "lucide-react";

import SectionPage from "@/components/layout/SectionPage";
import StatusBadge from "@/components/rca/StatusBadge";

import {
  getDashboardIncidents,
  getRcaCaseBundle,
} from "@/lib/api";

import type {
  RcaPrediction,
} from "@/types/rca";


function confidence(
  value: number | null
) {
  if (value === null) {
    return "—";
  }

  return `${(
    value * 100
  ).toFixed(2)}%`;
}


function outputString(
  prediction: RcaPrediction | null,
  key: string
) {
  if (!prediction) {
    return null;
  }

  const value =
    prediction.output_json[
      key
    ];

  return typeof value ===
    "string"
    ? value
    : null;
}


export default async function RCACasePage({
  params,
}: {
  params: Promise<{
    caseId: string;
  }>;
}) {
  const {
    caseId,
  } = await params;

  const numericCaseId =
    Number(
      caseId
    );

  if (
    !Number.isInteger(
      numericCaseId
    ) ||
    numericCaseId < 1
  ) {
    return (
      <SectionPage
        eyebrow="Evidence Intelligence"
        title="Invalid RCA Case"
        description="The supplied RCA case identifier is invalid."
        icon={BrainCircuit}
      />
    );
  }

  const [
    bundleResult,
    incidentsResult,
  ] =
    await Promise.allSettled([
      getRcaCaseBundle(
        numericCaseId
      ),
      getDashboardIncidents(
        100
      ),
    ]);

  if (
    bundleResult.status !==
    "fulfilled"
  ) {
    return (
      <SectionPage
        eyebrow="Evidence Intelligence"
        title={`RCA-${numericCaseId}`}
        description="This RCA case could not be loaded from the Guardian X backend."
        icon={BrainCircuit}
      >
        <Link
          href="/rca"
          className="text-xs text-cyan-300"
        >
          ← Back to RCA cases
        </Link>
      </SectionPage>
    );
  }

  const bundle =
    bundleResult.value;

  const incident =
    incidentsResult.status ===
    "fulfilled"
      ? incidentsResult.value.items.find(
          (item) =>
            item.case.id ===
            numericCaseId
        ) ?? null
      : null;

  const structured =
    bundle.structured;

  const consensus =
    bundle.consensus;

  const acceptedAudits =
    bundle.llmAudits.filter(
      (prediction) =>
        prediction.verifier_status ===
        "ACCEPTED"
    );

  const rejectedAudits =
    bundle.llmAudits.filter(
      (prediction) =>
        prediction.verifier_status ===
        "REJECTED"
    );

  const actionGate =
    outputString(
      consensus,
      "action_gate"
    );

  const consensusStatus =
    outputString(
      consensus,
      "consensus_status"
    );

  return (
    <SectionPage
      eyebrow="Evidence Intelligence"
      title={`RCA-${numericCaseId}`}
      description="Evidence-first root cause trace with deterministic verification, fusion ranking, LLM audit records and action linkage."
      icon={BrainCircuit}
    >
      <div className="space-y-6">
        <Link
          href="/rca"
          className="inline-flex items-center gap-2 text-xs text-white/40 transition hover:text-white/70"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          All RCA cases
        </Link>

        <section className="grid gap-4 xl:grid-cols-[1.4fr_0.6fr]">
          <div className="rounded-2xl border border-emerald-400/15 bg-emerald-400/[0.04] p-5">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-300" />

              <span className="text-[10px] uppercase tracking-[0.15em] text-emerald-300/70">
                Deterministic Diagnosis
              </span>
            </div>

            <h2 className="mt-4 break-words text-xl font-semibold text-white">
              {structured
                ?.primary_cause ??
                bundle.case
                  .baseline_primary_cause ??
                "No verified structured diagnosis"}
            </h2>

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <StatusBadge
                value={
                  structured
                    ?.verifier_status
                }
              />

              <span className="text-sm text-white/55">
                Confidence{" "}
                {confidence(
                  structured
                    ?.confidence ??
                    null
                )}
              </span>
            </div>

            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-white/10 bg-black/15 p-3">
                <p className="text-[10px] uppercase tracking-wider text-white/30">
                  Scope
                </p>

                <p className="mt-2 text-xs text-white/70">
                  {bundle.case
                    .scope_ref ??
                    incident?.case
                      .scope_ref ??
                    "—"}
                </p>
              </div>

              <div className="rounded-xl border border-white/10 bg-black/15 p-3">
                <p className="text-[10px] uppercase tracking-wider text-white/30">
                  Trigger
                </p>

                <p className="mt-2 text-xs text-white/70">
                  {bundle.case
                    .trigger_type ??
                    incident?.case
                      .trigger_type ??
                    "—"}
                </p>
              </div>

              <div className="rounded-xl border border-white/10 bg-black/15 p-3">
                <p className="text-[10px] uppercase tracking-wider text-white/30">
                  Action
                </p>

                <div className="mt-2">
                  <StatusBadge
                    value={
                      incident
                        ?.action
                        ?.status
                    }
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-violet-300" />

              <span className="text-[10px] uppercase tracking-[0.15em] text-white/35">
                Consensus
              </span>
            </div>

            <div className="mt-4">
              <StatusBadge
                value={
                  consensusStatus ??
                  consensus
                    ?.verifier_status
                }
              />
            </div>

            <div className="mt-5">
              <p className="text-[10px] uppercase tracking-wider text-white/30">
                Policy Gate
              </p>

              <p className="mt-2 break-words text-xs text-white/65">
                {actionGate ?? "—"}
              </p>
            </div>

            <p className="mt-5 text-xs leading-5 text-white/35">
              LLM agreement is shown as corroboration only. It does not replace deterministic verification.
            </p>
          </div>
        </section>

        <section className="rounded-2xl border border-white/10 bg-white/[0.025] p-5">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-cyan-300" />

            <div>
              <h2 className="text-sm font-medium text-white">
                Evidence Fusion Ranking
              </h2>

              <p className="mt-1 text-xs text-white/30">
                Candidate causes produced by evidence fusion
              </p>
            </div>
          </div>

          {bundle.fusion.length ===
          0 ? (
            <p className="mt-5 text-xs text-white/30">
              No evidence-fusion predictions were returned.
            </p>
          ) : (
            <div className="mt-5 overflow-x-auto">
              <table className="w-full min-w-[760px] text-left">
                <thead>
                  <tr className="border-b border-white/10 text-[10px] uppercase tracking-wider text-white/30">
                    <th className="py-3 pr-4 font-medium">
                      Rank
                    </th>

                    <th className="px-4 py-3 font-medium">
                      Cause
                    </th>

                    <th className="px-4 py-3 font-medium">
                      Confidence
                    </th>

                    <th className="px-4 py-3 font-medium">
                      Support
                    </th>

                    <th className="px-4 py-3 font-medium">
                      Contradiction
                    </th>

                    <th className="px-4 py-3 font-medium">
                      State
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {bundle.fusion.map(
                    (
                      prediction
                    ) => {
                      const output =
                        prediction
                          .output_json;

                      return (
                        <tr
                          key={
                            prediction.id
                          }
                          className="border-b border-white/5 text-xs last:border-0"
                        >
                          <td className="py-4 pr-4 text-white/40">
                            {
                              prediction.rank
                            }
                          </td>

                          <td className="px-4 py-4 text-white/70">
                            {
                              prediction.primary_cause
                            }
                          </td>

                          <td className="px-4 py-4 text-white/55">
                            {confidence(
                              prediction.confidence
                            )}
                          </td>

                          <td className="px-4 py-4 text-white/55">
                            {typeof output.support_score ===
                            "number"
                              ? output.support_score.toFixed(
                                  4
                                )
                              : "—"}
                          </td>

                          <td className="px-4 py-4 text-white/55">
                            {typeof output.contradiction_score ===
                            "number"
                              ? output.contradiction_score.toFixed(
                                  4
                                )
                              : "—"}
                          </td>

                          <td className="px-4 py-4">
                            <StatusBadge
                              value={
                                prediction.verifier_status
                              }
                            />
                          </td>
                        </tr>
                      );
                    }
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-2xl border border-violet-400/10 bg-violet-400/[0.025] p-5">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-violet-300" />

              <h2 className="text-sm font-medium text-white">
                LLM Proposal Audit
              </h2>
            </div>

            <div className="mt-5 grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-emerald-400/10 bg-emerald-400/5 p-4">
                <p className="text-2xl font-semibold text-white">
                  {
                    acceptedAudits.length
                  }
                </p>

                <p className="mt-1 text-[10px] uppercase tracking-wider text-emerald-300/60">
                  Accepted
                </p>
              </div>

              <div className="rounded-xl border border-red-400/10 bg-red-400/5 p-4">
                <p className="text-2xl font-semibold text-white">
                  {
                    rejectedAudits.length
                  }
                </p>

                <p className="mt-1 text-[10px] uppercase tracking-wider text-red-300/60">
                  Rejected
                </p>
              </div>
            </div>

            {rejectedAudits[0]
              ?.verifier_reason ? (
              <div className="mt-4 rounded-xl border border-red-400/10 bg-black/10 p-4">
                <p className="text-[10px] uppercase tracking-wider text-white/30">
                  Latest rejected reason
                </p>

                <p className="mt-2 break-words text-xs leading-5 text-red-200/60">
                  {
                    rejectedAudits[0]
                      .verifier_reason
                  }
                </p>
              </div>
            ) : null}
          </div>

          <div className="rounded-2xl border border-amber-400/10 bg-amber-400/[0.025] p-5">
            <div className="flex items-center gap-2">
              <TriangleAlert className="h-4 w-4 text-amber-300" />

              <h2 className="text-sm font-medium text-white">
                Authority Boundary
              </h2>
            </div>

            <p className="mt-4 text-xs leading-6 text-white/40">
              Evidence fusion, ML and LLM proposals can support diagnosis.
              Guardian X only treats the deterministic structured RCA as verified when its verifier has explicitly accepted it.
            </p>

            <div className="mt-4 rounded-xl border border-white/10 bg-black/10 p-4">
              <p className="text-[10px] uppercase tracking-wider text-white/30">
                Current deterministic state
              </p>

              <div className="mt-2">
                <StatusBadge
                  value={
                    structured
                      ?.verifier_status
                  }
                />
              </div>
            </div>
          </div>
        </section>
      </div>
    </SectionPage>
  );
}
