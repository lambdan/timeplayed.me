import type { PaginatedResponse } from "./models";
import type { GameOrPlatformStats } from "./total.models";

export interface PlatformModelV2 {
    id: number;
    abbreviation: string;
    name: string | null;
}

export interface PlatformWithStats extends GameOrPlatformStats {
    platform: PlatformModelV2;
}

export interface PaginatedPlatforms extends PaginatedResponse {
    data: PlatformWithStats[];
}