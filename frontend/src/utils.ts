import type { ActivitiesQuery, API_Activities } from "./models/models";

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

export function timeAgo(other?: Date | number): string {
  if (!other) return "";

  if (typeof other === "number") {
    other = new Date(other);
  }

  const now = new Date();
  const seconds = Math.floor((now.getTime() - other.getTime()) / 1000);

  const intervals = [
    { label: "year", seconds: 31536000 },
    { label: "month", seconds: 2592000 },
    { label: "day", seconds: 86400 },
    { label: "hour", seconds: 3600 },
    { label: "minute", seconds: 60 },
    { label: "second", seconds: 1 },
  ];

  for (const i of intervals) {
    const count = Math.floor(seconds / i.seconds);
    if (count > 0) return `${count} ${i.label}${count !== 1 ? "s" : ""} ago`;
  }

  return "just now";
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
  maxAge: number
): Promise<Response> {
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
        //console.log("cacheFetch: Returning cached", url);
        return new Response(parsed.body, {
          headers: parsed.headers || { "content-type": "application/json" },
        });
      }
    } catch {
      console.error(
        "cacheFetch: Failed to parse cached response for key:",
        cacheKey
      );
      // Ignore parse errors and proceed to fetch
    }
  }
  console.log("cacheFetch: Fetching", url);
  const res = await fetch(url);
  const body = await res.clone().text();
  const headers: Record<string, string> = {};
  res.headers.forEach((value, key) => {
    headers[key] = value;
  });
  const entry: CacheEntry = { timestamp: Date.now(), body, headers };
  sessionStorage.setItem(cacheKey, JSON.stringify(entry)); // store
  return res;
}

// this should probably a service...
export async function fetchActivities(params: ActivitiesQuery): Promise<API_Activities> {

  if (params.after && params.after instanceof Date) {
    params.after = params.after.getTime();
  }
  if (params.before && params.before instanceof Date) {
    params.before = params.before.getTime();
  }

  let url = "/api/activities?";
  const queryParts: string[] = [];
  for (const key in params) {
    const value = (params as any)[key];
    if (value !== undefined) {
      queryParts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
    }
  }
  url += queryParts.join("&");
  console.log("Fetching activities", params, url);
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch activities: ${res.status} ${res.statusText}`);
  }
  const data = await res.json();
  return data as API_Activities;
}