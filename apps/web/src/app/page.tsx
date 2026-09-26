import {
  Activity,
  BrainCircuit,
  RadioTower,
  Siren,
  Wrench,
} from "lucide-react";

import IncidentTable from "@/components/dashboard/IncidentTable";
import MapPreview from "@/components/dashboard/MapPreview";
import SafetyBanner from "@/components/dashboard/SafetyBanner";
import Sidebar from "@/components/dashboard/Sidebar";
import StatCard from "@/components/dashboard/StatCard";

import {
  getDashboardIncidents,
  getDashboardMap,
  getDashboardOverview,
} from "@/lib/api";


async function loadDashboardData() {
  try {
    return await Promise.all([
      getDashboardOverview(),
      getDashboardIncidents(),
      getDashboardMap(),
    ]);
  } catch {
    return null;
  }
}


function ApiUnavailable() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#050811] p-6 text-white">
      <div className="max-w-lg rounded-2xl border border-red-400/15 bg-red-400/5 p-6">
        <h1 className="text-lg font-medium">
          Guardian X API unavailable
        </h1>

        <p className="mt-2 text-sm leading-6 text-white/45">
          Start the FastAPI backend on port 8001 and refresh this page.
        </p>

        <code className="mt-4 block rounded-xl bg-black/30 p-3 text-xs text-red-200/70">
          uv run fastapi dev app/main.py --port 8001
        </code>
      </div>
    </main>
  );
}


export default async function Home() {
  const data =
    await loadDashboardData();

  if (!data) {
    return <ApiUnavailable />;
  }

  const [
    overview,
    incidents,
    map,
  ] = data;

  return (
    <main className="min-h-screen bg-[#050811] text-white">
      <div className="flex min-h-screen">
        <Sidebar />

        <div className="min-w-0 flex-1">
          <header className="flex min-h-20 items-center justify-between border-b border-white/10 px-5 md:px-8">
            <div>
              <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-300/60">
                Guardian Operations
              </p>

              <h1 className="mt-1 text-lg font-medium tracking-tight text-white">
                Network Intelligence Dashboard
              </h1>
            </div>

            <div className="flex items-center gap-2 rounded-full border border-emerald-400/15 bg-emerald-400/5 px-3 py-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />

              <span className="text-[11px] text-emerald-300">
                Backend Connected
              </span>
            </div>
          </header>

          <div className="space-y-6 p-5 md:p-8">
            <SafetyBanner
              safety={overview.safety}
            />

            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
              <StatCard
                title="Devices"
                value={
                  overview.network
                    .total_devices
                }
                description={`${overview.network.devices_with_active_alerts} currently affected`}
                icon={RadioTower}
              />

              <StatCard
                title="Active Alerts"
                value={
                  overview.alerts.active
                }
                description={`${overview.alerts.critical} critical`}
                icon={Siren}
              />

              <StatCard
                title="RCA Cases"
                value={
                  overview.rca.total_cases
                }
                description={`${overview.rca.verified_structured_predictions} verified structured predictions`}
                icon={BrainCircuit}
              />

              <StatCard
                title="Action Plans"
                value={
                  overview.actions.total
                }
                description={`${overview.actions.auto_eligible} auto eligible`}
                icon={Wrench}
              />

              <StatCard
                title="Feedback"
                value={
                  overview.feedback.total
                }
                description={`${overview.feedback.training_eligible} training eligible`}
                icon={Activity}
              />
            </section>

            <section className="grid gap-6 2xl:grid-cols-[1.35fr_0.65fr]">
              <IncidentTable
                incidents={incidents}
              />

              <MapPreview
                data={map}
              />
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}
