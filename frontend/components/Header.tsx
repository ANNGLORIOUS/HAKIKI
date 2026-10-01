"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useAuth } from "./AuthProvider";

const NAV = [
  { href: "/report", label: "Report a page" },
  { href: "/vouch", label: "Vouch for a seller" },
  { href: "/check", label: "Ask for a check" },
  { href: "/how-we-decide", label: "How we decide" },
];

export default function Header() {
  const { user, loading, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  useEffect(() => setOpen(false), [pathname]);

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link href="/" className="font-display text-2xl font-bold text-brand" aria-label="Hakiki home">
          Hakiki
        </Link>
        <button
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium md:hidden"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
          aria-controls="main-nav"
        >
          Menu
        </button>
        <nav
          id="main-nav"
          className={`${open ? "flex" : "hidden"} absolute left-0 right-0 top-14 z-10 flex-col gap-1 border-b border-slate-200 bg-white px-4 py-3 md:static md:flex md:flex-row md:items-center md:gap-5 md:border-0 md:p-0`}
        >
          {NAV.map((n) => (
            <Link key={n.href} href={n.href} className={`py-1.5 text-sm font-medium hover:text-brand ${pathname === n.href ? "text-brand" : "text-slate-700"}`}>
              {n.label}
            </Link>
          ))}
          <span className="hidden h-5 w-px bg-slate-300 md:block" />
          {loading ? null : user ? (
            <>
              <Link href="/my/reports" className="py-1.5 text-sm font-medium text-slate-700 hover:text-brand">My reports</Link>
              <button
                className="py-1.5 text-left text-sm font-medium text-slate-700 hover:text-brand"
                onClick={async () => { await logout(); router.push("/"); router.refresh(); }}
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="py-1.5 text-sm font-medium text-slate-700 hover:text-brand">Log in</Link>
              <Link href="/register" className="btn btn-primary !py-1.5">Create account</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
