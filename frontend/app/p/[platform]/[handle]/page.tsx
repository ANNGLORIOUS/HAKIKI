import type { Metadata } from "next";
import Link from "next/link";
import LabelBadge from "@/components/LabelBadge";
import SafetyTips from "@/components/SafetyTips";
import { categoryName, platformName } from "@/lib/labels";
import { serverGet } from "@/lib/server-api";
import type { PageDetail, PageNotFound } from "@/lib/types";

type Props = { params: { platform: string; handle: string } };
type Detail = PageDetail | PageNotFound;

const load = (p: Props["params"]) =>
  serverGet<Detail>(`/pages/${encodeURIComponent(p.platform)}/${encodeURIComponent(decodeURIComponent(p.handle))}/`);

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { data } = await load(params);
  const handle = decodeURIComponent(params.handle);
  // Only pages that passed moderation and the report threshold are indexed by search engines.
  const indexable = !!data && data.found && data.indexable;
  return {
    title: `@${handle} on ${platformName(params.platform)}`,
    description: `User reports, evidence status and vouches for @${handle} on ${platformName(params.platform)}.`,
    robots: indexable ? { index: true, follow: true } : { index: false, follow: true },
  };
}

function date(iso: string) {
  return new Date(iso).toLocaleDateString("en-KE", { year: "numeric", month: "long", day: "numeric" });
}

export default async function ProfilePage({ params }: Props) {
  const { data, detail } = await load(params);
  const handle = decodeURIComponent(params.handle);
  const qs = `platform=${encodeURIComponent(params.platform)}&handle=${encodeURIComponent(handle)}`;

  if (!data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-14">
        <p role="alert" className="rounded-lg border border-alert bg-alert-tint px-4 py-3 text-alert">
          {detail || "We couldn't load this page. Please try again."}
        </p>
      </div>
    );
  }

  const found = data.found;
  const d = found ? (data as PageDetail) : null;
  const categories = d ? Object.entries(d.categories) : [];

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <p className="text-slate-600">{platformName(params.platform)}</p>
      <h1 className="break-all text-4xl font-bold sm:text-5xl">@{handle}</h1>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <LabelBadge label={data.label} text={data.label_text} big />
        {d?.verified_owner && <span className="rounded-md border-2 border-brand px-2 py-1 text-sm font-semibold text-brand">Verified owner</span>}
      </div>
      <p className="mt-4 text-lg text-slate-800">{data.explanation}</p>

      {d?.disputed && (
        <p className="mt-4 border-l-4 border-dispute bg-dispute-tint px-4 py-3 text-slate-800">
          The verified owner has disputed a report. It stays visible while moderators review it.
        </p>
      )}

      {d && (
        <dl className="mt-8 grid grid-cols-2 gap-x-6 gap-y-5 border-y border-slate-200 py-6 sm:grid-cols-4">
          <div><dt className="text-sm text-slate-600">Published reports</dt><dd className="text-3xl font-bold">{d.reports_published}</dd></div>
          <div><dt className="text-sm text-slate-600">With evidence reviewed</dt><dd className="text-3xl font-bold">{d.reports_with_supported_evidence}</dd></div>
          <div><dt className="text-sm text-slate-600">Buyer vouches</dt><dd className="text-3xl font-bold">{d.vouches}</dd></div>
          <div><dt className="text-sm text-slate-600">Check requests</dt><dd className="text-3xl font-bold">{d.check_requests}</dd></div>
        </dl>
      )}

      {d && categories.length > 0 && (
        <section className="mt-8">
          <h2 className="text-2xl font-bold">What people reported</h2>
          <ul className="mt-3 space-y-1.5 text-lg">
            {categories.map(([c, n]) => <li key={c}>{categoryName(c)}: <strong>{n}</strong></li>)}
          </ul>
        </section>
      )}

      {d && (d.payment_identifiers.length > 0 || d.linked_pages_count > 0) && (
        <section className="mt-8">
          <h2 className="text-2xl font-bold">Payment details in reports</h2>
          {d.payment_identifiers.length > 0 && (
            <ul className="mt-3 flex flex-wrap gap-2">
              {d.payment_identifiers.map((p) => (
                <li key={p.type + p.masked} className="rounded-md border border-slate-300 bg-white px-3 py-1 font-mono text-sm">{p.masked}</li>
              ))}
            </ul>
          )}
          {d.linked_pages_count > 0 && (
            <p className="mt-3 text-lg text-slate-800">
              The same payment details also appear in reports about {d.linked_pages_count} other page{d.linked_pages_count === 1 ? "" : "s"}.
              Search the full number to see them.
            </p>
          )}
          <p className="mt-2 text-sm text-slate-600">Numbers are partly hidden to protect privacy. Search a full number to check it.</p>
        </section>
      )}

      <section className="mt-8 flex flex-wrap gap-3">
        <Link href={`/report?${qs}`} className="btn btn-primary">I was scammed by this page</Link>
        <Link href={`/vouch?${qs}`} className="btn btn-secondary">I bought and received my order</Link>
        <Link href={`/check?${qs}`} className="btn btn-secondary">Ask others to check it</Link>
      </section>

      <div className="mt-10"><SafetyTips tips={data.safety_tips} /></div>

      <details className="mt-8 border-t border-slate-200 pt-4">
        <summary className="cursor-pointer text-lg font-semibold">Why am I seeing this?</summary>
        <p className="mt-3 text-slate-800">
          {d?.why_listed ?? "Nobody has submitted reports or vouches for this account yet. You are seeing this page because you searched for it."}
        </p>
        {d && <p className="mt-2 text-sm text-slate-600">Last reviewed {date(d.last_reviewed)}.</p>}
      </details>

      <p className="mt-6 text-sm text-slate-600">{data.disclaimer}</p>
      <p className="mt-4 text-sm text-slate-700">
        Own this page? <Link className="link" href={`/claim/${params.platform}/${encodeURIComponent(handle)}`}>Claim it</Link> to respond to reports.
      </p>
    </div>
  );
}
