import type { Metadata } from "next";
import ClaimPage from "@/components/ClaimPage";

export const metadata: Metadata = { title: "Claim a page", robots: { index: false } };

export default function Page({ params }: { params: { platform: string; handle: string } }) {
  return <ClaimPage platform={params.platform} handle={decodeURIComponent(params.handle)} />;
}
