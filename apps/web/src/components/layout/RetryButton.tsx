"use client";

import {
  RotateCcw,
} from "lucide-react";

import {
  useRouter,
} from "next/navigation";


export default function RetryButton({
  label = "Retry",
}: {
  label?: string;
}) {
  const router =
    useRouter();

  return (
    <button
      type="button"
      onClick={() =>
        router.refresh()
      }
      className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-[11px] text-white/55 transition hover:border-cyan-400/20 hover:text-white"
    >
      <RotateCcw className="h-3.5 w-3.5" />

      {label}
    </button>
  );
}
