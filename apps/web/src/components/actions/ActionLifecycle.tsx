import {
  Ban,
  BadgeCheck,
  Circle,
} from "lucide-react";

import type {
  ActionPlan,
} from "@/types/actions";


type StageState =
  | "complete"
  | "blocked"
  | "pending";


interface Stage {
  label: string;
  description: string;
  state: StageState;
}


function stageIcon(
  state: StageState
) {
  if (
    state === "complete"
  ) {
    return BadgeCheck;
  }

  if (
    state === "blocked"
  ) {
    return Ban;
  }

  return Circle;
}


export default function ActionLifecycle({
  plan,
}: {
  plan: ActionPlan;
}) {
  const blocked =
    plan.status === "BLOCKED" ||
    plan.safety_gate_status ===
      "BLOCKED";

  const rejected =
    plan.status === "REJECTED" ||
    plan.rejected_at !== null;

  const simulationPassed =
    plan.latest_simulation
      ?.status === "PASSED";

  const verificationPassed =
    plan.latest_verification
      ?.status === "VERIFIED";

  const stages: Stage[] = [
    {
      label:
        "Action Planned",

      description:
        "Action plan generated from verified RCA evidence.",

      state:
        "complete",
    },

    {
      label:
        "Safety / Policy Gate",

      description:
        plan.safety_gate_status,

      state:
        blocked || rejected
          ? "blocked"
          : "complete",
    },

    {
      label:
        "Human Review",

      description:
        plan.reviewed_by
          ? `Reviewed by ${plan.reviewed_by}`
          : "Human review required",

      state:
        plan.reviewed_at
          ? "complete"
          : blocked || rejected
            ? "blocked"
            : "pending",
    },

    {
      label:
        "Simulation Approval",

      description:
        plan.approved_for_simulation_at
          ? "Approved for simulation"
          : "Not approved for simulation",

      state:
        plan.approved_for_simulation_at
          ? "complete"
          : blocked || rejected
            ? "blocked"
            : "pending",
    },

    {
      label:
        "Dry-run Simulation",

      description:
        plan.latest_simulation
          ? `${plan.latest_simulation.simulation_mode} / ${plan.latest_simulation.status}`
          : "No simulation recorded",

      state:
        simulationPassed
          ? "complete"
          : plan.latest_simulation
            ? "blocked"
            : blocked || rejected
              ? "blocked"
              : "pending",
    },

    {
      label:
        "Deterministic Verification",

      description:
        plan.latest_verification
          ? plan.latest_verification.status
          : "No verification recorded",

      state:
        verificationPassed
          ? "complete"
          : plan.latest_verification
            ? "blocked"
            : blocked || rejected
              ? "blocked"
              : "pending",
    },

    {
      label:
        "Final Lifecycle State",

      description:
        plan.status,

      state:
        plan.status ===
        "VERIFIED_SUCCESS"
          ? "complete"
          : blocked ||
              rejected ||
              plan.status ===
                "VERIFIED_FAILED" ||
              plan.status ===
                "ROLLBACK_REQUIRED"
            ? "blocked"
            : "pending",
    },
  ];

  return (
    <div className="space-y-0">
      {stages.map(
        (
          stage,
          index
        ) => {
          const Icon =
            stageIcon(
              stage.state
            );

          return (
            <div
              key={
                stage.label
              }
              className="relative flex gap-4 pb-6 last:pb-0"
            >
              {index <
              stages.length -
                1 ? (
                <div className="absolute left-[15px] top-8 h-full w-px bg-white/10" />
              ) : null}

              <div
                className={[
                  "relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border",
                  stage.state ===
                  "complete"
                    ? "border-emerald-400/20 bg-emerald-400/10"
                    : stage.state ===
                        "blocked"
                      ? "border-red-400/20 bg-red-400/10"
                      : "border-white/10 bg-white/5",
                ].join(" ")}
              >
                <Icon
                  className={[
                    "h-4 w-4",
                    stage.state ===
                    "complete"
                      ? "text-emerald-300"
                      : stage.state ===
                          "blocked"
                        ? "text-red-300"
                        : "text-white/25",
                  ].join(" ")}
                />
              </div>

              <div className="pt-1">
                <p className="text-xs font-medium text-white/75">
                  {
                    stage.label
                  }
                </p>

                <p className="mt-1 text-[11px] leading-5 text-white/35">
                  {
                    stage.description
                  }
                </p>
              </div>
            </div>
          );
        }
      )}
    </div>
  );
}
