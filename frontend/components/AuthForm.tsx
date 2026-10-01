"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, errorMessages, safeNext } from "@/lib/api";
import { useAuth } from "./AuthProvider";
import { ErrorList, Field, FormPage } from "./forms";

export default function AuthForm({ mode, next }: { mode: "login" | "register"; next?: string }) {
  const router = useRouter();
  const { refresh } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const isLogin = mode === "login";
  const dest = safeNext(next, "/");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErrors([]);
    try {
      await api(isLogin ? "/auth/login" : "/auth/register", { json: { email, password } });
      const me = await refresh();
      if (isLogin && me?.is_verified_reporter !== false) router.push(dest);
      else router.push(`/verify?next=${encodeURIComponent(dest)}`);
      router.refresh();
    } catch (err) {
      setErrors(errorMessages(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <FormPage
      title={isLogin ? "Log in" : "Create your account"}
      intro={isLogin ? undefined : "You'll verify your email and phone next. We do this so reports come from real people, which protects honest sellers."}
    >
      <form onSubmit={submit} className="space-y-5">
        <Field label="Email" htmlFor="email">
          <input id="email" type="email" className="input" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
        </Field>
        <Field label="Password" htmlFor="password" hint={isLogin ? undefined : "At least 8 characters. Avoid common passwords."}>
          <input id="password" type="password" className="input" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={isLogin ? 1 : 8} autoComplete={isLogin ? "current-password" : "new-password"} />
        </Field>
        <ErrorList errors={errors} />
        <button className="btn btn-primary w-full" disabled={busy}>{busy ? "Please wait..." : isLogin ? "Log in" : "Create account"}</button>
      </form>
      <p className="mt-5 text-slate-700">
        {isLogin ? "New here? " : "Already have an account? "}
        <Link className="link" href={`${isLogin ? "/register" : "/login"}?next=${encodeURIComponent(dest)}`}>
          {isLogin ? "Create an account" : "Log in"}
        </Link>
      </p>
    </FormPage>
  );
}
