import {
  MapPin,
  RadioTower,
  Smartphone,
} from "lucide-react";

import type {
  DashboardMap,
} from "@/types/guardian";


interface MapPreviewProps {
  data: DashboardMap;
}


export default function MapPreview({
  data,
}: MapPreviewProps) {
  const summary = data.summary;

  return (
    <section className="relative min-h-[320px] overflow-hidden rounded-2xl border border-white/10 bg-[#080d17]">
      <div
        className="absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      <div className="relative z-10 flex items-start justify-between p-5">
        <div>
          <h2 className="text-sm font-medium text-white">
            Network Geo Intelligence
          </h2>

          <p className="mt-1 text-xs text-white/35">
            Live geo payload ready for interactive mapping
          </p>
        </div>

        <MapPin className="h-5 w-5 text-cyan-300" />
      </div>

      <div className="relative z-10 grid grid-cols-2 gap-3 px-5 pb-5 md:grid-cols-4">
        <div className="rounded-xl border border-white/10 bg-black/20 p-4">
          <RadioTower className="h-4 w-4 text-cyan-300" />

          <p className="mt-3 text-xl font-semibold text-white">
            {summary.tower_count}
          </p>

          <p className="mt-1 text-[10px] uppercase tracking-wider text-white/30">
            Towers
          </p>
        </div>

        <div className="rounded-xl border border-white/10 bg-black/20 p-4">
          <RadioTower className="h-4 w-4 text-violet-300" />

          <p className="mt-3 text-xl font-semibold text-white">
            {summary.cell_count}
          </p>

          <p className="mt-1 text-[10px] uppercase tracking-wider text-white/30">
            Cells
          </p>
        </div>

        <div className="rounded-xl border border-white/10 bg-black/20 p-4">
          <Smartphone className="h-4 w-4 text-emerald-300" />

          <p className="mt-3 text-xl font-semibold text-white">
            {summary.geolocated_device_count}
          </p>

          <p className="mt-1 text-[10px] uppercase tracking-wider text-white/30">
            Geo Devices
          </p>
        </div>

        <div className="rounded-xl border border-white/10 bg-black/20 p-4">
          <MapPin className="h-4 w-4 text-amber-300" />

          <p className="mt-3 text-xl font-semibold text-white">
            {summary.point_count}
          </p>

          <p className="mt-1 text-[10px] uppercase tracking-wider text-white/30">
            Map Points
          </p>
        </div>
      </div>

      <div className="relative z-10 mx-5 mb-5 rounded-xl border border-dashed border-white/10 bg-black/10 px-4 py-8 text-center text-xs text-white/25">
        Interactive Leaflet network map will be mounted here in STEP 38D.
      </div>
    </section>
  );
}
