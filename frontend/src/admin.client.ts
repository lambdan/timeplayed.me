// Admin routes are not in the OpenAPI schema (so not in api.schema.d.ts),
// these types mirror backend/tpbackend/admin/models.py
import type {
  Activity,
  AuthenticatedUser,
  Game,
  Platform,
} from "./api.models.ts";
import { useApiToken } from "./composables/useApiToken.ts";

export type AdminUser = AuthenticatedUser & { activity_count: number };
export type AdminUserDetails = AdminUser & { history: string[] };

export type AdminDiscordHistory = {
  id: number;
  timestamp: number;
  event: string;
  message: string;
};

export type AdminActivity = Activity & { hidden: boolean };
export type AdminActivityDetails = AdminActivity & { history: string[] };
export type AdminActivityPatch = Partial<{
  game_id: number;
  platform_id: number;
  user_id: number;
  seconds: number;
  ended: number;
  hidden: boolean;
}>;

export type AdminGame = Game & { hidden: boolean; activity_count: number };
export type AdminGameDetails = AdminGame & { history: string[] };
export type AdminGamePatch = Partial<{
  name: string;
  image_url: string | null;
  release_year: number | null;
  parent_id: number | null;
  steam_id: number | null;
  hidden: boolean;
}>;
export type AdminGameMissing =
  "igdb" | "sgdb" | "cover" | "release_year" | "activity";

export type AdminPlatform = Platform & {
  activity_count: number;
  history: string[];
};
export type AdminPlatformPatch = Partial<{
  abbreviation: string;
  name: string | null;
  color_primary: string | null;
  color_secondary: string | null;
  icon: string | null;
}>;

export type AdminOverlapGroup = { keep_id: number; remove_ids: number[] };

export type IGDBSearchResult = {
  id: number;
  name: string;
  first_release_date: number | null;
  url: string;
};
export type SGDBSearchResult = {
  id: number;
  name: string;
  verified: boolean;
  release_date: number;
};

type Query = Record<string, string | number | undefined>;

const { token } = useApiToken();

async function request<T>(
  method: string,
  path: string,
  options: { query?: Query; body?: unknown } = {},
): Promise<T> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(options.query ?? {})) {
    if (value !== undefined && value !== "") {
      params.set(key, String(value));
    }
  }
  const qs = params.toString();
  const url = `/api/admin${path}${qs ? "?" + qs : ""}`;

  const response = await fetch(url, {
    method,
    headers: {
      Authorization: `Bearer ${token.value}`,
      "Content-Type": "application/json",
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    let detail = data?.detail;
    if (typeof detail !== "string") {
      detail = `${response.status} ${response.statusText}`;
    }
    throw new Error(detail);
  }
  return data as T;
}

export class AdminAPI {
  /////////////// USERS //////////////////

  static getPermissions() {
    return request<string[]>("GET", "/permissions");
  }

  static getUsers(query: { search?: string; offset?: number; limit?: number }) {
    return request<AdminUser[]>("GET", "/users", { query });
  }

  static addUser(name: string, display_name: string | null) {
    return request<AdminUserDetails>("POST", "/user", {
      body: { name, display_name },
    });
  }

  static getUser(id: number) {
    return request<AdminUserDetails>("GET", `/user/${id}`);
  }

  static setPermissions(id: number, permissions: string[]) {
    return request<AdminUserDetails>("PUT", `/user/${id}/permissions`, {
      body: { permissions },
    });
  }

  static deleteUser(id: number) {
    return request<string>("DELETE", `/user/${id}`);
  }

  static getDiscordHistory(id: number, offset = 0) {
    return request<AdminDiscordHistory[]>(
      "GET",
      `/user/${id}/discord_history`,
      {
        query: { offset },
      },
    );
  }

  /////////////// ACTIVITIES //////////////////

  static getActivities(query: {
    user?: number;
    game?: number;
    platform?: number;
    offset?: number;
    limit?: number;
  }) {
    return request<AdminActivity[]>("GET", "/activities", { query });
  }

  static getActivity(id: number) {
    return request<AdminActivityDetails>("GET", `/activity/${id}`);
  }

  static patchActivity(id: number, body: AdminActivityPatch) {
    return request<AdminActivityDetails>("PATCH", `/activity/${id}`, { body });
  }

  static deleteActivity(id: number) {
    return request<string>("DELETE", `/activity/${id}`);
  }

  static moveActivities(from_game_id: number, to_game_id: number) {
    return request<{ moved: number }>("POST", "/activities/move", {
      body: { from_game_id, to_game_id },
    });
  }

  static getOverlaps() {
    return request<AdminOverlapGroup[]>("GET", "/activities/overlaps");
  }

  static mergeOverlaps() {
    return request<{ groups: number; removed: number }>(
      "POST",
      "/activities/overlaps/merge",
    );
  }

  /////////////// GAMES //////////////////

  static getGames(query: {
    search?: string;
    missing?: AdminGameMissing;
    offset?: number;
    limit?: number;
  }) {
    return request<AdminGame[]>("GET", "/games", { query });
  }

  static getGame(id: number) {
    return request<AdminGameDetails>("GET", `/game/${id}`);
  }

  static addGame(name: string) {
    return request<AdminGameDetails>("POST", "/game", { body: { name } });
  }

  static patchGame(id: number, body: AdminGamePatch) {
    return request<AdminGameDetails>("PATCH", `/game/${id}`, { body });
  }

  static setIGDBId(id: number, igdb_id: number | null) {
    return request<AdminGameDetails>("PUT", `/game/${id}/igdb`, {
      body: { igdb_id },
    });
  }

  static setSGDBId(id: number, sgdb_id: number | null) {
    return request<AdminGameDetails>("PUT", `/game/${id}/sgdb`, {
      body: { sgdb_id },
    });
  }

  static addAlias(id: number, alias: string) {
    return request<AdminGameDetails>("POST", `/game/${id}/aliases`, {
      body: { alias },
    });
  }

  static removeAlias(id: number, alias: string) {
    return request<AdminGameDetails>("DELETE", `/game/${id}/aliases`, {
      query: { alias },
    });
  }

  static deleteGame(id: number) {
    return request<string>("DELETE", `/game/${id}`);
  }

  static mergePreview(id: number, into: number) {
    return request<{ activity_count: number; new_aliases: string[] }>(
      "GET",
      `/game/${id}/merge`,
      { query: { into } },
    );
  }

  static mergeGame(id: number, into_game_id: number) {
    return request<{ moved: number }>("POST", `/game/${id}/merge`, {
      body: { into_game_id },
    });
  }

  static searchIGDB(q: string) {
    return request<IGDBSearchResult[]>("GET", "/igdb/search", { query: { q } });
  }

  static searchSGDB(q: string) {
    return request<SGDBSearchResult[]>("GET", "/sgdb/search", { query: { q } });
  }

  /////////////// PLATFORMS //////////////////

  static getPlatforms() {
    return request<AdminPlatform[]>("GET", "/platforms");
  }

  static addPlatform(abbreviation: string) {
    return request<AdminPlatform>("POST", "/platform", {
      body: { abbreviation },
    });
  }

  static patchPlatform(id: number, body: AdminPlatformPatch) {
    return request<AdminPlatform>("PATCH", `/platform/${id}`, { body });
  }

  static deletePlatform(id: number) {
    return request<string>("DELETE", `/platform/${id}`);
  }

  /////////////// MISC //////////////////

  static getCacheStats() {
    return request<string>("GET", "/cache_stats");
  }

  static refreshSearch() {
    return request<string>("POST", "/refresh_search");
  }
}
