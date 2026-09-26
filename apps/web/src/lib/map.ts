import type {
  GuardianMapPayload,
} from "@/types/map";


const API_URL =
  process.env.NEXT_PUBLIC_GUARDIAN_API_URL ??
  "http://127.0.0.1:8001";


export async function getGuardianMap(): Promise<GuardianMapPayload> {
  const response =
    await fetch(
      `${API_URL}/api/v1/dashboard/map?device_limit=250`,
      {
        cache: "no-store",
      }
    );

  if (!response.ok) {
    throw new Error(
      `Guardian map request failed: ${response.status}`
    );
  }

  return response.json() as Promise<GuardianMapPayload>;
}
