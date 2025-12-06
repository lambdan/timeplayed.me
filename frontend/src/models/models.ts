export interface Platform {
  id: number;
  abbreviation: string;
  name: string | null;
}

export interface PlatformWithStats {
  platform: Platform;
  last_played: number;
  total_sessions: number;
  total_playtime: number;
  percent: number;
}

export interface User {
  id: number;
  name: string;
  default_platform: Platform;
}

export interface Game {
  id: number;
  name: string;
  image_url: string | null;
  steam_id: number | null;
  sgdb_id: number | null;
  aliases: string[];
  release_year: number | null;
}

export interface GameWithStats {
  game: Game;
  last_played: number;
  total_sessions: number;
  total_playtime: number;
}

export interface Activity {
  id: number;
  timestamp: number;
  user: User;
  game: Game;
  platform: Platform;
  seconds: number;
}

export interface API_Paginated {
  _total: number;
  _offset: number;
  _limit: number;
}

export interface API_Activities extends API_Paginated {
  data: Activity[];
  _before: string | null;
  _after: string | null;
}

export interface UserWithStats {
  user: User;
  last_played: number;
  total_activities: number;
  total_playtime: number;
}

export interface API_Users extends API_Paginated {
  data: UserWithStats[];
}

export interface API_Games extends API_Paginated {
  data: GameWithStats[];
}

export interface API_Platforms extends API_Paginated {
  data: PlatformWithStats[];
}

export interface SGDBGrid {
  id: number;
  score: number;
  width: number;
  height: number;
  style: string;
  mime: string;
  language: string;
  url: string;
  thumbnail: string;
  type: string;
  author: {
    name: string;
    steam64: string;
    avatar: string;
  };
}

export interface SGDBGame {
  id: number;
  name: string;
  //types: ["steam", "gog", "origin"];
  verified: boolean;
  /**
   * "2015-05-19T00:00:00"
   */
  release_date: string | undefined;
}

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

export interface GlobalStats {
  total_playtime: number;
  activities: number;
  users: number;
  games: number;
  platforms: number;
}

export interface GameStats {
  total_playtime: number;
  activity_count: number;
  platform_count: number;
  player_count: number;
  oldest_activity: Activity;
  newest_activity: Activity;
}

export interface ActivitiesQuery {
  offset?: number;
  limit?: number;
  userId?: string;
  gameId?: string;
  platformId?: string;
  before?: number | Date;
  after?: number | Date;
  order?: "asc" | "desc";
}

