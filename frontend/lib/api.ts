/** Browser-side API helper. Calls go to this site's own /api proxy, which adds the login cookie. */
export class ApiError extends Error {
  status: number;
  data: unknown;
  constructor(status: number, data: unknown) {
    super("API error " + status);
    this.status = status;
    this.data = data;
  }
}

interface Options {
  method?: string;
  json?: unknown;
  form?: FormData;
}

export async function api<T = unknown>(path: string, opts: Options = {}): Promise<T> {
  const hasBody = opts.json !== undefined || opts.form !== undefined;
  const res = await fetch("/api" + path, {
    method: opts.method ?? (hasBody ? "POST" : "GET"),
    headers: opts.json !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: opts.json !== undefined ? JSON.stringify(opts.json) : opts.form,
    credentials: "same-origin",
    cache: "no-store",
  });
  const text = await res.text();
  let data: unknown = null;
  if (text) {
    try { data = JSON.parse(text); } catch { data = { detail: "Unexpected response from the server." }; }
  }
  if (!res.ok) throw new ApiError(res.status, data);
  return data as T;
}

/** Turns Django REST Framework error bodies into a flat list of readable messages. */
export function errorMessages(err: unknown): string[] {
  if (!(err instanceof ApiError)) return ["Something went wrong. Check your connection and try again."];
  const d = err.data as Record<string, unknown> | null;
  if (err.status === 429) return ["Too many attempts. Please wait a bit and try again."];
  if (!d || typeof d !== "object") return ["Something went wrong. Please try again."];
  if (typeof d.detail === "string") return [d.detail];
  const out: string[] = [];
  for (const [key, val] of Object.entries(d)) {
    const msgs = Array.isArray(val) ? val.map(String) : [String(val)];
    const name = key === "non_field_errors" ? "" : key.replace(/_/g, " ") + ": ";
    msgs.forEach((m) => out.push(name + m));
  }
  return out.length ? out : ["Something went wrong. Please try again."];
}

/** Only allow redirects to paths on this site. */
export function safeNext(next: string | undefined | null, fallback = "/"): string {
  return next && next.startsWith("/") && !next.startsWith("//") ? next : fallback;
}
