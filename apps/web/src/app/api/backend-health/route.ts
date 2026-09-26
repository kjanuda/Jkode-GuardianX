import {
  NextResponse,
} from "next/server";


const API_URL =
  process.env.NEXT_PUBLIC_GUARDIAN_API_URL ??
  "http://127.0.0.1:8001";


export const dynamic =
  "force-dynamic";


export async function GET() {
  const controller =
    new AbortController();

  const timeout =
    setTimeout(
      () =>
        controller.abort(),
      4000
    );

  try {
    const response =
      await fetch(
        `${API_URL}/health`,
        {
          cache:
            "no-store",

          signal:
            controller.signal,
        }
      );

    let backendStatus:
      string | null = null;

    try {
      const body =
        await response.json() as {
          status?: unknown;
        };

      backendStatus =
        typeof body.status ===
        "string"
          ? body.status
          : null;

    } catch {
      backendStatus =
        null;
    }

    return NextResponse.json({
      online:
        response.ok,

      http_status:
        response.status,

      backend_status:
        backendStatus,

      checked_at:
        new Date()
          .toISOString(),
    });

  } catch {
    return NextResponse.json({
      online:
        false,

      http_status:
        null,

      backend_status:
        "unreachable",

      checked_at:
        new Date()
          .toISOString(),
    });

  } finally {
    clearTimeout(
      timeout
    );
  }
}
