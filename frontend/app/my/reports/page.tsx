import type { Metadata } from "next";
import MyReports from "@/components/MyReports";

export const metadata: Metadata = { title: "My reports", robots: { index: false } };

export default function Page() {
  return <MyReports />;
}
