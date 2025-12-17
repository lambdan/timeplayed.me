import type { components, paths } from "./api.schema";

export type Totals = components["schemas"]["Totals"];

export type User = components["schemas"]["PublicUserModel"];
export type UserWithStats = components["schemas"]["UserWithStats"];
export type PaginatedUsersWithStats =
  components["schemas"]["PaginatedUserWithStats"];

export type Activity = components["schemas"]["PublicActivityModel"];
export type PaginatedActivities = components["schemas"]["PaginatedActivities"];
export type ActivitiesQuery =
  paths["/api/activities"]["get"]["parameters"]["query"];

export type Platform = components["schemas"]["PublicPlatformModel"];
export type PlatformWithStats = components["schemas"]["PlatformWithStats"];
export type PaginatedPlatformsWithStats =
  components["schemas"]["PaginatedPlatformsWithStats"];

export type Game = components["schemas"]["PublicGameModel"];
export type GameWithStats = components["schemas"]["GameWithStats"];
export type PaginatedGamesWithStats =
  components["schemas"]["PaginatedGameWithStats"];

export type SGDBGrid = components["schemas"]["SGDB_Grid"];
export type SGDBGame = components["schemas"]["SGDB_Game"];
