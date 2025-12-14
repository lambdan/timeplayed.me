export interface PaginatedResponse {
  total: number;
  offset: number;
  limit: number;
}

/**
 * @deprecated
 */
export interface Platform {
  id: number;
  abbreviation: string;
  name: string | null;
}

/**
 * @deprecated
 */
export interface PlatformWithStats {
  platform: Platform;
  last_played: number;
  total_sessions: number;
  total_playtime: number;
  percent: number;
}

/**
 * @deprecated
 */
export interface User {
  id: number;
  name: string;
  default_platform: Platform;
}

/**
 * @deprecated
 */
export interface Game {
  id: number;
  name: string;
  image_url: string | null;
  steam_id: number | null;
  sgdb_id: number | null;
  aliases: string[];
  release_year: number | null;
}

/**
 * @deprecated
 */
export interface GameWithStats {
  game: Game;
  last_played: number;
  total_sessions: number;
  total_playtime: number;
}

/**
 * @deprecated
 */
export interface Activity {
  id: number;
  timestamp: number;
  user: User;
  game: Game;
  platform: Platform;
  seconds: number;
}

/**
 * @deprecated
 */
export interface API_Paginated {
  total: number;
  offset: number;
  limit: number;
}

/**
 * @deprecated
 */
export interface API_Activities extends API_Paginated {
  data: Activity[];
}

/**
 * @deprecated
 */
export interface UserWithStats {
  user: User;
  last_played: number;
  total_activities: number;
  total_playtime: number;
}

/**
 * @deprecated
 */
export interface API_Users extends API_Paginated {
  data: UserWithStats[];
}

/**
 * @deprecated
 */
export interface API_Games extends API_Paginated {
  data: GameWithStats[];
}

/**
 * @deprecated
 */
export interface API_Platforms extends API_Paginated {
  data: PlatformWithStats[];
}



/**
 * @deprecated
 */
export interface UserStats {
  total: {
    seconds: number;
    activities: number;
    games: number;
    platforms: number;
  };
  oldest_activity: Activity;
  newest_activity: Activity;
  active_days: number;
  average: {
    seconds_per_game: number;
    sessions_per_game: number;
    session_length: number;
  };
}

/**
 * @deprecated
 */
export interface GlobalStats {
  total_playtime: number;
  activities: number;
  users: number;
  games: number;
  platforms: number;
}

/**
 * @deprecated
 */
export interface GameStats {
  total_playtime: number;
  activity_count: number;
  platform_count: number;
  player_count: number;
  oldest_activity: Activity;
  newest_activity: Activity;
}

export interface ActivitiesQuery {
  offset: number;
  limit: number;
  userId?: string;
  gameId?: string;
  platformId?: string;
  before?: number | Date;
  after?: number | Date;
  order?: "asc" | "desc";
}

export interface UsersQuery {
  offset: number;
  limit: number;
  gameId?: number;
  before?: number | Date;
  after?: number | Date;
}


