import Link from "next/link";
import SearchBox from "@/components/SearchBox";

export default function Home() {
  return (
    <>
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-5xl px-4 py-14 sm:py-20">
          <h1 className="max-w-3xl text-4xl font-bold leading-tight sm:text-6xl">Check a seller before you send the money.</h1>
          <p className="mt-5 max-w-2xl text-lg text-slate-700 sm:text-xl">
            Search an Instagram or TikTok shop, or the phone number or Till you were asked to pay. See what other buyers reported, and what evidence backs it up.
          </p>
          <div className="mt-8 max-w-2xl"><SearchBox large /></div>
          <p className="mt-3 text-sm text-slate-600">
            Try <span className="font-medium text-ink">@shopname</span>, <span className="font-medium text-ink">0712 345 678</span> or{" "}
            <span className="font-medium text-ink">123456</span> (a Till number).
          </p>
        </div>
      </section>

      <section className="mx-auto grid max-w-5xl gap-10 px-4 py-14 md:grid-cols-3">
        <div>
          <h2 className="text-2xl font-bold">Got scammed?</h2>
          <p className="mt-2 text-slate-700">Report the page with your M-Pesa message and screenshots so the next buyer sees a warning.</p>
          <Link href="/report" className="btn btn-primary mt-4">Report a page</Link>
        </div>
        <div>
          <h2 className="text-2xl font-bold">Bought and it went well?</h2>
          <p className="mt-2 text-slate-700">Vouch for honest sellers with proof of your order. It helps good businesses stand out.</p>
          <Link href="/vouch" className="btn btn-secondary mt-4">Vouch for a seller</Link>
        </div>
        <div>
          <h2 className="text-2xl font-bold">Not sure yet?</h2>
          <p className="mt-2 text-slate-700">Haven't paid but the page looks off? Ask others to check it before you decide.</p>
          <Link href="/check" className="btn btn-secondary mt-4">Ask for a check</Link>
        </div>
      </section>

      <section className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-5xl px-4 py-14">
          <h2 className="text-3xl font-bold">What we do and don't say</h2>
          <div className="mt-6 grid gap-8 md:grid-cols-2">
            <p className="text-lg text-slate-800">
              A report is what a person says happened. Evidence is what supports it. A moderator decides whether it meets our standard before anything is
              published. We never call a seller a scammer, and one report alone never puts a warning on a page.
            </p>
            <p className="text-lg text-slate-800">
              Sellers can prove they own their page, respond to reports and appeal decisions. And "no reports yet" only means nobody has reported it,
              so check the tips on every result before you pay.{" "}
              <Link href="/how-we-decide" className="link">Read how we decide</Link>.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
