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
import type { ChartOptions, TooltipItem } from "chart.js";

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
  days_played: number;
  weeks_played: number;
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

export interface DaySession {
  activity: Activity;
  /** how much of it was played that day */
  seconds: number;
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
  /** what was played each day, an activity that spans days is on each of them */
  daySessions: DaySession[][];
  /** all activities, oldest first */
  activities: Activity[];
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
  records?: {
    most_games_day: { date: Date; games: number };
    game_streak: Period & { game_id: number };
    busiest_week: { start: Date; end: Date; seconds: number };
    biggest_game_day: { date: Date; game_id: number; seconds: number };
    /** game played in the most different weeks */
    most_regular: { game_id: number; weeks: number; of: number };
  };
}

export const MONTHS = Array.from({ length: 12 }, (_, m) =>
  new Date(2000, m, 1).toLocaleDateString("en-US", { month: "long" }),
);
// 2024-01-01 was a monday
export const WEEKDAYS = Array.from({ length: 7 }, (_, d) =>
  new Date(2024, 0, 1 + d).toLocaleDateString("en-US", { weekday: "long" }),
);

/**
 * heatmap colors, 0 = nothing played. pale yellow to deep red, all bright enough to
 * stand out from the empty gray
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

/** a piece of an activity that happened on one day of the year */
interface Chunk {
  a: Activity;
  day: number;
  seconds: number;
}

/**
 * the activity split over the (local) days it covered, so a 3 day long activity counts
 * on all 3 days instead of dumping everything on the day it ended. days outside the
 * year (an activity that started before new year) are clamped to it
 */
function splitByDay(a: Activity, year: number): Chunk[] {
  const first = new Date(year, 0, 1);
  const lastDay = daysBetween(first, new Date(year, 11, 31));
  const res = new Map<number, number>();
  let cur = a.started;
  while (cur < a.ended) {
    const d = new Date(cur);
    const midnight = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const end = Math.min(addDays(midnight, 1).getTime(), a.ended);
    const day = Math.min(Math.max(daysBetween(first, midnight), 0), lastDay);
    res.set(day, (res.get(day) ?? 0) + (end - cur) / 1000);
    cur = end;
  }
  return [...res].map(([day, seconds]) => ({ a, day, seconds }));
}

