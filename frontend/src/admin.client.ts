// Admin routes are not in the OpenAPI schema (so not in api.schema.d.ts),
// these types mirror backend/tpbackend/admin/models.py
import type {
  Activity,
  AuthenticatedUser,
  Game,
  IGDBSearchResult,
  Platform,
} from "./api.models.ts";
import { useApiToken } from "./composables/useApiToken.ts";

export type AdminPermission = { name: string; description: string };
// current: the token this browser is logged in with
export type AdminTokenInfo = { id: number; created: number; current: boolean };
export type AdminUser = AuthenticatedUser & { activity_count: number };
export type AdminHistory = {
  timestamp: number;
  // who made the change, null if nobody did (eg Oblivionis sync)
  actor_id: number | null;
  actor_name: string | null;
  message: string;
};
export type AdminUserDetails = AdminUser & { history: AdminHistory[] };

export type AdminDiscordHistory = {
  id: number;
  timestamp: number;
  event: string;
  message: string;
};

export type AdminActivity = Activity & { hidden: boolean };
export type AdminActivityDetails = AdminActivity & { history: AdminHistory[] };
export type AdminActivityPatch = Partial<{
  game_id: number;
  platform_id: number;
  user_id: number;
  seconds: number;
  ended: number;
  hidden: boolean;
}>;

export type AdminGame = Game & {
  hidden: boolean;
  own_nsfw: boolean;
  // ImageFile id of the uploaded cover
  uploaded_cover: string | null;
  activity_count: number;
  last_activity: number | null;
};
export type AdminGameDetails = AdminGame & { history: AdminHistory[] };
export type AdminGamePatch = Partial<{
  name: string;
  cover_disabled: boolean;
  nsfw: boolean;
  release_year: number | null;
  parent_id: number | null;
  steam_id: number | null;
  hidden: boolean;
}>;
export type AdminGameMissing =
  "igdb" | "cover" | "release_year" | "activity" | "not_on_igdb"; // igdb id 0

export type AdminPlatform = Platform & {
  activity_count: number;
  last_activity: number | null;
  history: AdminHistory[];
};
export type AdminPlatformPatch = Partial<{
  abbreviation: string;
  name: string | null;
  color_primary: string | null;
  color_secondary: string | null;
  icon: string | null;
  parent_id: number | null;
}>;

export type AdminOverlapGroup = { keep_id: number; remove_ids: number[] };

// the public IGDB search gives the same
export type { IGDBSearchResult };
// the parts we use of IGDB_GameInfo in backend/tpbackend/igdb/models.py
export type IGDBGameInfo = {
  id: number;
  name: string;
  first_release_date?: number | null;
  url: string;
};

type Query = Record<string, string | number | undefined>;

const { token } = useApiToken();

async function request<T>(
  method: string,
  path: string,
  // file: sent as the body as it is, like an image upload
  options: { query?: Query; body?: unknown; file?: File } = {},
): Promise<T> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(options.query ?? {})) {
    if (value !== undefined && value !== "") {
      params.set(key, String(value));
    }
  }
  const qs = params.toString();
  const url = `/api/admin${path}${qs ? "?" + qs : ""}`;

  let body: BodyInit | undefined;
  let contentType = "application/json";
  if (options.file) {
    body = options.file;
    contentType = options.file.type || "application/octet-stream";
  } else if (options.body !== undefined) {
    body = JSON.stringify(options.body);
  }
  const response = await fetch(url, {
    method,
    headers: {
      Authorization: `Bearer ${token.value}`,
      "Content-Type": contentType,
    },
    body,
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
    return request<AdminPermission[]>("GET", "/permissions");
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

  static generateToken(id: number) {
    return request<{ token: string }>("POST", `/user/${id}/token`);
  }

  static getTokens(id: number) {
    return request<AdminTokenInfo[]>("GET", `/user/${id}/tokens`);
  }

  static revokeToken(id: number, tokenId: number) {
    return request<string>("DELETE", `/user/${id}/tokens/${tokenId}`);
  }

  static revokeAllTokens(id: number) {
    return request<string>("DELETE", `/user/${id}/tokens`);
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

  static uploadCover(id: number, file: File) {
    return request<AdminGameDetails>("PUT", `/game/${id}/cover`, { file });
  }

  static coverFromUrl(id: number, url: string) {
    return request<AdminGameDetails>("PUT", `/game/${id}/cover/url`, {
      body: { url },
    });
  }

  static removeCover(id: number) {
    return request<AdminGameDetails>("DELETE", `/game/${id}/cover`);
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

  static getIGDBGameInfo(igdb_id: number) {
    return request<IGDBGameInfo>("GET", `/igdb/game/${igdb_id}`);
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

  static refreshSearch() {
    return request<string>("POST", "/refresh_search");
  }
}
