import { NextRequest, NextResponse } from "next/server";
import { BACKEND_URL, TOKEN_COOKIE } from "@/lib/config";

/**
 * Same-origin proxy to the Django API.
 * - The login token lives in an httpOnly cookie, so page scripts can never read it.
 * - The browser never talks to Django directly, so no CORS setup is needed.
 */
export const dynamic = "force-dynamic";

async function handler(req: NextRequest, { params }: { params: { path: string[] } }) {
  const isWrite = !["GET", "HEAD"].includes(req.method);

  // Basic cross-site request check for anything that changes data.
  const origin = req.headers.get("origin");
  if (isWrite && origin && new URL(origin).host !== req.headers.get("host")) {
    return NextResponse.json({ detail: "Cross-site request blocked." }, { status: 403 });
  }

  const path = params.path.join("/");
  const url = `${BACKEND_URL}/api/${path}/${req.nextUrl.search}`;

  const headers = new Headers();
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const token = req.cookies.get(TOKEN_COOKIE)?.value;
  if (token) headers.set("authorization", `Token ${token}`);
  // Pass the visitor's IP so the API's rate limits apply per person, not per server.
  const clientIp = (req.headers.get("x-forwarded-for") || "").split(",")[0].trim() || "unknown";
  headers.set("x-forwarded-for", clientIp);

  const init: RequestInit = { method: req.method, headers, cache: "no-store" };
  if (isWrite) init.body = await req.arrayBuffer();

  let upstream: Response;
  try {
    upstream = await fetch(url, init);
  } catch {
    return NextResponse.json({ detail: "The service is temporarily unavailable. Please try again shortly." }, { status: 502 });
  }

  const text = await upstream.text();
  let body = text;
  let newToken: string | null = null;

  if (upstream.ok && (path === "auth/login" || path === "auth/register")) {
    try {
      const parsed = JSON.parse(text);
      newToken = parsed.token ?? null;
      delete parsed.token; // never send the token to page scripts
      body = JSON.stringify(parsed);
    } catch { /* leave body as is */ }
  }

  const res = new NextResponse(upstream.status === 204 ? null : body, {
    status: upstream.status,
    headers: { "content-type": upstream.headers.get("content-type") ?? "application/json" },
  });

  const cookieOpts = { httpOnly: true, sameSite: "lax" as const, secure: process.env.NODE_ENV === "production", path: "/" };
  if (newToken) res.cookies.set(TOKEN_COOKIE, newToken, { ...cookieOpts, maxAge: 60 * 60 * 24 * 30 });
  if (path === "auth/logout" || (upstream.status === 401 && token)) res.cookies.set(TOKEN_COOKIE, "", { ...cookieOpts, maxAge: 0 });
  return res;
}

export { handler as GET, handler as POST, handler as PUT, handler as PATCH, handler as DELETE };
