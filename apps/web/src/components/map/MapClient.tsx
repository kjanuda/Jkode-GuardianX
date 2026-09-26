"use client";

import dynamic from "next/dynamic";

import type {
  GuardianMapPayload,
} from "@/types/map";


const NetworkMap =
  dynamic(
    () =>
      import(
        "@/components/map/NetworkMap"
      ),
    {
      ssr: false,

      loading: () => (
        <div className="flex h-[620px] items-center justify-center rounded-2xl border border-white/10 bg-[#070b14] text-xs text-white/30">
          Loading network map...
        </div>
      ),
    }
  );


export default function MapClient({
  data,
}: {
  data: GuardianMapPayload;
}) {
  return (
    <NetworkMap
      data={data}
    />
  );
}
