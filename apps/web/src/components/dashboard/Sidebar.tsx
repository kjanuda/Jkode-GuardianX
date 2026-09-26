"use client";

import Link from "next/link";
import {
  usePathname,
} from "next/navigation";

import {
  Activity,
  ShieldCheck,
} from "lucide-react";

import BackendHealthStatus from "@/components/layout/BackendHealthStatus";

import {
  navigation,
} from "@/lib/navigation";


export default function Sidebar() {
  const pathname =
    usePathname();

  return (
    <aside className="hidden min-h-screen w-64 shrink-0 border-r border-white/10 bg-[#070b14] lg:flex lg:flex-col">
      <div className="flex h-20 items-center gap-3 border-b border-white/10 px-6">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-cyan-400/25 bg-cyan-400/10">
          <ShieldCheck className="h-5 w-5 text-cyan-300" />
        </div>

        <div>
          <div className="text-sm font-semibold tracking-[0.18em] text-white">
            GUARDIAN X
          </div>

          <div className="mt-0.5 text-[10px] uppercase tracking-[0.18em] text-white/40">
            Telecom Intelligence
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {navigation.map(
          (item) => {
            const Icon =
              item.icon;

            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(
                    item.href
                  );

            return (
              <Link
                key={
                  item.label
                }
                href={
                  item.href
                }
                className={[
                  "flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm transition",
                  active
                    ? "bg-white/8 text-white"
                    : "text-white/45 hover:bg-white/5 hover:text-white/80",
                ].join(" ")}
              >
                <Icon className="h-4 w-4" />

                {
                  item.label
                }
              </Link>
            );
          }
        )}
      </nav>

      <div className="px-4 pb-2">
        <BackendHealthStatus />
      </div>

      <div className="m-4 rounded-2xl border border-emerald-400/15 bg-emerald-400/5 p-4">
        <div className="flex items-center gap-2 text-xs font-medium text-emerald-300">
          <Activity className="h-4 w-4" />
          Safety Guard Active
        </div>

        <p className="mt-2 text-[11px] leading-5 text-white/35">
          Advisory execution only.
          Human approval remains mandatory.
        </p>
      </div>
    </aside>
  );
}
