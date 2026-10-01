import type { Metadata } from "next";
import AuthForm from "@/components/AuthForm";

export const metadata: Metadata = { title: "Create account", robots: { index: false } };

export default function Page({ searchParams }: { searchParams: { next?: string } }) {
  return <AuthForm mode="register" next={searchParams.next} />;
}
