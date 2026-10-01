"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, errorMessages } from "@/lib/api";
import { categoryName, platformName } from "@/lib/labels";
import type { MyReport } from "@/lib/types";
import { ErrorList, FormPage } from "./forms";
import RequireVerified from "./RequireVerified";

function List() {
  const [items, setItems] = useState<MyReport[] | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  useEffect(() => {
    api<MyReport[]>("/me/reports").then(setItems).catch((e) => setErrors(errorMessages(e)));
  }, []);

  if (errors.length) return <ErrorList errors={errors} />;
  if (!items) return <p role="status">Loading...</p>;
  if (!items.length) return <p className="text-lg">You haven't reported anything yet. <Link className="link" href="/report">Report a page</Link>.</p>;
  return (
    <ul className="divide-y divide-slate-200 border-y border-slate-200">
      {items.map((r) => (
        <li key={r.id} className="py-4">
          <p className="text-lg font-semibold">@{r.handle} <span className="font-normal text-slate-600">on {platformName(r.platform)}</span></p>
          <p className="text-slate-700">{categoryName(r.category)}</p>
          <p className="mt-1"><strong>{r.status_text}</strong>, {r.evidence_count} file{r.evidence_count === 1 ? "" : "s"}, sent {new Date(r.created_at).toLocaleDateString("en-KE")}</p>
        </li>
      ))}
    </ul>
  );
}

export default function MyReports() {
  return (
    <FormPage title="My reports" intro="Only you can see this list. Your name is never shown on public pages.">
      <RequireVerified needVerified={false}><List /></RequireVerified>
    </FormPage>
  );
}
