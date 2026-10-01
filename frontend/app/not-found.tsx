import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-16">
      <h1 className="text-4xl font-bold">We couldn't find that page</h1>
      <p className="mt-3 text-lg text-slate-700">The link may be wrong or out of date.</p>
      <Link href="/" className="btn btn-primary mt-6">Search for a seller</Link>
    </div>
  );
}
