import Link from "next/link";
import { platformName } from "@/lib/labels";
import type { PageSummary } from "@/lib/types";
import LabelBadge from "./LabelBadge";

export default function PageRow({ page }: { page: PageSummary }) {
  return (
    <li>
      <Link
        href={`/p/${page.platform}/${page.handle}`}
        className="flex flex-wrap items-center justify-between gap-3 py-4 hover:bg-slate-50 sm:px-2"
      >
        <div>
          <p className="text-lg font-semibold">@{page.handle}</p>
          <p className="text-sm text-slate-600">
            {platformName(page.platform)}, {page.reports_published} published report{page.reports_published === 1 ? "" : "s"},{" "}
            {page.vouches} vouch{page.vouches === 1 ? "" : "es"}
          </p>
        </div>
        <LabelBadge label={page.label} text={page.label_text} />
      </Link>
    </li>
  );
}
