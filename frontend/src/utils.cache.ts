// Small cache in sessionStorage, so the same game/user/platform isn't fetched on every page load.
// Entries expire, so changes (like an admin setting a new IGDB ID) show up without closing the tab.

const MINUTE = 60 * 1000;
/** games, users, platforms */
export const DATA_MAX_AGE = 2 * MINUTE;
/** covers come from IGDB/SGDB (the backend caches IGDB for an hour too), so they're kept longer */
export const COVER_MAX_AGE = 60 * MINUTE;

interface Entry<T> {
  stored: number;
  value: T;
}

export function getCached<T>(key: string, maxAge = DATA_MAX_AGE): T | null {
  const raw = sessionStorage.getItem(key);
  if (!raw) return null;
  try {
    const entry = JSON.parse(raw) as Entry<T>;
    // entries from before they had a timestamp count as expired
    if (
      typeof entry.stored === "number" &&
      Date.now() - entry.stored < maxAge
    ) {
      return entry.value;
    }
  } catch {}
  sessionStorage.removeItem(key);
  return null;
}

export function setCached<T>(key: string, value: T) {
  const entry: Entry<T> = { stored: Date.now(), value };
  try {
    sessionStorage.setItem(key, JSON.stringify(entry));
  } catch (e) {
    console.error("Error storing session cache:", e);
  }
}

/** removes every entry whose key starts with prefix */
function clearCached(prefix: string) {
  for (const key of Object.keys(sessionStorage)) {
    if (key.startsWith(prefix)) sessionStorage.removeItem(key);
  }
}

/** after editing a game, so the next page load shows the change. Its cover too */
export function clearCachedGame(gameId: number) {
  sessionStorage.removeItem(`api_getGame_${gameId}`);
  clearCached(`gameCover_${gameId}_`);
}

export function clearCachedPlatform(platformId: number) {
  sessionStorage.removeItem(`api_getPlatform_${platformId}`);
}
