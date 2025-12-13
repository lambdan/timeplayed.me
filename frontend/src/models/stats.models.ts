export interface RecapGameEntry {
  id: number;
  name: string;
  seconds: number;
  first_played: Date;
  last_played: Date;
  percentage: number;
  activity_count: number;
  average_session_seconds: number;
}

export interface RecapPlatformEntry {
  id: number;
  name: string;
  seconds: number;
  percentage: number;
  activity_count: number;
  average_session_seconds: number;
  most_played_game: string;
}
