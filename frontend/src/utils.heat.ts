/**
 * "Heat" colors for amounts of playtime, used by the recap heatmaps and activity rows
 * so a long session looks the same everywhere.
 */

/**
 * 0 = nothing played, then pale yellow to deep red, all bright enough to stand out from
 * the empty gray
 */
export const HEAT_COLORS = [
  "var(--bs-secondary-bg)",
  "#fde68a",
  "#fcd34d",
  "#fbbf24",
  "#f59e0b",
  "#f97316",
  "#ea580c",
  "#dc2626",
  "#b91c1c",
];

/** hours thresholds, a duration gets the last one it reaches */
const LEVELS = [0, 0.5, 1, 2, 3, 4, 6, 8];

export const HEAT_LEGEND = [
  "None",
  "< 30 m",
  "30 m – 1 h",
  "1 – 2 h",
  "2 – 3 h",
  "3 – 4 h",
  "4 – 6 h",
  "6 – 8 h",
  "8 h +",
];

/** index into HEAT_COLORS for an amount of seconds */
export function heatLevel(seconds: number): number {
  if (seconds <= 0) return 0;
  return LEVELS.filter((l) => seconds / 3600 >= l).length;
}

/** background + readable text color, for badges */
export function heatBadgeStyle(seconds: number) {
  const level = heatLevel(seconds);
  return {
    background: HEAT_COLORS[level],
    // dark text on the yellows, white on the oranges and reds
    color: level >= 5 ? "#fff" : "#212529",
  };
}
