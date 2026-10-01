import type { Metadata } from "next";
import AuthForm from "@/components/AuthForm";

export const metadata: Metadata = { title: "Log in", robots: { index: false } };

export default function Page({ searchParams }: { searchParams: { next?: string } }) {
  return <AuthForm mode="login" next={searchParams.next} />;
}