/** most played game for each key, by the seconds in the chunks */
function topGameBy<K>(chunks: Chunk[], key: (c: Chunk) => K): Map<K, number> {
  const seconds = new Map<K, Map<number, number>>();
  for (const c of chunks) {
    const m = seconds.get(key(c)) ?? new Map<number, number>();
    m.set(c.a.game_id, (m.get(c.a.game_id) ?? 0) + c.seconds);
    seconds.set(key(c), m);
  }
  const res = new Map<K, number>();
  for (const [k, m] of seconds) {
    res.set(k, [...m].reduce((x, y) => (y[1] > x[1] ? y : x))[0]);
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
  const monthOf = (a: Activity) => day(a).getMonth();
  const monthOfDay = (dayIdx: number) => addDays(first, dayIdx).getMonth();
  // monday based calendar weeks, the first and last week of the year can be partial
  const firstWeekday = (first.getDay() + 6) % 7;
  const weekOf = (dayIdx: number) => Math.floor((dayIdx + firstWeekday) / 7);
  const daysInYear = daysBetween(first, new Date(year + 1, 0, 1));

  // everything per day is based on these, oldest activity first
  const chunks = [...activities].reverse().flatMap((a) => splitByDay(a, year));

  // per game: the days of the year it was played on, sorted
  const gameDays = new Map<number, number[]>();
  for (const c of chunks) {
    const set = gameDays.get(c.a.game_id) ?? [];
    if (!set.includes(c.day)) set.push(c.day);
    gameDays.set(c.a.game_id, set);
  }
  gameDays.forEach((d) => d.sort((x, y) => x - y));

  const games = [...totalsBy(activities, (a) => a.game_id)].map(([id, t]) => {
    const played = gameDays.get(id)!;
    const info = lookups.games.get(id);
    return {
      ...t,
      game_id: id,
      name: info?.name ?? `Game ${id}`,
      release_year: info?.release_year ?? null,
      percentage: pct(t.seconds),
      first_played: addDays(first, played[0]),
      last_played: addDays(first, played[played.length - 1]),
      new: !lookups.playedBefore.has(id),
      days_played: played.length,
      weeks_played: new Set(played.map(weekOf)).size,
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

  const week = weekHours(activities);
  const days = new Array(daysInYear).fill(0);
  // every activity is listed on each day it was played on
  const daySessions: DaySession[][] = days.map(() => []);
  for (const c of chunks) {
    days[c.day] += c.seconds;
    daySessions[c.day].push({ activity: c.a, seconds: c.seconds });
  }
  const dates = days.flatMap((s, i) => (s ? [addDays(first, i)] : []));
  const monthTop = topGameBy(chunks, (c) => monthOfDay(c.day));
  // activity counts go by the month/weekday it ended, playtime by when it was played
  const monthSessions = buckets(activities, monthOf, 12);
  const weekdaySessions = buckets(
    activities,
    (a) => (new Date(a.ended).getDay() + 6) % 7,
    7,
  );
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
    months: monthSessions.map((t, m) => ({
      sessions: t.sessions,
      seconds: days.reduce(
        (sum, s, i) => (monthOfDay(i) === m ? sum + s : sum),
        0,
      ),
      top_game_id: monthTop.get(m),
    })),
    weekdays: weekdaySessions.map((t, d) => ({
      sessions: t.sessions,
      seconds: week[d].reduce((a, b) => a + b, 0),
    })),
    weekHours: week,
    hours: week[0].map((_, h) => week.reduce((a, day) => a + day[h], 0)),
    days,
    daySessions,
    activities: [...activities].reverse(),
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
          top_game_id: topGameBy(chunks, (c) => c.day).get(biggest)!,
        }
      : undefined,
    records: activities.length
      ? records(chunks, days, daySessions, games, gameDays, first, weekOf)
      : undefined,
  };
}

function records(
  chunks: Chunk[],
  days: number[],
  daySessions: DaySession[][],
  games: RecapGame[],
  gameDays: Map<number, number[]>,
  first: Date,
  weekOf: (dayIdx: number) => number,
): Recap["records"] {
  const date = (dayIdx: number) => addDays(first, dayIdx);

  const gamesPerDay = daySessions.map(
    (s) => new Set(s.map((x) => x.activity.game_id)).size,
  );
  const mostGamesDay = gamesPerDay.indexOf(Math.max(...gamesPerDay));

  // longest streak of one game, ties go to the most played game
  let gameStreak: Period & { game_id: number } = {
    game_id: 0,
    days: 0,
    start: first,
    end: first,
  };
  for (const g of games) {
    const streak = longestStreak(gameDays.get(g.game_id)!.map(date))!;
    if (streak.days > gameStreak.days)
      gameStreak = { ...streak, game_id: g.game_id };
  }

  const weekSeconds = new Map<number, number>();
  days.forEach((seconds, dayIdx) => {
    const w = weekOf(dayIdx);
    weekSeconds.set(w, (weekSeconds.get(w) ?? 0) + seconds);
  });
  const [busiestWeek, busiestSeconds] = [...weekSeconds].reduce((a, b) =>
    b[1] > a[1] ? b : a,
  );
  const weekDays = days
    .map((_, i) => i)
    .filter((i) => weekOf(i) === busiestWeek);

  const gameDaySeconds = new Map<string, number>();
  for (const c of chunks) {
    const k = `${c.day}:${c.a.game_id}`;
    gameDaySeconds.set(k, (gameDaySeconds.get(k) ?? 0) + c.seconds);
  }
  const [gameDay, gameDayTotal] = [...gameDaySeconds].reduce((x, y) =>
    y[1] > x[1] ? y : x,
  );
  const [gameDayIdx, gameDayGame] = gameDay.split(":").map(Number);

  // games are most played first, so ties go to the most played one
  const mostRegular = games.reduce((a, b) =>
    b.weeks_played > a.weeks_played ? b : a,
  );

  return {
    most_games_day: {
      date: date(mostGamesDay),
      games: gamesPerDay[mostGamesDay],
    },
    game_streak: gameStreak,
    busiest_week: {
      start: date(weekDays[0]),
      end: date(weekDays[weekDays.length - 1]),
      seconds: busiestSeconds,
    },
    biggest_game_day: {
      date: date(gameDayIdx),
      game_id: gameDayGame,
      seconds: gameDayTotal,
    },
    most_regular: {
      game_id: mostRegular.game_id,
      weeks: mostRegular.weeks_played,
      of: weekOf(days.length - 1) + 1,
    },
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

/** options shared by the recap bar charts, which have hours on the y axis */
export function barOptions(
  label: (ctx: TooltipItem<"bar">) => string,
  stacked = false,
): ChartOptions<"bar"> {
  const muted = bsColor("secondary-color");
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { label: (ctx) => ` ${label(ctx)}` } },
    },
    scales: {
      x: { stacked, grid: { display: false }, ticks: { color: muted } },
      y: {
        stacked,
        ticks: { color: muted, callback: (v) => `${v}h` },
        grid: { color: bsColor("border-color-translucent") },
      },
    },
  };
}

/** a bootstrap css variable, so charts follow the theme */
export function bsColor(name: string): string {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(`--bs-${name}`)
    .trim();
}
