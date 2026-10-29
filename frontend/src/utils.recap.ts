/**
 * Year recap, everything is computed here from the users activities.
 *
 * Conventions (same as the 2025 recap, so numbers don't change):
 * - A session belongs to the year it *ended* in (UTC), same filter as the activities endpoint
 * - Months/weekdays/days are based on when the session ended, in the viewers timezone
 * - Hour of day is the exception, sessions are split over the hours they actually covered
 */
import { TimeplayedAPI } from "./api.client";
import type { Activity } from "./api.models";

export interface Bucket {
  seconds: number;
  sessions: number;
}

export interface RecapGame extends Bucket {
  game_id: number;
  name: string;
  release_year: number | null;
  percentage: number;
  first_played: Date;
  last_played: Date;
  /** first time ever playing it */
  new: boolean;
}

export interface RecapPlatform extends Bucket {
  platform_id: number;
  name: string;
  color: string;
  percentage: number;
  top_game_id: number;
}

export interface RecapMonth extends Bucket {
  top_game_id?: number;
}

export interface Period {
  days: number;
  start: Date;
  end: Date;
}

export interface Recap {
  totals: Bucket & { games: number; days_played: number; new_games: number };
  previous_year?: Bucket & { games: number };
  games: RecapGame[];
  platforms: RecapPlatform[];
  months: RecapMonth[];
  /** monday first */
  weekdays: Bucket[];
  /** seconds per hour of day */
  hours: number[];
  /** seconds per [weekday (monday first)][hour] */
  weekHours: number[][];
  /** seconds per day of year */
  days: number[];
  /** sessions per day of year, oldest first */
  sessionsByDay: Activity[][];
  longest_session?: {
    activity_id: number;
    game_id: number;
    seconds: number;
    date: Date;
  };
  longest_streak?: Period;
  longest_break?: Period;
  biggest_day?: { date: Date; seconds: number; top_game_id: number };
  community?: { rank: number; players: number; share: number };
}

export const MONTHS = Array.from({ length: 12 }, (_, m) =>
  new Date(2000, m, 1).toLocaleDateString("en-US", { month: "long" }),
);
// 2024-01-01 was a monday
export const WEEKDAYS = Array.from({ length: 7 }, (_, d) =>
  new Date(2024, 0, 1 + d).toLocaleDateString("en-US", { weekday: "long" }),
);

// for platforms without a (visible) color
const FALLBACK_COLORS = ["#f59e0b", "#ec4899", "#8b5cf6", "#06b6d4", "#10b981"];

const DAY = 86400000;

/////////////// loading ///////////////

/** fetch everything and build the recap, onProgress gets 0-100 */
export async function loadRecap(
  userId: number,
  year: number,
  onProgress: (percent: number) => void,
): Promise<Recap> {
  const after = Date.UTC(year, 0, 1);
  const before = Date.UTC(year + 1, 0, 1);
  const users = String(userId);

  const [totals, previous, everyone] = await Promise.all([
    TimeplayedAPI.getTotals({ users, after, before }),
    TimeplayedAPI.getTotals({
      users,
      after: Date.UTC(year - 1, 0, 1),
      before: after,
    }),
    TimeplayedAPI.getUsersStats({ after, before, limit: 100 }),
  ]);

  // newest first like the old recap, so ties end up the same way
  const activities: Activity[] = [];
  while (activities.length < totals.activity_count) {
    const page = await TimeplayedAPI.getActivities({
      user: userId,
      after,
      before,
      order: "desc",
      sort: "timestamp",
      limit: 200,
      offset: activities.length,
    });
    if (!page.length) break;
    activities.push(...page);
    onProgress((activities.length / totals.activity_count) * 90);
  }

  // names, release years, and which games were played before this year
  const gameIds = [...new Set(activities.map((a) => a.game_id))];
  const games = new Map<
    number,
    { name: string; release_year: number | null }
  >();
  const playedBefore = new Set<number>();
  for (let i = 0; i < gameIds.length; i += 100) {
    const ids = gameIds.slice(i, i + 100);
    const [info, earlier] = await Promise.all([
      TimeplayedAPI.getGameStatsMany(ids),
      TimeplayedAPI.getGameStatsMany(ids, { user: userId, before: after - 1 }),
    ]);
    info.forEach((g) => games.set(g.id, g));
    earlier
      .filter((g) => g.stats.activity_count)
      .forEach((g) => playedBefore.add(g.id));
  }
  const platformIds = [...new Set(activities.map((a) => a.platform_id))];
  const platforms = await Promise.all(
    platformIds.map((id) => TimeplayedAPI.getPlatform(id)),
  );
  onProgress(100);

  const recap = buildRecap(activities, year, {
    games,
    playedBefore,
    platforms: new Map(platforms.map((p) => [p.id, p])),
  });

  if (previous.activity_count) {
    recap.previous_year = {
      seconds: previous.seconds,
      sessions: previous.activity_count,
      games: previous.game_count,
    };
  }
  const players = everyone.filter((u) => u.stats.seconds > 0);
  const rank = players.findIndex((u) => u.id === userId);
  if (rank >= 0) {
    const all = players.reduce((a, u) => a + u.stats.seconds, 0);
    recap.community = {
      rank: rank + 1,
      players: players.length,
      share: (players[rank].stats.seconds / all) * 100,
    };
  }
  return recap;
}

