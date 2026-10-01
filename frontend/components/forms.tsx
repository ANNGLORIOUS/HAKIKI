"use client";

import { PLATFORMS } from "@/lib/labels";

export function Field({
  label, hint, children, htmlFor,
}: { label: string; hint?: string; children: React.ReactNode; htmlFor: string }) {
  return (
    <div>
      <label htmlFor={htmlFor} className="mb-1 block text-sm font-semibold">{label}</label>
      {hint && <p className="mb-1.5 text-sm text-slate-600">{hint}</p>}
      {children}
    </div>
  );
}

export function PlatformHandle({
  platform, handle, onPlatform, onHandle,
}: { platform: string; handle: string; onPlatform: (v: string) => void; onHandle: (v: string) => void }) {
  return (
    <div className="grid gap-4 sm:grid-cols-[180px_1fr]">
      <Field label="Platform" htmlFor="platform">
        <select id="platform" className="input" value={platform} onChange={(e) => onPlatform(e.target.value)} required>
          {PLATFORMS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
        </select>
      </Field>
      <Field label="Handle or profile link" htmlFor="handle" hint="Paste the full profile link, or type @handle. Short links like vm.tiktok.com won't work.">
        <input id="handle" className="input" value={handle} onChange={(e) => onHandle(e.target.value)} placeholder="@shopname" required maxLength={300} />
      </Field>
    </div>
  );
}

export function ErrorList({ errors }: { errors: string[] }) {
  if (!errors.length) return null;
  return (
    <div role="alert" className="rounded-lg border border-alert bg-alert-tint px-4 py-3 text-sm text-alert">
      <ul className="list-disc space-y-1 pl-4">{errors.map((e, i) => <li key={i}>{e}</li>)}</ul>
    </div>
  );
}

export function SuccessBox({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div role="status" className="rounded-lg border border-brand bg-brand-tint px-5 py-4">
      <p className="text-lg font-bold text-brand">{title}</p>
      {children && <div className="mt-2 space-y-2 text-slate-800">{children}</div>}
    </div>
  );
}

export function FormPage({ title, intro, children }: { title: string; intro?: string; children: React.ReactNode }) {
  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="text-3xl font-bold sm:text-4xl">{title}</h1>
      {intro && <p className="mt-3 text-lg text-slate-700">{intro}</p>}
      <div className="panel mt-6">{children}</div>
    </div>
  );
}
