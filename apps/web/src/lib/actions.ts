import type {
  ActionPlan,
} from "@/types/actions";


const API_URL =
  process.env.NEXT_PUBLIC_GUARDIAN_API_URL ??
  "http://127.0.0.1:8001";


export async function getActionPlan(
  planId: number
): Promise<ActionPlan> {
  const response =
    await fetch(
      `${API_URL}/api/v1/actions/${planId}`,
      {
        cache: "no-store",
      }
    );

  if (!response.ok) {
    throw new Error(
      `Action plan request failed: ${response.status}`
    );
  }

  return response.json() as Promise<ActionPlan>;
}
