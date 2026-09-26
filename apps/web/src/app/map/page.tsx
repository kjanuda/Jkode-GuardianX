import {
  MapIcon,
  MapPin,
  RadioTower,
  Smartphone,
  Siren,
} from "lucide-react";

import SectionPage from "@/components/layout/SectionPage";
import MapClient from "@/components/map/MapClient";

import {
  getGuardianMap,
} from "@/lib/map";


async function loadMap() {
  try {
    return await getGuardianMap();
  } catch {
    return null;
  }
}


export default async function MapPage() {
  const data =
    await loadMap();

  return (
    <SectionPage
      eyebrow="Geo Intelligence"
      title="Network Map"
      description="Live tower, serving-cell and device telemetry locations with alert, RCA and action context."
      icon={MapIcon}
    >
      {!data ? (
        <div className="rounded-xl border border-red-400/15 bg-red-400/5 p-5">
          <p className="text-sm text-red-200">
            Geo intelligence unavailable
          </p>

          <p className="mt-2 text-xs leading-5 text-white/35">
            Guardian X could not load the dashboard map payload.
          </p>
        </div>
      ) : (
        <div className="space-y-5">
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
            <div className="rounded-xl border border-white/10 bg-black/15 p-4">
              <RadioTower className="h-4 w-4 text-cyan-300" />

              <p className="mt-3 text-2xl font-semibold text-white">
                {
                  data.summary
                    .tower_count
                }
              </p>

              <p className="mt-1 text-[10px] uppercase tracking-wider text-white/30">
                Towers
              </p>
            </div>

            <div className="rounded-xl border border-white/10 bg-black/15 p-4">
              <RadioTower className="h-4 w-4 text-violet-300" />

              <p className="mt-3 text-2xl font-semibold text-white">
                {
                  data.summary
                    .cell_count
                }
              </p>

              <p className="mt-1 text-[10px] uppercase tracking-wider text-white/30">
                Cells
              </p>
            </div>

            <div className="rounded-xl border border-white/10 bg-black/15 p-4">
              <Smartphone className="h-4 w-4 text-emerald-300" />

              <p className="mt-3 text-2xl font-semibold text-white">
                {
                  data.summary
                    .geolocated_device_count
                }
              </p>

              <p className="mt-1 text-[10px] uppercase tracking-wider text-white/30">
                Geo Devices
              </p>
            </div>

            <div className="rounded-xl border border-white/10 bg-black/15 p-4">
              <Siren className="h-4 w-4 text-red-300" />

              <p className="mt-3 text-2xl font-semibold text-white">
                {
                  data.summary
                    .active_device_alert_count
                }
              </p>

              <p className="mt-1 text-[10px] uppercase tracking-wider text-white/30">
                Alert Devices
              </p>
            </div>

            <div className="rounded-xl border border-white/10 bg-black/15 p-4">
              <MapPin className="h-4 w-4 text-amber-300" />

              <p className="mt-3 text-2xl font-semibold text-white">
                {
                  data.summary
                    .point_count
                }
              </p>

              <p className="mt-1 text-[10px] uppercase tracking-wider text-white/30">
                Map Points
              </p>
            </div>
          </section>

          <MapClient
            data={data}
          />

          <div className="rounded-xl border border-emerald-400/15 bg-emerald-400/5 p-4">
            <p className="text-xs text-emerald-200">
              Coordinate provenance preserved
            </p>

            <p className="mt-1 text-xs leading-5 text-white/35">
              Towers use native coordinates, cells inherit their serving tower location, and devices use their latest telemetry coordinates.
            </p>
          </div>
        </div>
      )}
    </SectionPage>
  );
}
