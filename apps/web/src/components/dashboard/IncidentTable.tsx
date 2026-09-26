import type {
  DashboardIncidents,
} from "@/types/guardian";


interface IncidentTableProps {
  incidents: DashboardIncidents;
}


function formatConfidence(
  value: number | null
) {
  if (value === null) {
    return "—";
  }

  return `${Math.round(value * 100)}%`;
}


export default function IncidentTable({
  incidents,
}: IncidentTableProps) {
  return (
    <section className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.025]">
      <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
        <div>
          <h2 className="text-sm font-medium text-white">
            Recent RCA Incidents
          </h2>

          <p className="mt-1 text-xs text-white/35">
            Evidence → Diagnosis → Action lifecycle
          </p>
        </div>

        <span className="rounded-lg bg-white/5 px-2.5 py-1 text-[11px] text-white/40">
          {incidents.count} shown
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[850px] text-left">
          <thead>
            <tr className="border-b border-white/10 text-[10px] uppercase tracking-[0.14em] text-white/30">
              <th className="px-5 py-3 font-medium">
                Incident
              </th>

              <th className="px-5 py-3 font-medium">
                Scope
              </th>

              <th className="px-5 py-3 font-medium">
                Diagnosis
              </th>

              <th className="px-5 py-3 font-medium">
                Confidence
              </th>

              <th className="px-5 py-3 font-medium">
                Action
              </th>

              <th className="px-5 py-3 font-medium">
                Status
              </th>
            </tr>
          </thead>

          <tbody>
            {incidents.items.map((incident) => (
              <tr
                key={incident.incident_id}
                className="border-b border-white/5 text-xs last:border-0"
              >
                <td className="px-5 py-4 font-medium text-white/80">
                  {incident.incident_id}
                </td>

                <td className="px-5 py-4">
                  <div className="text-white/65">
                    {incident.case.scope_ref}
                  </div>

                  <div className="mt-1 text-[10px] text-white/30">
                    {incident.case.scope_type}
                  </div>
                </td>

                <td className="px-5 py-4">
                  <div className="max-w-[230px] truncate text-white/65">
                    {incident.diagnosis.primary_cause}
                  </div>

                  <div className="mt-1 text-[10px] text-white/30">
                    {incident.diagnosis.verifier_status ?? "UNVERIFIED"}
                  </div>
                </td>

                <td className="px-5 py-4 text-white/60">
                  {formatConfidence(
                    incident.diagnosis.confidence
                  )}
                </td>

                <td className="px-5 py-4">
                  {incident.action ? (
                    <>
                      <div className="max-w-[230px] truncate text-white/65">
                        {incident.action.action_code}
                      </div>

                      <div className="mt-1 text-[10px] text-white/30">
                        {incident.action.execution_mode}
                      </div>
                    </>
                  ) : (
                    <span className="text-white/25">
                      No action
                    </span>
                  )}
                </td>

                <td className="px-5 py-4">
                  <span className="rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] text-white/55">
                    {incident.action?.status ??
                      incident.incident_status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
