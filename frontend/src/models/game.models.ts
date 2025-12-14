import type { Activity, PaginatedResponse } from "./models";
import type { GameOrPlatformStats } from "./total.models";

export interface GameModelV2 {
  id: number;
  name: string;
  image_url: string | null;
  steam_id: number | null;
  sgdb_id: number | null;
  aliases: string[];
  release_year: number | null;
}

export interface GameWithStats extends GameOrPlatformStats {
  game: GameModelV2;
}

export interface PaginatedGamesWithStats extends PaginatedResponse {
    data: GameWithStats[];
}