import type { Metadata } from "next";
import { CopyrightForm } from "@/components/SimpleForms";

export const metadata: Metadata = { title: "Stolen video complaint", robots: { index: false } };

export default function Page({ searchParams }: { searchParams: { platform?: string; handle?: string } }) {
  return <CopyrightForm initialPlatform={searchParams.platform} initialHandle={searchParams.handle} />;
}
