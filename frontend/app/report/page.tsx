import type { Metadata } from "next";
import ReportForm from "@/components/ReportForm";

export const metadata: Metadata = { title: "Report a page", robots: { index: false } };

export default function Page({ searchParams }: { searchParams: { platform?: string; handle?: string } }) {
  return <ReportForm initialPlatform={searchParams.platform} initialHandle={searchParams.handle} />;
}
