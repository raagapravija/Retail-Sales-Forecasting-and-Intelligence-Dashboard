/** Number and date formatting, in one place so the whole dashboard agrees. */

export const compactUsd = (n: number): string => {
  const abs = Math.abs(n);
  if (abs >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `$${(n / 1e3).toFixed(1)}K`;
  return `$${n.toFixed(0)}`;
};

export const compactNum = (n: number): string => {
  const abs = Math.abs(n);
  if (abs >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return n.toFixed(0);
};

export const usd = (n: number): string =>
  n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

export const num = (n: number, digits = 0): string =>
  n.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });

export const pct = (n: number, digits = 1): string => `${n.toFixed(digits)}%`;

export const signedPct = (n: number, digits = 1): string =>
  `${n >= 0 ? "+" : ""}${n.toFixed(digits)}%`;

export const shortDate = (iso: string): string =>
  new Date(iso + (iso.length === 10 ? "T00:00:00" : "")).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
  });

export const longDate = (iso: string): string =>
  new Date(iso + (iso.length === 10 ? "T00:00:00" : "")).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

/**
 * The dashboard's colours. Kept to two data colours plus up/down for change,
 * matching `tailwind.config.js`.
 */
export const ACTUAL = "#1f5fa8";
export const FORECAST = "#c4561d";
export const UP = "#2e7a4c";
export const DOWN = "#b3392f";
export const SURFACE = "#faf9f6";

export const INK = "#1a1a18";
export const INK_MUTED = "#52514e";
export const INK_FAINT = "#85837b";
export const HAIRLINE = "#dedbd2";
