"use client";

import Link from "next/link";
import { useState } from "react";
import { api, errorMessages } from "@/lib/api";
import { CATEGORIES, EVIDENCE_KINDS, PAYMENT_TYPES } from "@/lib/labels";
import { compressImage } from "@/lib/image";
import { ErrorList, Field, FormPage, PlatformHandle, SuccessBox } from "./forms";
import RequireVerified from "./RequireVerified";

interface Picked { file: File; kind: string }

export default function ReportForm({ initialPlatform, initialHandle }: { initialPlatform?: string; initialHandle?: string }) {
  const [platform, setPlatform] = useState(initialPlatform || "instagram");
  const [handle, setHandle] = useState(initialHandle || "");
  const [category, setCategory] = useState("non_delivery");
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState("");
  const [payType, setPayType] = useState("send_money");
  const [payValue, setPayValue] = useState("");
  const [regName, setRegName] = useState("");
  const [whatsapp, setWhatsapp] = useState("");
  const [files, setFiles] = useState<Picked[]>([]);
  const [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [done, setDone] = useState(false);

  async function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const list = Array.from(e.target.files ?? []).slice(0, 6 - files.length);
    e.target.value = "";
    const shrunk = await Promise.all(list.map((f) => compressImage(f)));
    setFiles((prev) => [...prev, ...shrunk.map((file, i) => ({ file, kind: prev.length + i === 0 ? "mpesa_message" : "chat_screenshot" }))]);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErrors([]);
    if (!files.length) { setErrors(["Attach at least one screenshot, such as your M-Pesa message or the chat."]); return; }
    const fd = new FormData();
    fd.append("platform", platform);
    fd.append("handle", handle);
    fd.append("category", category);
    fd.append("description", description);
    if (amount) fd.append("amount_kes", amount);
    if (date) fd.append("incident_date", date);
    if (payValue.trim()) {
      fd.append("payment_type", payType);
      fd.append("payment_value", payValue);
      if (regName.trim()) fd.append("registered_name", regName);
    }
    if (whatsapp.trim()) fd.append("whatsapp_number", whatsapp);
    files.forEach((f) => { fd.append("files", f.file); fd.append("kinds", f.kind); });
    setBusy(true);
    try { await api("/reports", { form: fd }); setDone(true); window.scrollTo({ top: 0 }); }
    catch (err) { setErrors(errorMessages(err)); }
    finally { setBusy(false); }
  }

  return (
    <FormPage
      title="Report a page"
      intro="Tell us what happened and attach your proof. A moderator reviews every report before it is published, and your name is never shown."
    >
      <RequireVerified>
        {done ? (
          <SuccessBox title="Thank you. We received your report.">
            <p>A moderator will review it. You can follow its progress under <Link className="link" href="/my/reports">My reports</Link>.</p>
            <p className="font-semibold">While you wait, act quickly on your money:</p>
            <ul className="list-disc space-y-1 pl-5">
              <li>Contact Safaricom about the M-Pesa transaction. Timing matters.</li>
              <li>Report the account on {platform === "tiktok" ? "TikTok" : "the platform"} itself.</li>
              <li>Consider reporting to the police or the DCI (cybercrime), and keep all your screenshots.</li>
            </ul>
          </SuccessBox>
        ) : (
          <form onSubmit={submit} className="space-y-6">
            <PlatformHandle platform={platform} handle={handle} onPlatform={setPlatform} onHandle={setHandle} />

            <Field label="What happened?" htmlFor="category">
              <select id="category" className="input" value={category} onChange={(e) => setCategory(e.target.value)}>
                {CATEGORIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
            </Field>

            <Field label="Describe it in your own words" htmlFor="description" hint="What did you order, what did they say, and what happened after you paid? Stick to facts. At least 20 characters.">
              <textarea id="description" className="input min-h-[140px]" value={description} onChange={(e) => setDescription(e.target.value)} required minLength={20} maxLength={3000} />
            </Field>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Amount lost (KES)" htmlFor="amount">
                <input id="amount" type="number" inputMode="decimal" min="0" className="input" value={amount} onChange={(e) => setAmount(e.target.value)} />
              </Field>
              <Field label="Date you paid" htmlFor="date">
                <input id="date" type="date" max={new Date().toISOString().slice(0, 10)} className="input" value={date} onChange={(e) => setDate(e.target.value)} />
              </Field>
            </div>

            <fieldset className="space-y-4 border-t border-slate-200 pt-6">
              <legend className="text-xl font-bold">Where did you send the money?</legend>
              <p className="text-slate-700">This helps link pages run by the same people, even when they change handles. Numbers are stored securely and never shown in full.</p>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Payment method" htmlFor="paytype">
                  <select id="paytype" className="input" value={payType} onChange={(e) => setPayType(e.target.value)}>
                    {PAYMENT_TYPES.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
                  </select>
                </Field>
                <Field label="Number" htmlFor="payvalue">
                  <input id="payvalue" className="input" inputMode="numeric" value={payValue} onChange={(e) => setPayValue(e.target.value)} placeholder="0712 345 678" />
                </Field>
              </div>
              <Field label="Name M-Pesa showed when you paid" htmlFor="regname" hint="Scammers often use a different name from the page. Copy it exactly as shown.">
                <input id="regname" className="input" value={regName} onChange={(e) => setRegName(e.target.value)} maxLength={120} />
              </Field>
              <Field label="WhatsApp number they used (optional)" htmlFor="wa">
                <input id="wa" className="input" inputMode="tel" value={whatsapp} onChange={(e) => setWhatsapp(e.target.value)} />
              </Field>
            </fieldset>

            <fieldset className="space-y-3 border-t border-slate-200 pt-6">
              <legend className="text-xl font-bold">Your proof</legend>
              <p className="text-slate-700">Attach your M-Pesa message and chat screenshots. Up to 6 files. Photos are shrunk on your phone so they upload fast.</p>
              <input id="files" type="file" accept="image/*,video/mp4" multiple className="block w-full text-base file:mr-3 file:rounded-lg file:border-0 file:bg-brand file:px-4 file:py-2.5 file:font-semibold file:text-white" onChange={onPick} disabled={files.length >= 6} aria-label="Add proof files" />
              {files.length > 0 && (
                <ul className="divide-y divide-slate-200 border-y border-slate-200">
                  {files.map((f, i) => (
                    <li key={i} className="flex flex-wrap items-center gap-3 py-2">
                      <span className="min-w-0 flex-1 truncate text-sm">{f.file.name} ({Math.max(1, Math.round(f.file.size / 1024))} KB)</span>
                      <select aria-label={`Type of file ${i + 1}`} className="input !w-auto !py-1.5 !text-sm" value={f.kind} onChange={(e) => setFiles((p) => p.map((x, j) => (j === i ? { ...x, kind: e.target.value } : x)))}>
                        {EVIDENCE_KINDS.map((k) => <option key={k.value} value={k.value}>{k.label}</option>)}
                      </select>
                      <button type="button" className="text-sm font-medium text-alert underline" onClick={() => setFiles((p) => p.filter((_, j) => j !== i))}>Remove</button>
                    </li>
                  ))}
                </ul>
              )}
            </fieldset>

            <p className="text-sm text-slate-600">By submitting you confirm that this report is true to the best of your knowledge. Knowingly false reports can harm honest sellers and lead to your account being removed.</p>
            <ErrorList errors={errors} />
            <button className="btn btn-primary w-full sm:w-auto" disabled={busy}>{busy ? "Sending..." : "Submit report"}</button>
          </form>
        )}
      </RequireVerified>
    </FormPage>
  );
}
