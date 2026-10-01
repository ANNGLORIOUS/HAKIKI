"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, errorMessages, safeNext } from "@/lib/api";
import type { User } from "@/lib/types";
import { useAuth } from "./AuthProvider";
import { ErrorList, Field, FormPage } from "./forms";

function Step({
  title, done, sendPath, verifyPath, phoneInput, onVerified,
}: { title: string; done: boolean; sendPath: string; verifyPath: string; phoneInput?: boolean; onVerified: () => Promise<unknown> }) {
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [errors, setErrors] = useState<string[]>([]);

  async function send() {
    setBusy(true); setErrors([]); setMsg("");
    try {
      await api(sendPath, { json: phoneInput ? { phone } : {} });
      setSent(true);
      setMsg(phoneInput ? "We sent a 6-digit code by SMS." : "We sent a 6-digit code to your email.");
    } catch (e) { setErrors(errorMessages(e)); } finally { setBusy(false); }
  }

  async function verify(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true); setErrors([]);
    try { await api(verifyPath, { json: { code } }); await onVerified(); }
    catch (err) { setErrors(errorMessages(err)); } finally { setBusy(false); }
  }

  if (done) return <p className="py-4 text-lg font-semibold text-brand">{title}: verified</p>;

  return (
    <div className="py-5">
      <h2 className="text-2xl font-bold">{title}</h2>
      {phoneInput && (
        <div className="mt-3 max-w-sm">
          <Field label="Phone number" htmlFor="phone" hint="Kenyan number, for example 0712 345 678">
            <input id="phone" className="input" type="tel" inputMode="tel" value={phone} onChange={(e) => setPhone(e.target.value)} autoComplete="tel" />
          </Field>
        </div>
      )}
      <button type="button" className="btn btn-secondary mt-3" onClick={send} disabled={busy || (phoneInput && !phone.trim())}>
        {sent ? "Send a new code" : "Send code"}
      </button>
      {msg && <p role="status" className="mt-2 text-slate-700">{msg}</p>}
      <form onSubmit={verify} className="mt-4 max-w-sm space-y-3">
        <Field label="6-digit code" htmlFor={"code-" + title}>
          <input id={"code-" + title} className="input tracking-widest" inputMode="numeric" pattern="[0-9]{6}" maxLength={6} value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} autoComplete="one-time-code" />
        </Field>
        <ErrorList errors={errors} />
        <button className="btn btn-primary" disabled={busy || code.length !== 6}>Verify</button>
      </form>
    </div>
  );
}

export default function VerifyFlow({ next }: { next?: string }) {
  const { user, loading, refresh } = useAuth();
  const router = useRouter();
  const dest = safeNext(next, "/report");

  useEffect(() => {
    if (!loading && !user) router.replace(`/login?next=${encodeURIComponent("/verify?next=" + dest)}`);
  }, [loading, user, router, dest]);

  if (loading || !user) return <FormPage title="Verify your account"><p role="status">Loading...</p></FormPage>;
  const ok = (u: User) => u.email_verified && u.phone_verified;

  return (
    <FormPage title="Verify your account" intro="Verified accounts keep reports honest and protect legitimate sellers from fake ones. Your details are never shown publicly.">
      <div className="divide-y divide-slate-200">
        <Step title="Email" done={user.email_verified} sendPath="/auth/email/send" verifyPath="/auth/email/verify" onVerified={refresh} />
        <Step title="Phone" done={user.phone_verified} phoneInput sendPath="/auth/phone/send" verifyPath="/auth/phone/verify" onVerified={refresh} />
      </div>
      {ok(user) && (
        <div className="mt-6 rounded-lg border border-brand bg-brand-tint px-5 py-4">
          <p className="text-lg font-bold text-brand">You're verified.</p>
          <Link href={dest} className="btn btn-primary mt-3">Continue</Link>
        </div>
      )}
    </FormPage>
  );
}
