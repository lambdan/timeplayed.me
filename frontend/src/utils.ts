export function formatDate(date?: Date | number): string {
  if (!date) return "";
  return iso8601Date(date, true);
  /*if (!date) return "";
  if (typeof date === "number") {
    date = new Date(date);
  }
  return date.toLocaleString();*/
}

export function formatDuration(
  secs?: number,
  hhmmss = false,
  steam = true,
): string {
  const f = () => {
    if (!secs) {
      if (hhmmss) return "00:00:00";
      if (steam) return "0 minutes";
      return "0s";
    }

    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    const s = Math.floor(secs % 60);
    const [hh, mm, ss] = [
      h.toString().padStart(2, "0").trim(),
      m.toString().padStart(2, "0").trim(),
      s.toString().padStart(2, "0").trim(),
    ];

    if (hhmmss) {
      return `${hh}:${mm}:${ss}`;
    }

    // > 1.5 hours = show hours with 1 decimal
    // >= 1 minute = show minutes with 0 decimals
    // < 1 minute: show seconds
    if (steam) {
      const _h = secs / 3600;
      if (_h > 1.5) {
        return `${_h.toFixed(1)} hours`;
      }
      const _m = Math.floor(secs / 60);
      if (_m == 1) {
        return `1 minute`;
      }
      if (_m > 1) {
        return `${_m} minutes`;
      }
      return `${Math.floor(secs)} seconds`;
    }

    const parts: string[] = [];

    if (h > 0) {
      parts.push(`${h}h`);
    }
    if (m > 0) {
      parts.push(`${m}m`);
    }
    if (s > 0) {
      parts.push(`${s}s`);
    }
    return parts.join(" ");
  };
  return f().trim();
}

export function timeAgo(other?: Date | number, short = false): string {
  if (!other) return "";

  if (typeof other === "number") {
    other = new Date(other);
  }

  const now = new Date();
  const seconds = Math.floor((now.getTime() - other.getTime()) / 1000);
  const delta = Math.abs(seconds);

  if (delta > 86400 && delta < 172800) {
    return "yesterday";
  }

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
      return `${count} ${i.label} ago`;
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

export function iso8601Date(date: Date | number, includeTime = false): string {
  if (typeof date === "number") {
    date = new Date(date);
  }
  let output = date.toISOString().slice(0, 10);
  if (!includeTime) {
    return output;
  }
  output += " " + date.toISOString().slice(11, 19) + " UTC";
  return output;
}

export function clamp(num: number, min: number, max: number): number {
  return Math.min(Math.max(num, min), max);
}

/** Returns a year if recap should be shown */
export function getRecapYear(): number | null {
  const now = new Date();
  // december 15 or later, return current year
  if (now.getMonth() === 11 && now.getDate() >= 15) {
    return now.getFullYear();
  }
  // january 15 or earlier, return previous year
  if (now.getMonth() === 0 && now.getDate() <= 15) {
    return now.getFullYear() - 1;
  }
  // rest of the year, no recap
  return null;
}

/** Update <title> */
export function updateDocumentTitle(title: string): void {
  document.title = `${title} - Timeplayed.me`;
}
