import {
  NextRequest,
  NextResponse,
} from "next/server";

const API_URL =
  process.env.NEXT_PUBLIC_GUARDIAN_API_URL ??
  "http://127.0.0.1:8001";

export const dynamic = "force-dynamic";

export async function POST(
  request: NextRequest
) {
  const controller =
    new AbortController();

  const timeout =
    setTimeout(
      () => controller.abort(),
      210_000
    );

  try {
    const payload =
      await request.json();

    const response =
      await fetch(
        `${API_URL}/api/v1/agent/query`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify(
              payload
            ),

          cache:
            "no-store",

          signal:
            controller.signal,
        }
      );

    const raw =
      await response.text();

    let data:
      | Record<string, unknown>
      | null = null;

    try {
      data =
        JSON.parse(
          raw
        ) as Record<
          string,
          unknown
        >;
    } catch {
      data = null;
    }

    if (!response.ok) {
      const detail =
        typeof data?.detail ===
        "string"
          ? data.detail
          : `Guardian Agent failed with HTTP ${response.status}`;

      return NextResponse.json(
        {
          detail,
        },
        {
          status:
            response.status,
        }
      );
    }

    if (!data) {
      return NextResponse.json(
        {
          detail:
            "Guardian Agent returned an invalid response.",
        },
        {
          status: 502,
        }
      );
    }

    return NextResponse.json(
      data
    );

  } catch (error) {
    if (
      error instanceof Error &&
      error.name ===
        "AbortError"
    ) {
      return NextResponse.json(
        {
          detail:
            "Guardian Agent timed out while waiting for the local AI model.",
        },
        {
          status: 504,
        }
      );
    }

    return NextResponse.json(
      {
        detail:
          "Guardian Agent backend is unavailable.",
      },
      {
        status: 502,
      }
    );

  } finally {
    clearTimeout(
      timeout
    );
  }
}