/////////////// stats ///////////////

interface Lookups {
  games: Map<number, { name: string; release_year: number | null }>;
  playedBefore: Set<number>;
  platforms: Map<
    number,
    {
      display_name: string;
      color_primary: string | null;
      color_secondary: string | null;
    }
  >;
}

/** local midnight of the day the session ended, clamped to the year */
function localDay(a: Activity, year: number): Date {
  const d = new Date(a.ended);
  const day = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const first = new Date(year, 0, 1);
  const last = new Date(year, 11, 31);
  return day < first ? first : day > last ? last : day;
}

function daysBetween(a: Date, b: Date): number {
  // rounding takes care of DST
  return Math.round((b.getTime() - a.getTime()) / DAY);
}

function addDays(d: Date, n: number): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);
}

/** totals grouped by key, most played first */
function totalsBy<K>(
  activities: Activity[],
  key: (a: Activity) => K,
): Map<K, Bucket> {
  const res = new Map<K, Bucket>();
  for (const a of activities) {
    const t = res.get(key(a)) ?? { seconds: 0, sessions: 0 };
    t.seconds += a.seconds;
    t.sessions += 1;
    res.set(key(a), t);
  }
  return new Map([...res].sort((x, y) => y[1].seconds - x[1].seconds));
}

/** totals for key 0..n-1, including empty ones */
function buckets(
  activities: Activity[],
  key: (a: Activity) => number,
  n: number,
): Bucket[] {
  const t = totalsBy(activities, key);
  return Array.from(
    { length: n },
    (_, i) => t.get(i) ?? { seconds: 0, sessions: 0 },
  );
}

/** most played game (or whatever `of` returns) for each key */
function topBy<K>(
  activities: Activity[],
  key: (a: Activity) => K,
  of: (a: Activity) => number = (a) => a.game_id,
): Map<K, number> {
  const seconds = new Map<K, Map<number, number>>();
  for (const a of activities) {
    const m = seconds.get(key(a)) ?? new Map<number, number>();
    m.set(of(a), (m.get(of(a)) ?? 0) + a.seconds);
    seconds.set(key(a), m);
  }
  const res = new Map<K, number>();
  for (const [k, m] of seconds) {
    let best = -1;
    for (const [id, s] of m) {
      if (best === -1 || s > m.get(best)!) best = id;
    }
    res.set(k, best);
  }
  return res;
}

/** seconds played per [weekday (monday first)][hour], sessions are split over the hours they covered */
function weekHours(activities: Activity[]): number[][] {
  const res = Array.from({ length: 7 }, () => new Array(24).fill(0));
  for (const a of activities) {
    let cur = new Date(a.started);
    while (cur.getTime() < a.ended) {
      const next = new Date(cur);
      next.setMinutes(60, 0, 0); // start of the next hour
      const chunk = Math.min(next.getTime(), a.ended) - cur.getTime();
      res[(cur.getDay() + 6) % 7][cur.getHours()] += Math.round(chunk / 1000);
      cur = next;
    }
  }
  return res;
}

/** most days in a row with something played */
function longestStreak(dates: Date[]): Period | undefined {
  if (!dates.length) return undefined;
  let best = { days: 1, start: dates[0], end: dates[0] };
  let start = dates[0];
  for (let i = 1; i < dates.length; i++) {
    if (daysBetween(dates[i - 1], dates[i]) !== 1) start = dates[i];
    const days = daysBetween(start, dates[i]) + 1;
    if (days > best.days) best = { days, start, end: dates[i] };
  }
  return best;
}

/** most days in a row with nothing played, between the first and last day played */
function longestBreak(dates: Date[]): Period | undefined {
  let best: Period | undefined;
  for (let i = 1; i < dates.length; i++) {
    const gap = daysBetween(dates[i - 1], dates[i]) - 1;
    if (gap > 0 && (!best || gap > best.days)) {
      best = {
        days: gap,
        start: addDays(dates[i - 1], 1),
        end: addDays(dates[i], -1),
      };
    }
  }
  return best;
}

