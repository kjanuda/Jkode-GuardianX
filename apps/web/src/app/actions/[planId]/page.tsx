import Link from "next/link";

import {
  ArrowLeft,
  CheckCircle2,
  LockKeyhole,
  RotateCcw,
  ShieldCheck,
  Wrench,
} from "lucide-react";

import ActionLifecycle from "@/components/actions/ActionLifecycle";
import ActionStatusBadge from "@/components/actions/ActionStatusBadge";
import RetryButton from "@/components/layout/RetryButton";
import SectionPage from "@/components/layout/SectionPage";

import {
  getActionPlan,
} from "@/lib/actions";


function boolValue(
  value: unknown
) {
  return value === true;
}


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


export default async function ActionDetailPage({
  params,
}: {
  params: Promise<{
    planId: string;
  }>;
}) {
  const {
    planId,
  } = await params;

  const numericPlanId =
    Number(
      planId
    );

  if (
    !Number.isInteger(
      numericPlanId
    ) ||
    numericPlanId < 1
  ) {
    return (
      <SectionPage
        eyebrow="Guarded Remediation"
        title="Invalid Action Plan"
        description="The supplied action plan identifier is invalid."
        icon={Wrench}
      />
    );
  }

  const result =
    await Promise.allSettled([
      getActionPlan(
        numericPlanId
      ),
    ]);

  if (
    result[0].status !==
    "fulfilled"
  ) {
    return (
      <SectionPage
        eyebrow="Guarded Remediation"
        title={`PLAN-${numericPlanId}`}
        description="This action plan could not be loaded from the Guardian X backend."
        icon={Wrench}
      >
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href="/actions"
            className="text-xs text-cyan-300"
          >
            ? Back to action plans
          </Link>

          <RetryButton label="Retry plan" />
        </div>
      </SectionPage>
    );
  }

  const plan =
    result[0].value;

  const safetyChecks =
    plan.safety_checks_json ??
    {};

  const preconditions =
    Array.isArray(
      plan.preconditions_json
    )
      ? plan.preconditions_json
      : [];

  const verificationPlan =
    Array.isArray(
      plan.verification_plan_json
    )
      ? plan.verification_plan_json
      : [];

  const rollbackPlan =
    Array.isArray(
      plan.rollback_plan_json
    )
      ? plan.rollback_plan_json
      : [];

  const executionAllowed =
    boolValue(
      safetyChecks[
        "execution_allowed"
      ]
    );

  const autoExecutionAllowed =
    boolValue(
      safetyChecks[
        "auto_execution_allowed"
      ]
    );

  const physicalChangeAllowed =
    boolValue(
      safetyChecks[
        "physical_change_allowed"
      ]
    );

  return (
    <SectionPage
      eyebrow="Guarded Remediation"
      title={`PLAN-${plan.id}`}
      description="Action planning, policy review, simulation, deterministic verification and rollback readiness."
      icon={Wrench}
    >
      <div className="space-y-6">
        <Link
          href="/actions"
          className="inline-flex items-center gap-2 text-xs text-white/40 hover:text-white/70"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          All action plans
        </Link>

        <section className="grid gap-4 xl:grid-cols-[1.35fr_0.65fr]">
          <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5">
            <div className="flex flex-wrap items-center gap-2">
              <ActionStatusBadge
                value={
                  plan.status
                }
              />

              <ActionStatusBadge
                value={
                  plan.execution_mode
                }
              />

              <ActionStatusBadge
                value={
                  plan.safety_gate_status
                }
              />
            </div>

            <h2 className="mt-5 text-xl font-semibold text-white">
              {
                plan.title
              }
            </h2>

            <p className="mt-3 text-sm leading-6 text-white/45">
              {
                plan.description
              }
            </p>

            <div className="mt-5 rounded-xl border border-white/10 bg-black/15 p-4">
              <p className="text-[10px] uppercase tracking-wider text-white/30">
                Rationale
              </p>

              <p className="mt-2 text-xs leading-6 text-white/55">
                {
                  plan.rationale
                }
              </p>
            </div>

            <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-xl border border-white/10 bg-black/10 p-3">
                <p className="text-[10px] uppercase text-white/30">
                  RCA Case
                </p>

                <Link
                  href={`/rca/${plan.rca_case_id}`}
                  className="mt-2 block text-xs text-cyan-300"
                >
                  RCA-
                  {
                    plan.rca_case_id
                  }
                </Link>
              </div>

              <div className="rounded-xl border border-white/10 bg-black/10 p-3">
                <p className="text-[10px] uppercase text-white/30">
                  Root Cause
                </p>

                <p className="mt-2 break-words text-xs text-white/65">
                  {
                    plan.source_primary_cause
                  }
                </p>
              </div>

              <div className="rounded-xl border border-white/10 bg-black/10 p-3">
                <p className="text-[10px] uppercase text-white/30">
                  Confidence
                </p>

                <p className="mt-2 text-xs text-white/65">
                  {confidence(
                    plan.source_confidence
                  )}
                </p>
              </div>

              <div className="rounded-xl border border-white/10 bg-black/10 p-3">
                <p className="text-[10px] uppercase text-white/30">
                  Target
                </p>

                <p className="mt-2 text-xs text-white/65">
                  {
                    plan.target_ref ??
                    "—"
                  }
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-emerald-400/15 bg-emerald-400/[0.035] p-5">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-emerald-300" />

              <h2 className="text-sm font-medium text-white">
                Execution Safety
              </h2>
            </div>

            <div className="mt-5 space-y-3">
              <div className="flex items-center justify-between rounded-xl border border-white/10 bg-black/10 p-3">
                <span className="text-xs text-white/45">
                  Real execution
                </span>

                <span className="text-xs text-red-300">
                  DISABLED
                </span>
              </div>

              <div className="flex items-center justify-between rounded-xl border border-white/10 bg-black/10 p-3">
                <span className="text-xs text-white/45">
                  Auto eligible
                </span>

                <span className="text-xs text-white/65">
                  {
                    plan.auto_eligible
                      ? "YES"
                      : "NO"
                  }
                </span>
              </div>

              <div className="flex items-center justify-between rounded-xl border border-white/10 bg-black/10 p-3">
                <span className="text-xs text-white/45">
                  Human approval
                </span>

                <span className="text-xs text-white/65">
                  {
                    plan.requires_human_approval
                      ? "REQUIRED"
                      : "NOT REQUIRED"
                  }
                </span>
              </div>

              <div className="flex items-center justify-between rounded-xl border border-white/10 bg-black/10 p-3">
                <span className="text-xs text-white/45">
                  Execution allowed
                </span>

                <span className="text-xs text-white/65">
                  {
                    executionAllowed
                      ? "YES"
                      : "NO"
                  }
                </span>
              </div>

              <div className="flex items-center justify-between rounded-xl border border-white/10 bg-black/10 p-3">
                <span className="text-xs text-white/45">
                  Physical change
                </span>

                <span className="text-xs text-white/65">
                  {
                    physicalChangeAllowed
                      ? "YES"
                      : "NO"
                  }
                </span>
              </div>

              <div className="flex items-center justify-between rounded-xl border border-white/10 bg-black/10 p-3">
                <span className="text-xs text-white/45">
                  Auto execution
                </span>

                <span className="text-xs text-white/65">
                  {
                    autoExecutionAllowed
                      ? "YES"
                      : "NO"
                  }
                </span>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-2">
          <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5">
            <h2 className="text-sm font-medium text-white">
              Lifecycle
            </h2>

            <p className="mt-1 text-xs text-white/30">
              Planning → review → simulation → verification
            </p>

            <div className="mt-6">
              <ActionLifecycle
                plan={plan}
              />
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded-2xl border border-cyan-400/10 bg-cyan-400/[0.025] p-5">
              <h2 className="text-sm font-medium text-white">
                Latest Simulation
              </h2>

              {plan.latest_simulation ? (
                <div className="mt-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-white/40">
                      Mode
                    </span>

                    <ActionStatusBadge
                      value={
                        plan.latest_simulation
                          .simulation_mode
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-xs text-white/40">
                      Status
                    </span>

                    <ActionStatusBadge
                      value={
                        plan.latest_simulation
                          .status
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-xs text-white/40">
                      Verification ready
                    </span>

                    <span className="text-xs text-white/65">
                      {
                        plan.latest_simulation
                          .verification_ready
                          ? "YES"
                          : "NO"
                      }
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-xs text-white/40">
                      Execution allowed
                    </span>

                    <span className="text-xs text-red-300">
                      {
                        plan.latest_simulation
                          .execution_allowed
                          ? "YES"
                          : "NO"
                      }
                    </span>
                  </div>
                </div>
              ) : (
                <p className="mt-4 text-xs text-white/30">
                  No simulation exists for this action plan.
                </p>
              )}
            </div>

            <div className="rounded-2xl border border-emerald-400/10 bg-emerald-400/[0.025] p-5">
              <h2 className="text-sm font-medium text-white">
                Latest Verification
              </h2>

              {plan.latest_verification ? (
                <div className="mt-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-white/40">
                      Status
                    </span>

                    <ActionStatusBadge
                      value={
                        plan.latest_verification
                          .status
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-xs text-white/40">
                      Integrity
                    </span>

                    <span className="text-xs text-white/65">
                      {
                        plan.latest_verification
                          .integrity_valid
                          ? "VALID"
                          : "INVALID"
                      }
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-xs text-white/40">
                      Rollback decision
                    </span>

                    <span className="text-xs text-white/65">
                      {
                        plan.latest_verification
                          .rollback_decision
                      }
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-xs text-white/40">
                      Execution allowed
                    </span>

                    <span className="text-xs text-red-300">
                      {
                        plan.latest_verification
                          .execution_allowed
                          ? "YES"
                          : "NO"
                      }
                    </span>
                  </div>
                </div>
              ) : (
                <p className="mt-4 text-xs text-white/30">
                  No deterministic verification exists yet.
                </p>
              )}
            </div>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5">
            <h2 className="text-sm font-medium text-white">
              Preconditions
            </h2>

            <div className="mt-4 space-y-3">
              {preconditions.map(
                (
                  item,
                  index
                ) => (
                  <div
                    key={
                      `${index}-${item}`
                    }
                    className="flex gap-2 text-xs leading-5 text-white/45"
                  >
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-cyan-300" />

                    {item}
                  </div>
                )
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5">
            <h2 className="text-sm font-medium text-white">
              Verification Plan
            </h2>

            <div className="mt-4 space-y-3">
              {verificationPlan.map(
                (
                  item,
                  index
                ) => (
                  <div
                    key={
                      `${index}-${item}`
                    }
                    className="flex gap-2 text-xs leading-5 text-white/45"
                  >
                    <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-300" />

                    {item}
                  </div>
                )
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-5">
            <h2 className="text-sm font-medium text-white">
              Rollback Plan
            </h2>

            <div className="mt-4 space-y-3">
              {rollbackPlan.map(
                (
                  item,
                  index
                ) => (
                  <div
                    key={
                      `${index}-${item}`
                    }
                    className="flex gap-2 text-xs leading-5 text-white/45"
                  >
                    <RotateCcw className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-300" />

                    {item}
                  </div>
                )
              )}
            </div>
          </div>
        </section>

        <div className="flex items-start gap-3 rounded-xl border border-red-400/15 bg-red-400/[0.035] p-4">
          <LockKeyhole className="mt-0.5 h-4 w-4 shrink-0 text-red-300" />

          <div>
            <p className="text-xs font-medium text-red-200">
              Production execution unavailable
            </p>

            <p className="mt-1 text-xs leading-5 text-white/35">
              This interface exposes no real network execution control. Guardian X remains in advisory mode.
            </p>
          </div>
        </div>
      </div>
    </SectionPage>
  );
}
