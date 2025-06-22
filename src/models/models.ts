export interface Platform {
  abbreviation: string;
  name: string | null;
}

export interface User {
  id: number;
  last_active: string;
  name: string;
  avatar_url: string | null;
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

export interface Activity {
  id: number;
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

export interface API_Users {
  data: User[];
  _total: number;
  _offset: number;
  _limit: number;
  _order: number;
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
