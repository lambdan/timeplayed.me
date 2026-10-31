/**
 * Numbers for the stats page. Days are "YYYY-MM-DD" as the api gives them (UTC),
 * months are "YYYY-MM".
 */

export interface DaySeconds {
  day: string;
  seconds: number;
}

const HOUR = 3600;
export const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

/** the playtime by day chart response, as a list of days */
export function toDays(chart: {
  labels: string[];
  datasets: { data: number[] }[];
}): DaySeconds[] {
  return chart.labels.map((day, i) => ({
    day,
    seconds: chart.datasets[0]?.data[i] ?? 0,
  }));
}

/** every month from the first one until now, also months where nothing happened */
export function monthsSince(first: string, now = new Date()): string[] {
  const months: string[] = [];
  let year = +first.slice(0, 4);
  let month = +first.slice(5, 7);
  const lastYear = now.getUTCFullYear();
  const lastMonth = now.getUTCMonth() + 1;
  while (year < lastYear || (year === lastYear && month <= lastMonth)) {
    months.push(`${year}-${String(month).padStart(2, "0")}`);
    month += 1;
    if (month > 12) {
      month = 1;
      year += 1;
    }
  }
  return months;
}

/** "2025-01" -> "Jan 25" */
export function monthLabel(month: string): string {
  const [year, m] = month.split("-");
  const name = new Date(Date.UTC(+year, +m - 1, 1)).toLocaleString("en", {
    month: "short",
    timeZone: "UTC",
  });
  return `${name} ${year.slice(2)}`;
}

/** days from the first one until today, both included */
export function daysSince(first: string, now = new Date()): number {
  const today = Date.UTC(
    now.getUTCFullYear(),
    now.getUTCMonth(),
    now.getUTCDate(),
  );
  return Math.round((today - Date.parse(`${first}T00:00:00Z`)) / 86400000) + 1;
}

export function secondsPerMonth(days: DaySeconds[]): Map<string, number> {
  const out = new Map<string, number>();
  for (const d of days) {
    const month = d.day.slice(0, 7);
    out.set(month, (out.get(month) ?? 0) + d.seconds);
  }
  return out;
}

/** how many of the timestamps (ms) fall in each month, like players by their first activity */
export function countPerMonth(timestamps: number[]): Map<string, number> {
  const out = new Map<string, number>();
  for (const ts of timestamps) {
    const month = new Date(ts).toISOString().slice(0, 7);
    out.set(month, (out.get(month) ?? 0) + 1);
  }
  return out;
}

/** seconds per weekday, monday first */
export function secondsPerWeekday(days: DaySeconds[]): number[] {
  const out = [0, 0, 0, 0, 0, 0, 0];
  for (const d of days) {
    const sundayFirst = new Date(`${d.day}T00:00:00Z`).getUTCDay();
    out[(sundayFirst + 6) % 7] += d.seconds;
  }
  return out;
}

export function runningTotal(values: number[]): number[] {
  const out: number[] = [];
  let sum = 0;
  for (const v of values) {
    sum += v;
    out.push(sum);
  }
  return out;
}

/** the entry with the most seconds */
export function busiest<T extends { seconds: number }>(
  entries: T[],
): T | undefined {
  let best: T | undefined;
  for (const e of entries) {
    if (!best || e.seconds > best.seconds) {
      best = e;
    }
  }
  return best;
}

/** hours played in each of the months */
export function hoursPerMonth(days: DaySeconds[], months: string[]): number[] {
  const perMonth = secondsPerMonth(days);
  return months.map((m) => (perMonth.get(m) ?? 0) / HOUR);
}

/** hours played per weekday, monday first */
export function hoursPerWeekday(days: DaySeconds[]): number[] {
  return secondsPerWeekday(days).map((s) => s / HOUR);
}
