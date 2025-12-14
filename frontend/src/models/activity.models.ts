import type { GameModelV2 } from "./game.models";
import type { PaginatedResponse } from "./models";
import type { PlatformModelV2 } from "./platform.models";
import type { UserModelV2 } from "./user.models";

export interface ActivityModelV2 {
    id: number;
    timestamp: number;
    user: UserModelV2;
    game: GameModelV2;
    seconds: number;
    platform: PlatformModelV2;
}

export interface PaginatedActivities extends PaginatedResponse {
    data: ActivityModelV2[];
    order: "asc" | "desc";
}