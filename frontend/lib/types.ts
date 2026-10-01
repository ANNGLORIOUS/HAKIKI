export type Platform = "tiktok" | "instagram" | "facebook" | "whatsapp" | "other";

export type Label =
  | "no_reports" | "needs_checking" | "reports_review" | "reported_multiple"
  | "vouched" | "mixed" | "disputed" | "resolved";

export interface PageSummary {
  platform: Platform;
  handle: string;
  profile_url: string;
  label: Label;
  label_text: string;
  verified_owner: boolean;
  reports_published: number;
  vouches: number;
}

export interface PageDetail extends PageSummary {
  found: true;
  explanation: string;
  why_listed: string;
  reports_with_supported_evidence: number;
  categories: Record<string, number>;
  check_requests: number;
  linked_pages_count: number;
  payment_identifiers: { type: string; masked: string }[];
  disputed: boolean;
  last_reviewed: string;
  safety_tips: string[];
  disclaimer: string;
  indexable: boolean;
}

export interface PageNotFound {
  found: false;
  platform: Platform;
  handle: string;
  label: Label;
  label_text: string;
  explanation: string;
  safety_tips: string[];
  disclaimer: string;
}

export interface HandleSearch {
  query_type: "handle";
  query: string;
  found: boolean;
  results: PageSummary[];
  safety_tips: string[];
  message: string;
  disclaimer: string;
}

export interface PaymentSearch {
  query_type: "payment";
  matched: boolean;
  report_count: number;
  page_count: number;
  pages: PageSummary[];
  message: string;
  safety_tips: string[];
  disclaimer: string;
}

export interface User {
  id: number;
  email: string;
  phone: string | null;
  phone_verified: boolean;
  email_verified: boolean;
  is_verified_reporter: boolean;
  role: "reporter" | "seller" | "moderator";
}

export interface MyReport {
  id: number;
  platform: Platform;
  handle: string;
  category: string;
  status: string;
  status_text: string;
  evidence_count: number;
  created_at: string;
}
