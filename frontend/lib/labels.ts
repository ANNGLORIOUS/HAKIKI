import type { Label, Platform } from "./types";

export const LABELS: Record<Label, { text: string; cls: string }> = {
  no_reports: { text: "No reports yet", cls: "border-slate-300 bg-white text-slate-700" },
  needs_checking: { text: "Needs checking", cls: "border-info bg-info-tint text-info" },
  reports_review: { text: "Reports received, review ongoing", cls: "border-caution bg-caution-tint text-caution" },
  reported_multiple: { text: "Reported by multiple users", cls: "border-alert bg-alert-tint text-alert" },
  vouched: { text: "Vouched by buyers", cls: "border-brand bg-brand-tint text-brand" },
  mixed: { text: "Mixed: vouches and reports", cls: "border-caution bg-caution-tint text-caution" },
  disputed: { text: "Disputed by the seller", cls: "border-dispute bg-dispute-tint text-dispute" },
  resolved: { text: "Resolved", cls: "border-slate-400 bg-slate-50 text-slate-700" },
};

export const PLATFORMS: { value: Platform; label: string }[] = [
  { value: "instagram", label: "Instagram" },
  { value: "tiktok", label: "TikTok" },
  { value: "facebook", label: "Facebook" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "other", label: "Other" },
];

export const platformName = (p: string) => PLATFORMS.find((x) => x.value === p)?.label ?? p;

export const CATEGORIES: { value: string; label: string }[] = [
  { value: "non_delivery", label: "I paid and never received the item" },
  { value: "deposit_blocked", label: "I paid a deposit, then they blocked me" },
  { value: "fake_item", label: "The item was fake or counterfeit" },
  { value: "wrong_item", label: "I received a very different item" },
  { value: "stolen_video", label: "The page uses someone else's videos" },
  { value: "impersonation", label: "The page pretends to be another business" },
];

export const categoryName = (c: string) => CATEGORIES.find((x) => x.value === c)?.label ?? c;

export const PAYMENT_TYPES = [
  { value: "send_money", label: "M-Pesa Send Money (phone number)" },
  { value: "till", label: "Till number (Buy Goods)" },
  { value: "paybill", label: "Paybill number" },
  { value: "bank", label: "Bank account" },
];

export const EVIDENCE_KINDS = [
  { value: "mpesa_message", label: "M-Pesa message" },
  { value: "chat_screenshot", label: "Chat screenshot" },
  { value: "page_screenshot", label: "Page or video screenshot" },
  { value: "video", label: "Video" },
  { value: "other", label: "Other" },
];
