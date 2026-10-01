import Link from "next/link";

export default function Footer() {
  return (
    <footer className="mt-16 border-t border-slate-200 bg-white">
      <div className="mx-auto max-w-5xl px-4 py-8 text-sm text-slate-600">
        <p className="max-w-2xl">
          Hakiki shares reports submitted by users, along with the evidence behind them. A report is an allegation, not a
          verdict, and no reports found does not mean a seller is safe.
        </p>
        <p className="mt-3">
          <Link href="/how-we-decide" className="link">How we decide what to publish</Link>
        </p>
      </div>
    </footer>
  );
}
