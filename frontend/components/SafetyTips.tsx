export default function SafetyTips({ tips, title = "Before you pay" }: { tips: string[]; title?: string }) {
  if (!tips?.length) return null;
  return (
    <section aria-labelledby="tips-h" className="border-l-4 border-brand bg-brand-tint px-5 py-4">
      <h2 id="tips-h" className="text-xl font-bold">{title}</h2>
      <ul className="mt-2 list-disc space-y-1.5 pl-5 text-slate-800">
        {tips.map((t) => <li key={t}>{t}</li>)}
      </ul>
    </section>
  );
}
