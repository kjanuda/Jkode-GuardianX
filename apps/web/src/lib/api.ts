import type {
  DashboardIncidents,
  DashboardMap,
  DashboardOverview,
  GuardianAlert,
  GuardianAlertCollection,
} from "@/types/guardian";

import type {
  NormalizedRcaCase,
  RcaCaseBundle,
  RcaPrediction,
} from "@/types/rca";


const API_URL =
  process.env.NEXT_PUBLIC_GUARDIAN_API_URL ??
  "http://127.0.0.1:8001";


async function apiGet<T>(
  path: string
): Promise<T> {
  const response = await fetch(
    `${API_URL}${path}`,
    {
      cache: "no-store",
    }
  );

  if (!response.ok) {
    throw new Error(
      `Guardian X API request failed: ${response.status}`
    );
  }

  return response.json() as Promise<T>;
}


function asRecord(
  value: unknown
): Record<string, unknown> {
  if (
    value !== null &&
    typeof value === "object" &&
    !Array.isArray(value)
  ) {
    return value as Record<string, unknown>;
  }

  return {};
}


function stringValue(
  value: unknown
): string | null {
  return typeof value === "string"
    ? value
    : null;
}


function numberValue(
  value: unknown
): number | null {
  return typeof value === "number"
    ? value
    : null;
}


function normalizePredictions(
  value: unknown
): RcaPrediction[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      const row =
        asRecord(item);

      const id =
        numberValue(
          row.id
        );

      const engineType =
        stringValue(
          row.engine_type
        );

      if (
        id === null ||
        engineType === null
      ) {
        return null;
      }

      return {
        id,
        engine_type:
          engineType,

        primary_cause:
          stringValue(
            row.primary_cause
          ),

        confidence:
          numberValue(
            row.confidence
          ),

        rank:
          numberValue(
            row.rank
          ) ?? 1,

        output_json:
          asRecord(
            row.output_json
          ),

        verifier_status:
          stringValue(
            row.verifier_status
          ),

        verifier_reason:
          stringValue(
            row.verifier_reason
          ),

        created_at:
          stringValue(
            row.created_at
          ) ?? "",
      } satisfies RcaPrediction;
    })
    .filter(
      (
        item
      ): item is RcaPrediction =>
        item !== null
    );
}


function normalizeRcaCase(
  payload: unknown,
  fallbackCaseId: number
): NormalizedRcaCase {
  const root =
    asRecord(
      payload
    );

  const nestedCase =
    asRecord(
      root.case
    );

  const caseData =
    Object.keys(
      nestedCase
    ).length > 0
      ? nestedCase
      : root;

  const predictions =
    normalizePredictions(
      root.predictions
    );

  return {
    id:
      numberValue(
        caseData.id
      ) ??
      numberValue(
        caseData.case_id
      ) ??
      fallbackCaseId,

    case_uuid:
      stringValue(
        caseData.case_uuid
      ),

    status:
      stringValue(
        caseData.status
      ),

    scope_type:
      stringValue(
        caseData.scope_type
      ),

    scope_ref:
      stringValue(
        caseData.scope_ref
      ),

    trigger_type:
      stringValue(
        caseData.trigger_type
      ),

    risk_score:
      numberValue(
        caseData.risk_score
      ),

    risk_level:
      stringValue(
        caseData.risk_level
      ),

    baseline_primary_cause:
      stringValue(
        caseData.baseline_primary_cause
      ),

    created_at:
      stringValue(
        caseData.created_at
      ),

    updated_at:
      stringValue(
        caseData.updated_at
      ),

    predictions,
  };
}


function latestEngine(
  predictions: RcaPrediction[],
  engine: string
) {
  return (
    [...predictions]
      .filter(
        (prediction) =>
          prediction.engine_type ===
          engine
      )
      .sort(
        (a, b) =>
          b.id - a.id
      )[0] ??
    null
  );
}


function normalizeAlertPayload(
  payload: unknown
): GuardianAlertCollection {
  if (Array.isArray(payload)) {
    return {
      items:
        payload as GuardianAlert[],
      count:
        payload.length,
    };
  }

  if (
    payload !== null &&
    typeof payload ===
      "object"
  ) {
    const object =
      payload as Record<
        string,
        unknown
      >;

    const possibleItems =
      Array.isArray(
        object.value
      )
        ? object.value
        : Array.isArray(
              object.items
            )
          ? object.items
          : [];

    const rawCount =
      typeof object.Count ===
      "number"
        ? object.Count
        : typeof object.count ===
            "number"
          ? object.count
          : possibleItems.length;

    return {
      items:
        possibleItems as GuardianAlert[],
      count:
        rawCount,
    };
  }

  return {
    items: [],
    count: 0,
  };
}


async function getAlerts(
  path: string
): Promise<GuardianAlertCollection> {
  const payload =
    await apiGet<unknown>(
      path
    );

  return normalizeAlertPayload(
    payload
  );
}


export function getDashboardOverview() {
  return apiGet<DashboardOverview>(
    "/api/v1/dashboard/overview"
  );
}


export function getDashboardIncidents(
  limit = 8
) {
  return apiGet<DashboardIncidents>(
    `/api/v1/dashboard/incidents?limit=${limit}`
  );
}


export function getDashboardMap() {
  return apiGet<DashboardMap>(
    "/api/v1/dashboard/map?device_limit=250"
  );
}


export function getActiveAlerts() {
  return getAlerts(
    "/api/v1/alerts/active"
  );
}


export function getAlertHistory() {
  return getAlerts(
    "/api/v1/alerts/history"
  );
}


export async function getRcaCaseBundle(
  caseId: number
): Promise<RcaCaseBundle> {
  const [
    caseResult,
    evidenceResult,
  ] =
    await Promise.allSettled([
      apiGet<unknown>(
        `/api/v1/rca/cases/${caseId}`
      ),

      apiGet<unknown>(
        `/api/v1/rca/cases/${caseId}/evidence-packet`
      ),
    ]);

  if (
    caseResult.status !==
    "fulfilled"
  ) {
    throw new Error(
      `RCA case ${caseId} unavailable`
    );
  }

  const normalized =
    normalizeRcaCase(
      caseResult.value,
      caseId
    );

  const predictions =
    normalized.predictions;

  return {
    case:
      normalized,

    structured:
      latestEngine(
        predictions,
        "STRUCTURED_RCA_V1"
      ),

    consensus:
      latestEngine(
        predictions,
        "RCA_CONSENSUS_V1"
      ),

    fusion:
      predictions
        .filter(
          (prediction) =>
            prediction.engine_type ===
            "EVIDENCE_FUSION_V1"
        )
        .sort(
          (a, b) =>
            a.rank - b.rank
        ),

    llmAudits:
      predictions
        .filter(
          (prediction) =>
            prediction.engine_type ===
            "RCA_PROPOSAL_AUDIT_V1"
        )
        .sort(
          (a, b) =>
            b.id - a.id
        ),

    evidencePacket:
      evidenceResult.status ===
      "fulfilled"
        ? evidenceResult.value
        : null,
  };
}
