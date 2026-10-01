import type { Metadata } from "next";
import { VouchForm } from "@/components/SimpleForms";

export const metadata: Metadata = { title: "Vouch for a seller", robots: { index: false } };

export default function Page({ searchParams }: { searchParams: { platform?: string; handle?: string } }) {
  return <VouchForm initialPlatform={searchParams.platform} initialHandle={searchParams.handle} />;
}
