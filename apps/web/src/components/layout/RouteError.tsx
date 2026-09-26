"use client";

import {
  AlertTriangle,
  RotateCcw,
} from "lucide-react";


interface Props {
  section: string;

  error: Error & {
    digest?: string;
  };

  reset: () => void;
}


export default function RouteError({
  section,
  error,
  reset,
}: Props) {
  return (
    <main className="min-h-screen bg-[#050810] px-6 py-12 text-white">
      <div className="mx-auto max-w-xl rounded-2xl border border-red-400/15 bg-red-400/[0.035] p-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-red-400/20 bg-red-400/10">
            <AlertTriangle className="h-5 w-5 text-red-300" />
          </div>

          <div>
            <p className="text-[10px] uppercase tracking-[0.15em] text-red-300/60">
              Guardian X
            </p>

            <h1 className="mt-1 text-lg font-medium text-white">
              {section} unavailable
            </h1>
          </div>
        </div>

        <p className="mt-5 text-sm leading-6 text-white/45">
          This section encountered an unexpected error while loading.
          Other Guardian X sections may still be available.
        </p>

        <p className="mt-3 break-words text-xs text-white/25">
          {error.message ||
            "Unknown application error"}
        </p>

        <button
          type="button"
          onClick={
            reset
          }
          className="mt-5 inline-flex items-center gap-2 rounded-lg border border-red-400/20 bg-red-400/10 px-4 py-2 text-xs text-red-200 transition hover:bg-red-400/15"
        >
          <RotateCcw className="h-3.5 w-3.5" />

          Retry section
        </button>
      </div>
    </main>
  );
}
