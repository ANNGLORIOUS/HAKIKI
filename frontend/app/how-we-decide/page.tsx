import type { Metadata } from "next";
import LabelBadge from "@/components/LabelBadge";
import type { Label } from "@/lib/types";

export const metadata: Metadata = { title: "How we decide" };

const ROWS: { label: Label; when: string }[] = [
  { label: "no_reports", when: "Nobody has submitted anything about the account. This is not a sign the seller is safe." },
  { label: "needs_checking", when: "Someone asked whether the page is legitimate. Questions are opinions, not evidence, so this never counts against a seller." },
  { label: "reports_review", when: "Reports exist but moderators haven't finished reviewing them, or fewer than three independent users reported with supporting evidence." },
  { label: "reported_multiple", when: "Three or more different users reported with evidence that a moderator reviewed and supported." },
  { label: "vouched", when: "Several buyers gave proof that they received their orders, and there are no published reports." },
  { label: "mixed", when: "The page has both buyer vouches and published reports." },
  { label: "disputed", when: "The verified owner has challenged a report. The report stays visible during the review." },
  { label: "resolved", when: "A report was reviewed and resolved by moderators, for example removed after a successful dispute." },
];

export default function HowWeDecide() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-4xl font-bold">How we decide what to publish</h1>
      <p className="mt-4 text-lg text-slate-800">
        Hakiki helps people investigate online sellers using reports, evidence, verification and dispute history. We do not identify scammers.
        We show what users reported and how well the evidence holds up.
      </p>

      <h2 className="mt-10 text-2xl font-bold">Reports, evidence and decisions are different things</h2>
      <p className="mt-3 text-lg text-slate-800">
        A report is what a person says happened. Evidence, such as an M-Pesa message or a chat screenshot, is what supports it. A moderator then decides
        whether the report meets our standard for publication. Only then does it count on a public page. Nothing is published from a single report.
      </p>

      <h2 className="mt-10 text-2xl font-bold">What each label means</h2>
      <ul className="mt-4 divide-y divide-slate-200 border-y border-slate-200">
        {ROWS.map((r) => (
          <li key={r.label} className="grid gap-2 py-4 sm:grid-cols-[260px_1fr] sm:gap-6">
            <div><LabelBadge label={r.label} /></div>
            <p className="text-slate-800">{r.when}</p>
          </li>
        ))}
      </ul>

      <h2 className="mt-10 text-2xl font-bold">Fairness for sellers</h2>
      <p className="mt-3 text-lg text-slate-800">
        A seller can prove they own a page by placing a code in their bio, then dispute any published report with their own proof. You don't need a registered
        business to do this. Reports stay visible while a dispute is reviewed, and each decision can be appealed once, to a different moderator.
        Every moderation action is recorded in a log that nobody can edit.
      </p>

      <h2 className="mt-10 text-2xl font-bold">Your privacy</h2>
      <p className="mt-3 text-lg text-slate-800">
        Reporters are never named publicly. Phone and payment numbers are stored securely and shown only in part. Searching a full number tells you whether it
        was reported, and how many times, without revealing anything else about the reporters.
      </p>

      <h2 className="mt-10 text-2xl font-bold">What we can't do</h2>
      <p className="mt-3 text-lg text-slate-800">
        We can't recover money or remove a page from TikTok or Instagram. If you lost money, contact Safaricom about the M-Pesa transaction as soon as you can,
        report the account on the platform, and consider reporting to the police or the Directorate of Criminal Investigations.
      </p>
    </div>
  );
}
