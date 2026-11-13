import type { ReactNode } from "react";
import { HAIRLINE, INK_FAINT, INK_MUTED, SURFACE } from "../lib/format";

/** A titled panel. Every chart and table on the page sits in one of these. */
export function Card({
  title,
  subtitle,
  action,
  children,
  className = "",
}: {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`card ${className}`}>
      {(title || action) && (
        <header className="flex items-start justify-between gap-4 mb-4">
          <div>
            {title && <h2 className="card-title">{title}</h2>}
            {subtitle && <p className="card-subtitle">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      {children}
    </section>
  );
}

/**
 * The headline numbers: one panel split by hairlines, not a row of separate cards.
 * Each child is a <Kpi />.
 */
export function KpiStrip({ children }: { children: ReactNode }) {
  return (
    <section className="card p-0 grid sm:grid-cols-2 lg:grid-cols-4">{children}</section>
  );
}

/** A single headline number. The chart *is* the number — no one-bar bar chart. */
export function Kpi({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div
      className="flex flex-col justify-between min-h-[104px] px-5 py-4 border-hairline
                 border-b last:border-b-0 sm:[&:nth-child(odd)]:border-r
                 sm:[&:nth-child(n+3)]:border-b-0
                 lg:border-b-0 lg:border-r lg:last:border-r-0"
    >
      <span className="label">{label}</span>
      <span className="num text-[27px] leading-none font-semibold mt-2 tracking-tight">
        {value}
      </span>
      {hint && <span className="text-[11.5px] text-ink-faint mt-1.5">{hint}</span>}
    </div>
  );
}

/** Plain loading text in place of a skeleton placeholder. */
export function Loading({ label = "Loading…" }: { label?: string }) {
  return <p className="text-[12.5px] text-ink-faint py-6">{label}</p>;
}

export function ErrorNote({ error }: { error: string }) {
  return (
    <div className="card border-down">
      <p className="text-[13px] font-semibold text-down">Could not load</p>
      <p className="text-[12px] text-ink-muted mt-1 font-mono break-words">{error}</p>
    </div>
  );
}

/** Shared Recharts styling, so every chart on the page reads as one system. */
export const axisProps = {
  stroke: HAIRLINE,
  tick: { fill: INK_MUTED, fontSize: 11 },
  tickLine: false,
  axisLine: { stroke: HAIRLINE },
} as const;

export const gridProps = {
  stroke: HAIRLINE,
  strokeDasharray: "0",
  vertical: false,
} as const;

/** Flat, square tooltip that appears in place: no shadow, no slide-in. */
export const tooltipStyle = {
  contentStyle: {
    background: SURFACE,
    border: `1px solid ${HAIRLINE}`,
    borderRadius: 2,
    fontSize: 12,
    boxShadow: "none",
  },
  labelStyle: { color: INK_FAINT, fontSize: 11, marginBottom: 4 },
  isAnimationActive: false,
} as const;

export const legendProps = {
  wrapperStyle: { fontSize: 12, color: INK_MUTED, paddingTop: 8 },
  iconType: "plainline",
  iconSize: 14,
} as const;
