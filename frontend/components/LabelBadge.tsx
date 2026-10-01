import { LABELS } from "@/lib/labels";
import type { Label } from "@/lib/types";

/** Public status label. Text plus border, so it never depends on colour alone. */
export default function LabelBadge({ label, text, big = false }: { label: Label; text?: string; big?: boolean }) {
  const l = LABELS[label] ?? LABELS.no_reports;
  return (
    <span className={`inline-block rounded-md border-2 font-semibold ${l.cls} ${big ? "px-3 py-1.5 text-base" : "px-2 py-0.5 text-sm"}`}>
      {text || l.text}
    </span>
  );
}
