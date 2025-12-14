import type {
  ActivitiesQuery,
  API_Activities,
  API_Users,
  Game,
  SGDBGame,
  SGDBGrid,
  User,
  UsersQuery,
} from "./models/models";

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

// this should probably a service...
export async function fetchActivities(
  params: ActivitiesQuery,
): Promise<API_Activities> {
  if (params.after && params.after instanceof Date) {
    params.after = params.after.getTime();
  }
  if (params.before && params.before instanceof Date) {
    params.before = params.before.getTime();
  }

  const apiParams = {
    user: params.userId,
    game: params.gameId,
    platform: params.platformId,
    offset: params.offset,
    limit: params.limit,
    before: params.before,
    after: params.after,
    order: params.order,
  };

  let url = "/api/activities?";
  const queryParts: string[] = [];
  for (const key in apiParams) {
    const value = (apiParams as any)[key];
    if (value !== undefined) {
      queryParts.push(
        `${encodeURIComponent(key)}=${encodeURIComponent(value)}`,
      );
    }
  }
  url += queryParts.join("&");
  console.log("Fetching activities", apiParams, url);
  //const res = await cacheFetch(url, 60 * 1000); // 1 minute cache
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch activities`);
  }
  return (await res.json()) as API_Activities;
}

// this should probably a service...
export async function fetchUsers(params: UsersQuery): Promise<API_Users> {
  if (params.after && params.after instanceof Date) {
    params.after = params.after.getTime();
  }
  if (params.before && params.before instanceof Date) {
    params.before = params.before.getTime();
  }
  const apiParams = {
    offset: params.offset,
    limit: params.limit,
    gameId: params.gameId,
    before: params.before,
    after: params.after,
  };

  let url = "/api/users?";
  const queryParts: string[] = [];
  for (const key in apiParams) {
    const value = (apiParams as any)[key];
    if (value !== undefined) {
      queryParts.push(
        `${encodeURIComponent(key)}=${encodeURIComponent(value)}`,
      );
    }
  }
  url += queryParts.join("&");
  console.log("Fetching users", apiParams, url);
  //const res = await cacheFetch(url, 60 * 1000); // 1 minute cache
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch activities`);
  }
  return (await res.json()) as API_Users;
}

export async function getGameCoverUrl(
  gameId: number,
  thumbnail = false,
): Promise<string> {
  const CACHE_LIFETIME = 1000 * 60 * 60; // 1 hour
  const gameInfo = await cacheFetch(`/api/games/${gameId}`, CACHE_LIFETIME);
  const gameData = ((await gameInfo.json()) as any).game as Game;

  const FALLBACK = "https://placehold.co/267x400?text=No+Image";
  if (gameData.image_url) {
    return gameData.image_url;
  }

  if (gameData.steam_id) {
    return `https://shared.steamstatic.com/store_item_assets/steam/apps/${gameData.steam_id}/library_600x900.jpg`;
  }

  if (gameData.sgdb_id) {
    const res = await cacheFetch(
      `/api/sgdb/grids/${gameData.sgdb_id}/best`,
      CACHE_LIFETIME,
    );
    if (res.ok) {
      const data: SGDBGrid = await res.json();
      return thumbnail ? data.thumbnail : data.url;
    }
    return FALLBACK;
  }

  // search
  const searchRes = await cacheFetch(
    `/api/sgdb/search?query=${encodeURIComponent(gameData.name)}`,
    CACHE_LIFETIME,
  );

  if (searchRes.ok) {
    const searchData: SGDBGame[] = await searchRes.json();
    if (searchData.length > 0) {
      const gameId = searchData[0].id;
      const res = await cacheFetch(
        `/api/sgdb/grids/${gameId}/best`,
        CACHE_LIFETIME,
      );
      if (res.ok) {
        const data: SGDBGrid = await res.json();
        return thumbnail ? data.thumbnail : data.url;
      }
    }
  }

  return FALLBACK;
}

export async function fetchUserInfo(userId: string): Promise<User> {
  const CACHE_LIFETIME = 1000 * 60 * 10; // 10 minutes
  const res = await cacheFetch(`/api/users/${userId}`, CACHE_LIFETIME);
  if (!res.ok) {
    throw new Error(`Failed to fetch user info for user ${userId}`);
  }
  const data = await res.json();
  return data.user as User;
}

export function iso8601Date(date: Date | number): string {
  if (typeof date === "number") {
    date = new Date(date);
  }
  return date.toISOString().slice(0, 10);
}
