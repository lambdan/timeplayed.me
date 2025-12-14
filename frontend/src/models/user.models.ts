import type { ActivityModelV2 } from "./activity.models";
import type { PaginatedResponse } from "./models";
import type { PlatformModelV2 } from "./platform.models";
import type { Totals } from "./total.models";

export interface UserModelV2 {
  id: string; // usually a number...
  name: string;
  default_platform: PlatformModelV2;
}

export interface UserWithStats {
    user: UserModelV2;
    oldest_activity: ActivityModelV2;
    newest_activity: ActivityModelV2;
    totals: Totals;
}

export interface PaginatedUsersWithStats extends PaginatedResponse {
    data: UserWithStats[];
}
