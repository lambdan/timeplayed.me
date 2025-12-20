import { TimeplayedAPI } from "./api.client";

export function formatDate(date?: Date | number): string {
  if (!date) return "";
  if (typeof date === "number") {
    date = new Date(date);
  }
  return date.toLocaleString();
}

export function formatDuration(secs?: number): string {
  if (!secs) return "00:00:00";
  // HH:MM:SS
  const hours = Math.floor(secs / 3600);
  const minutes = Math.floor((secs % 3600) / 60);
  const seconds = Math.floor(secs % 60);
  return `${hours.toString().padStart(2, "0")}:${minutes
    .toString()
    .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
}

export function timeAgo(other?: Date | number, short = false): string {
  if (!other) return "";

  if (typeof other === "number") {
    other = new Date(other);
  }

  const now = new Date();
  const seconds = Math.floor((now.getTime() - other.getTime()) / 1000);

  let intervals = [
    { label: "year", seconds: 31536000 },
    { label: "month", seconds: 2592000 },
    { label: "day", seconds: 86400 },
    { label: "hour", seconds: 3600 },
    { label: "minute", seconds: 60 },
    { label: "second", seconds: 1 },
  ];
  if (short) {
    intervals = [
      { label: "y", seconds: 31536000 },
      { label: "mo", seconds: 2592000 },
      { label: "d", seconds: 86400 },
      { label: "h", seconds: 3600 },
      { label: "m", seconds: 60 },
      { label: "s", seconds: 1 },
    ];
  }

  for (const i of intervals) {
    const count = Math.floor(seconds / i.seconds);
    if (count > 0 && !short) {
      return `${count} ${i.label}${count !== 1 ? "s" : ""} ago`;
    }
    if (count > 0 && short) {
      return `${count}${i.label} ago`;
    }
  }

  return "now";
}

export function toUTCDate(s: string): Date {
  return new Date(s + "Z");
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Do a fetch, and cache it locally.
 * If the request is made again within maxAge, the cached response will be returned.
 * @param url URL to fetch
 * @param maxAge Maximum age of the cache in milliseconds
 * @returns Response
 */
export async function cacheFetch(
  url: string,
  maxAge: number,
): Promise<Response> {
  //return fetch(url);
  interface CacheEntry {
    timestamp: number;
    body: string;
    headers?: Record<string, string>;
  }
  const cacheKey = `fetch2:${url}`;
  const cached = sessionStorage.getItem(cacheKey);
  if (cached) {
    try {
      const parsed = JSON.parse(cached) as CacheEntry;
      const age = Date.now() - parsed.timestamp;
      if (age < maxAge) {
        // hit cache
        return new Response(parsed.body, {
          headers: parsed.headers || { "Content-Type": "application/json" },
        });
      }
    } catch {}
  }
  const res = await fetch(url);
  const body = await res.clone().text();
  const headers: Record<string, string> = {};
  res.headers.forEach((value, key) => {
    headers[key] = value;
  });
  const entry: CacheEntry = { timestamp: Date.now(), body, headers };
  try {
    // store
    sessionStorage.setItem(cacheKey, JSON.stringify(entry)); // store
  } catch (err) {}
  return res;
}

export async function getGameCoverUrl(
  gameId: number,
  thumbnail = false,
): Promise<string> {
  async function test(
    gameId: number,
    thumbnail: boolean,
  ): Promise<string | undefined> {
    async function getBest(id: number) {
      const best = await TimeplayedAPI.getBestSGDBGridForGame(id);
      if (best) {
        if (best.thumb && thumbnail) {
          return best.thumb;
        }
        if (best.url) {
          return best.url;
        }
      }
      return null;
    }

    try {
      const gameData = (await TimeplayedAPI.getGame(gameId)).game;

      if (gameData.image_url) {
        return gameData.image_url;
      }

      if (gameData.steam_id) {
        return `https://shared.steamstatic.com/store_item_assets/steam/apps/${gameData.steam_id}/library_600x900.jpg`;
      }

      if (gameData.sgdb_id) {
        const best = await getBest(gameData.sgdb_id);
        if (best) {
          return best;
        }
      }

      // search
      const search = await TimeplayedAPI.searchSGDB(gameData.name);

      if (search && search.length > 0) {
        const gameId = search[0]?.id;
        if (gameId !== undefined) {
          const best = await getBest(gameId);
          if (best) {
            return best;
          }
        }
      }
    } catch (err) {}
  }
  const coverUrl = await test(gameId, thumbnail);
  if (coverUrl) {
    return coverUrl;
  }
  // fallback to placeholder
  const size = thumbnail ? "267x400" : "600x900";
  return `https://placehold.co/${size}?text=No+Cover+Found`;
}

export function iso8601Date(date: Date | number): string {
  if (typeof date === "number") {
    date = new Date(date);
  }
  return date.toISOString().slice(0, 10);
}

export function clamp(num: number, min: number, max: number): number {
  return Math.min(Math.max(num, min), max);
}
