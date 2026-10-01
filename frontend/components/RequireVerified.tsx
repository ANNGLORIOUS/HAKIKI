"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "./AuthProvider";

/** Shows its children only to logged-in users (and, by default, only after phone + email are verified). */
export default function RequireVerified({ children, needVerified = true }: { children: React.ReactNode; needVerified?: boolean }) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const next = encodeURIComponent(pathname);

  if (loading) return <p className="text-slate-600" role="status">Loading...</p>;
  if (!user) {
    return (
      <div>
        <p className="text-lg">Please log in first. It keeps reports accountable and protects sellers from fake ones.</p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link href={`/login?next=${next}`} className="btn btn-primary">Log in</Link>
          <Link href={`/register?next=${next}`} className="btn btn-secondary">Create account</Link>
        </div>
      </div>
    );
  }
  if (needVerified && !user.is_verified_reporter) {
    return (
      <div>
        <p className="text-lg">
          Please verify your {!user.email_verified && !user.phone_verified ? "email and phone number" : !user.email_verified ? "email" : "phone number"} first.
          It takes about a minute.
        </p>
        <Link href={`/verify?next=${next}`} className="btn btn-primary mt-4">Verify now</Link>
      </div>
    );
  }
  return <>{children}</>;
}