/** first color that's visible on a dark background */
function visibleColor(
  colors: (string | null | undefined)[],
  i: number,
): string {
  for (const c of colors) {
    if (c && /^[0-9a-f]{6}$/i.test(c)) {
      const [r, g, b] = [0, 2, 4].map((j) => parseInt(c.slice(j, j + 2), 16));
      if (0.2126 * r + 0.7152 * g + 0.0722 * b > 50) return `#${c}`;
    }
  }
  return FALLBACK_COLORS[i % FALLBACK_COLORS.length];
}

function buildRecap(
  activities: Activity[],
  year: number,
  lookups: Lookups,
): Recap {
  const total = activities.reduce((a, b) => a + b.seconds, 0);
  const pct = (s: number) => (total ? (s / total) * 100 : 0);
  const first = new Date(year, 0, 1);
  const day = (a: Activity) => localDay(a, year);
  const dayIndex = (a: Activity) => daysBetween(first, day(a));
  const monthOf = (a: Activity) => day(a).getMonth();

  const games = [...totalsBy(activities, (a) => a.game_id)].map(([id, t]) => {
    const played = activities.filter((a) => a.game_id === id).map(day);
    const info = lookups.games.get(id);
    return {
      ...t,
      game_id: id,
      name: info?.name ?? `Game ${id}`,
      release_year: info?.release_year ?? null,
      percentage: pct(t.seconds),
      first_played: new Date(Math.min(...played.map((d) => d.getTime()))),
      last_played: new Date(Math.max(...played.map((d) => d.getTime()))),
      new: !lookups.playedBefore.has(id),
    };
  });

  const platformTop = topBy(activities, (a) => a.platform_id);
  const platforms = [...totalsBy(activities, (a) => a.platform_id)].map(
    ([id, t], i) => {
      const p = lookups.platforms.get(id);
      return {
        ...t,
        platform_id: id,
        name: p?.display_name ?? `Platform ${id}`,
        color: visibleColor([p?.color_primary, p?.color_secondary], i),
        percentage: pct(t.seconds),
        top_game_id: platformTop.get(id)!,
      };
    },
  );

  const monthTop = topBy(activities, monthOf);
  const week = weekHours(activities);
  const days = buckets(
    activities,
    dayIndex,
    daysBetween(first, new Date(year + 1, 0, 1)),
  ).map((t) => t.seconds);
  const dates = days.flatMap((s, i) => (s ? [addDays(first, i)] : []));
  const sessionsByDay: Activity[][] = days.map(() => []);
  // activities are newest first, go backwards so each day is oldest first
  for (const a of [...activities].reverse()) sessionsByDay[dayIndex(a)].push(a);
  const biggest = days.indexOf(Math.max(...days));
  const longest = activities.reduce<Activity | undefined>(
    (best, a) => (!best || a.seconds > best.seconds ? a : best),
    undefined,
  );

  return {
    totals: {
      seconds: total,
      sessions: activities.length,
      games: games.length,
      days_played: dates.length,
      new_games: games.filter((g) => g.new).length,
    },
    games,
    platforms,
    months: buckets(activities, monthOf, 12).map((t, m) => ({
      ...t,
      top_game_id: monthTop.get(m),
    })),
    // not clamped to the year, the weekday it actually ended on is what matters
    weekdays: buckets(
      activities,
      (a) => (new Date(a.ended).getDay() + 6) % 7,
      7,
    ),
    weekHours: week,
    hours: week[0].map((_, h) => week.reduce((a, day) => a + day[h], 0)),
    days,
    sessionsByDay,
    longest_session: longest && {
      activity_id: longest.id,
      game_id: longest.game_id,
      seconds: longest.seconds,
      date: day(longest),
    },
    longest_streak: longestStreak(dates),
    longest_break: longestBreak(dates),
    biggest_day: dates.length
      ? {
          date: addDays(first, biggest),
          seconds: days[biggest],
          top_game_id: topBy(activities, dayIndex).get(biggest)!,
        }
      : undefined,
  };
}

/////////////// formatting ///////////////

/** "Mar 4" */
export function shortDate(d: Date): string {
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

/** % change, undefined if there's nothing to compare with */
export function percentChange(
  current: number,
  previous?: number,
): number | undefined {
  return previous ? ((current - previous) / previous) * 100 : undefined;
}

/** a bootstrap css variable, so charts follow the theme */
export function bsColor(name: string): string {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(`--bs-${name}`)
    .trim();
}
