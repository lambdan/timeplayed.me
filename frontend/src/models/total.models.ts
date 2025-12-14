import type { ActivityModelV2 } from "./activity.models";

export interface Totals {
    playtime_secs: number;
    activity_count: number;
    user_count: number;
    game_count: number;
    platform_count: number;
}

export interface GameOrPlatformStats {
    totals: Totals;
    oldest_activity: ActivityModelV2 | null;
    newest_activity: ActivityModelV2 | null;
    percent: number;
}