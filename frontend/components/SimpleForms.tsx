"use client";

import { useState } from "react";
import { api, errorMessages } from "@/lib/api";
import { compressImage } from "@/lib/image";
import { ErrorList, Field, FormPage, PlatformHandle, SuccessBox } from "./forms";
import RequireVerified from "./RequireVerified";

interface Initial { initialPlatform?: string; initialHandle?: string }

function useForm(initial: Initial) {
  const [platform, setPlatform] = useState(initial.initialPlatform || "instagram");
  const [handle, setHandle] = useState(initial.initialHandle || "");
  const [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [doneMsg, setDoneMsg] = useState("");
  async function run(fn: () => Promise<{ message?: string }>) {
    setBusy(true); setErrors([]);
    try { const r = await fn(); setDoneMsg(r.message || "Thank you."); window.scrollTo({ top: 0 }); }
    catch (e) { setErrors(errorMessages(e)); }
    finally { setBusy(false); }
  }
  return { platform, setPlatform, handle, setHandle, busy, errors, setErrors, doneMsg, run };
}

export function VouchForm(props: Initial) {
  const f = useForm(props);
  const [comment, setComment] = useState("");
  const [proof, setProof] = useState<File | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!proof) { f.setErrors(["Attach proof of your purchase, such as your M-Pesa message or a delivery photo."]); return; }
    const fd = new FormData();
    fd.append("platform", f.platform); fd.append("handle", f.handle); fd.append("comment", comment); fd.append("proof", proof);
    f.run(() => api("/vouches", { form: fd }));
  }

  return (
    <FormPage title="Vouch for a seller" intro="Bought from a page and got what you paid for? Show proof so other buyers can trust it. Vouches appear once a moderator checks your proof.">
      <RequireVerified>
        {f.doneMsg ? <SuccessBox title={f.doneMsg} /> : (
          <form onSubmit={submit} className="space-y-6">
            <PlatformHandle platform={f.platform} handle={f.handle} onPlatform={f.setPlatform} onHandle={f.setHandle} />
            <Field label="Proof of purchase" htmlFor="proof" hint="Your M-Pesa message, or a photo of the delivered item.">
              <input id="proof" type="file" accept="image/*" className="block w-full text-base file:mr-3 file:rounded-lg file:border-0 file:bg-brand file:px-4 file:py-2.5 file:font-semibold file:text-white"
                onChange={async (e) => { const file = e.target.files?.[0]; setProof(file ? await compressImage(file) : null); }} />
            </Field>
            <Field label="How did it go? (optional)" htmlFor="comment">
              <textarea id="comment" className="input min-h-[100px]" value={comment} onChange={(e) => setComment(e.target.value)} maxLength={1000} />
            </Field>
            <ErrorList errors={f.errors} />
            <button className="btn btn-primary" disabled={f.busy}>{f.busy ? "Sending..." : "Submit vouch"}</button>
          </form>
        )}
      </RequireVerified>
    </FormPage>
  );
}

export function CheckForm(props: Initial) {
  const f = useForm(props);
  const [note, setNote] = useState("");

  return (
    <FormPage title="Ask others to check a page" intro="Haven't paid yet and want a second opinion? Add the page here. Questions don't count as evidence and never count against a seller.">
      <RequireVerified needVerified={false}>
        {f.doneMsg ? <SuccessBox title={f.doneMsg} /> : (
          <form onSubmit={(e) => { e.preventDefault(); f.run(() => api("/check-requests", { json: { platform: f.platform, handle: f.handle, note } })); }} className="space-y-6">
            <PlatformHandle platform={f.platform} handle={f.handle} onPlatform={f.setPlatform} onHandle={f.setHandle} />
            <Field label="What made you unsure? (optional)" htmlFor="note" hint="For example: they want a deposit first, or the videos look copied.">
              <input id="note" className="input" value={note} onChange={(e) => setNote(e.target.value)} maxLength={500} />
            </Field>
            <ErrorList errors={f.errors} />
            <button className="btn btn-primary" disabled={f.busy}>{f.busy ? "Sending..." : "Ask for a check"}</button>
          </form>
        )}
      </RequireVerified>
    </FormPage>
  );
}

export function CopyrightForm(props: Initial) {
  const f = useForm(props);
  const [original, setOriginal] = useState("");
  const [infringing, setInfringing] = useState("");
  const [description, setDescription] = useState("");

  return (
    <FormPage title="Stolen video complaint" intro="Is a page using your videos or photos to sell things without your permission? This is separate from a scam report and is reviewed on its own.">
      <RequireVerified>
        {f.doneMsg ? <SuccessBox title={f.doneMsg} /> : (
          <form onSubmit={(e) => { e.preventDefault(); f.run(() => api("/copyright-complaints", { json: { platform: f.platform, handle: f.handle, original_url: original, infringing_url: infringing, description } })); }} className="space-y-6">
            <PlatformHandle platform={f.platform} handle={f.handle} onPlatform={f.setPlatform} onHandle={f.setHandle} />
            <Field label="Link to your original video or photo" htmlFor="orig"><input id="orig" type="url" className="input" value={original} onChange={(e) => setOriginal(e.target.value)} required placeholder="https://" /></Field>
            <Field label="Link to the post that copies it" htmlFor="inf"><input id="inf" type="url" className="input" value={infringing} onChange={(e) => setInfringing(e.target.value)} required placeholder="https://" /></Field>
            <Field label="Explain" htmlFor="desc" hint="Why is this yours, and how is the other page using it? At least 20 characters."><textarea id="desc" className="input min-h-[120px]" value={description} onChange={(e) => setDescription(e.target.value)} required minLength={20} maxLength={2000} /></Field>
            <ErrorList errors={f.errors} />
            <button className="btn btn-primary" disabled={f.busy}>{f.busy ? "Sending..." : "Submit complaint"}</button>
          </form>
        )}
      </RequireVerified>
    </FormPage>
  );
}
