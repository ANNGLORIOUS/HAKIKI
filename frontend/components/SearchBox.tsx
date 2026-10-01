"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function SearchBox({ initial = "", large = false }: { initial?: string; large?: boolean }) {
  const [q, setQ] = useState(initial);
  const router = useRouter();

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const v = q.trim();
    if (v) router.push(`/search?q=${encodeURIComponent(v)}`);
  }

  return (
    <form onSubmit={submit} role="search" className="w-full">
      <label htmlFor="q" className="sr-only">Seller handle, profile link, phone number or Till number</label>
      <div className={`flex overflow-hidden rounded-xl border-2 border-brand bg-white focus-within:ring-4 focus-within:ring-brand/20 ${large ? "shadow-sm" : ""}`}>
        <input
          id="q"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="@shopname, profile link, phone or Till number"
          className={`min-w-0 flex-1 bg-transparent px-4 text-ink placeholder-slate-400 focus:outline-none ${large ? "py-4 text-lg" : "py-3 text-base"}`}
          autoComplete="off"
          inputMode="search"
          maxLength={200}
        />
        <button type="submit" className={`bg-brand px-5 font-semibold text-white hover:bg-brand-dark focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-white ${large ? "text-lg" : "text-base"}`}>
          Check
        </button>
      </div>
    </form>
  );
}
