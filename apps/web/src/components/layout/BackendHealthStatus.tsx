"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  Activity,
} from "lucide-react";


type HealthState =
  | "CHECKING"
  | "ONLINE"
  | "OFFLINE";


export default function BackendHealthStatus() {
  const [
    state,
    setState,
  ] = useState<HealthState>(
    "CHECKING"
  );


  useEffect(
    () => {
      let mounted =
        true;

      async function checkHealth() {
        try {
          const response =
            await fetch(
              "/api/backend-health",
              {
                cache:
                  "no-store",
              }
            );

          const data =
            await response.json() as {
              online?: boolean;
            };

          if (!mounted) {
            return;
          }

          setState(
            data.online
              ? "ONLINE"
              : "OFFLINE"
          );

        } catch {
          if (
            mounted
          ) {
            setState(
              "OFFLINE"
            );
          }
        }
      }


      void checkHealth();

      const interval =
        window.setInterval(
          () => {
            void checkHealth();
          },
          15000
        );


      return () => {
        mounted =
          false;

        window.clearInterval(
          interval
        );
      };
    },
    []
  );


  const classes =
    state === "ONLINE"
      ? "border-emerald-400/15 bg-emerald-400/5 text-emerald-300"
      : state === "OFFLINE"
        ? "border-red-400/15 bg-red-400/5 text-red-300"
        : "border-white/10 bg-white/5 text-white/35";


  return (
    <div
      className={[
        "flex items-center gap-2 rounded-lg border px-3 py-2",
        classes,
      ].join(" ")}
    >
      <Activity className="h-3.5 w-3.5" />

      <div>
        <p className="text-[9px] uppercase tracking-[0.14em] opacity-60">
          Backend
        </p>

        <p className="mt-0.5 text-[10px] font-medium">
          {state}
        </p>
      </div>
    </div>
  );
}
