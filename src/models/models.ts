export interface Platform {
  abbreviation: string;
  name: string | null;
}

export interface User {
  id: number;
  name: string;
  avatar_url: string | null;
  default_platform: Platform;
}

export interface Game {
  id: number;
  name: string;
  steam_id: number | null;
  sgdb_id: number | null;
  aliases: string[];
  release_year: number | null;
}

export interface Activity {
  id: number;
  /**
   * ISO8601 string representing the date and time of the activity.
   */
  timestamp: string;
  user: User;
  game: Game;
  platform: Platform;
  seconds: number;
}

export interface API_Activities {
  data: Activity[];
  _total: number;
  _offset: number;
  _limit: number;
  _order: number;
}
