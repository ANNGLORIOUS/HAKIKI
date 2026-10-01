import type { Metadata } from "next";
import VerifyFlow from "@/components/VerifyFlow";

export const metadata: Metadata = { title: "Verify your account", robots: { index: false } };

export default function Page({ searchParams }: { searchParams: { next?: string } }) {
  return <VerifyFlow next={searchParams.next} />;
}
