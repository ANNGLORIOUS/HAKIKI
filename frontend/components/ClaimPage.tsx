"use client";

import { useState } from "react";
import { api, errorMessages } from "@/lib/api";
import { platformName } from "@/lib/labels";
import { ErrorList, FormPage } from "./forms";
import RequireVerified from "./RequireVerified";

export default function ClaimPage({ platform, handle }: { platform: string; handle: string }) {
  const [result, setResult] = useState<{ code: string; instructions: string } | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  async function claim() {
    setBusy(true); setErrors([]);
    try { setResult(await api(`/pages/${platform}/${encodeURIComponent(handle)}/claim`, { method: "POST", json: {} })); }
    catch (e) { setErrors(errorMessages(e)); } finally { setBusy(false); }
  }

  return (
    <FormPage title={`Claim @${handle}`} intro={`Prove you own this ${platformName(platform)} page. Once confirmed, you can respond to reports and dispute any that are wrong.`}>
      <RequireVerified needVerified>
        {result ? (
          <div className="space-y-4">
            <p className="text-lg">Add this code to your profile bio:</p>
            <p className="inline-block rounded-lg border-2 border-brand bg-brand-tint px-4 py-3 font-mono text-2xl font-bold">{result.code}</p>
            <p className="text-slate-800">{result.instructions}</p>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-slate-800">We'll give you a short code to put in your bio. A moderator checks it, then marks you as the verified owner. You don't need a registered business.</p>
            <ErrorList errors={errors} />
            <button className="btn btn-primary" onClick={claim} disabled={busy}>{busy ? "Please wait..." : "Get my code"}</button>
          </div>
        )}
      </RequireVerified>
    </FormPage>
  );
}
