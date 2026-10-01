import type { Metadata } from "next";
import { CheckForm } from "@/components/SimpleForms";

export const metadata: Metadata = { title: "Ask for a check", robots: { index: false } };

export default function Page({ searchParams }: { searchParams: { platform?: string; handle?: string } }) {
  return <CheckForm initialPlatform={searchParams.platform} initialHandle={searchParams.handle} />;
}
