import { headers } from "next/headers";
import { BACKEND_URL } from "./config";

/** Server-side GET to the Django API (used by pages that render on the server for SEO). */
export async function serverGet<T>(path: string): Promise<{ status: number; data: T | null; detail?: string }> {
  const xff = (headers().get("x-forwarded-for") || "").split(",")[0].trim();
  try {
    const res = await fetch(`${BACKEND_URL}/api${path}`, {
      cache: "no-store",
      headers: xff ? { "x-forwarded-for": xff } : {},
    });
    const body = await res.json().catch(() => null);
    if (!res.ok) return { status: res.status, data: null, detail: body?.detail };
    return { status: res.status, data: body as T };
  } catch {
    return { status: 503, data: null, detail: "The service is temporarily unavailable. Please try again shortly." };
  }
}
