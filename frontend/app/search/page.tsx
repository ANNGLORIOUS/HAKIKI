import type { Metadata } from "next";
import Link from "next/link";
import PageRow from "@/components/PageRow";
import SafetyTips from "@/components/SafetyTips";
import SearchBox from "@/components/SearchBox";
import { serverGet } from "@/lib/server-api";
import type { HandleSearch, PaymentSearch } from "@/lib/types";

export const metadata: Metadata = { title: "Search results", robots: { index: false, follow: false } };

export default async function SearchPage({ searchParams }: { searchParams: { q?: string } }) {
  const q = (searchParams.q || "").trim();
  const res = q ? await serverGet<HandleSearch | PaymentSearch>(`/search/?q=${encodeURIComponent(q)}`) : null;
  const data = res?.data;

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <SearchBox initial={q} />

      {!q && <p className="mt-8 text-lg text-slate-700">Enter a seller's handle, profile link, phone number or Till number.</p>}

      {res && !data && (
        <p role="alert" className="mt-8 rounded-lg border border-alert bg-alert-tint px-4 py-3 text-alert">
          {res.detail || "We couldn't run that search. Please try again."}
        </p>
      )}

      {data?.query_type === "handle" && (
        <div className="mt-8">
          {data.found ? (
            <>
              <h1 className="text-3xl font-bold">Results for {data.query}</h1>
              <ul className="mt-4 divide-y divide-slate-200 border-y border-slate-200">
                {data.results.map((p) => <PageRow key={p.platform + p.handle} page={p} />)}
              </ul>
              <p className="mt-4 text-sm text-slate-600">{data.disclaimer}</p>
            </>
          ) : (
            <>
              <h1 className="text-3xl font-bold">No reports yet for {data.query}</h1>
              <p className="mt-3 text-lg text-slate-800">{data.message}</p>
              <div className="mt-6"><SafetyTips tips={data.safety_tips} /></div>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link href={`/check?handle=${encodeURIComponent(data.query)}`} className="btn btn-primary">Ask others to check this page</Link>
                <Link href={`/report?handle=${encodeURIComponent(data.query)}`} className="btn btn-secondary">I was scammed by this page</Link>
              </div>
            </>
          )}
        </div>
      )}

      {data?.query_type === "payment" && (
        <div className="mt-8">
          {data.matched ? (
            <>
              <h1 className="text-3xl font-bold">
                This number appears in {data.report_count} published report{data.report_count === 1 ? "" : "s"}
              </h1>
              <p className="mt-3 text-lg text-slate-800">
                The reports involve {data.page_count} page{data.page_count === 1 ? "" : "s"}. These are allegations by users, not court findings. Look at each page to see the evidence status.
              </p>
              <ul className="mt-4 divide-y divide-slate-200 border-y border-slate-200">
                {data.pages.map((p) => <PageRow key={p.platform + p.handle} page={p} />)}
              </ul>
              <p className="mt-4 text-sm text-slate-600">{data.disclaimer}</p>
            </>
          ) : (
            <>
              <h1 className="text-3xl font-bold">No published reports for this number</h1>
              <p className="mt-3 text-lg text-slate-800">{data.message}</p>
              <div className="mt-6"><SafetyTips tips={data.safety_tips} /></div>
              <p className="mt-6 text-slate-700">
                Already lost money to this number? <Link href="/report" className="link">Report it</Link>.
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
