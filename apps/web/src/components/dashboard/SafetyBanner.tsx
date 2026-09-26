import {
  LockKeyhole,
  ShieldCheck,
} from "lucide-react";

import type {
  DashboardOverview,
} from "@/types/guardian";


interface SafetyBannerProps {
  safety: DashboardOverview["safety"];
}


export default function SafetyBanner({
  safety,
}: SafetyBannerProps) {
  return (
    <section className="flex flex-col gap-4 rounded-2xl border border-emerald-400/15 bg-emerald-400/[0.045] p-5 md:flex-row md:items-center md:justify-between">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-400/10">
          <ShieldCheck className="h-5 w-5 text-emerald-300" />
        </div>

        <div>
          <h2 className="text-sm font-medium text-white">
            Guarded Advisory Mode
          </h2>

          <p className="mt-1 max-w-2xl text-xs leading-5 text-white/40">
            Guardian X can diagnose, plan, simulate and verify.
            Production telecom changes remain disabled.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 text-[11px] text-emerald-300">
          {safety.execution_mode}
        </span>

        <span className="flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] text-white/50">
          <LockKeyhole className="h-3 w-3" />
          Human Approval Required
        </span>

        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] text-white/50">
          Auto Execution OFF
        </span>
      </div>
    </section>
  );
}
