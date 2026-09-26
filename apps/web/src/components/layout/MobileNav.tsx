"use client";

import Link from "next/link";
import {
  usePathname,
} from "next/navigation";

import BackendHealthStatus from "@/components/layout/BackendHealthStatus";

import {
  navigation,
} from "@/lib/navigation";


export default function MobileNav() {
  const pathname =
    usePathname();

  return (
    <div className="border-b border-white/10 bg-[#070b14] lg:hidden">
      <div className="flex gap-2 overflow-x-auto px-4 py-3">
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
                  "flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-xs",
                  active
                    ? "bg-white/10 text-white"
                    : "text-white/40",
                ].join(" ")}
              >
                <Icon className="h-3.5 w-3.5" />

                {
                  item.label
                }
              </Link>
            );
          }
        )}
      </div>

      <div className="px-4 pb-3">
        <BackendHealthStatus />
      </div>
    </div>
  );
}
