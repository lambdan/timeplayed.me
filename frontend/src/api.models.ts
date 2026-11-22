import type { components, paths } from "./api.schema";

export type Totals = components["schemas"]["Total"];

export type User = components["schemas"]["API_User"];
export type AuthenticatedUser = components["schemas"]["API_AuthenticatedUser"];
export type UserWithStats = components["schemas"]["API_UserWithStats"];

export type Activity = components["schemas"]["API_Activity"];
export type ActivitiesQuery =
  paths["/activities"]["get"]["parameters"]["query"];

export type LiveActivity = components["schemas"]["API_LiveActivity"];
export type LiveActivityPost =
  paths["/activity/live"]["post"]["requestBody"]["content"]["application/json"];
export type ActivityPost =
  paths["/activity"]["post"]["requestBody"]["content"]["application/json"];

export type Platform = components["schemas"]["API_Platform"];
export type PlatformWithStats = components["schemas"]["API_PlatformWithStats"];

export type Game = components["schemas"]["API_Game"];
export type GameWithStats = components["schemas"]["API_GameWithStats"];

export type GameCover = components["schemas"]["API_GameCover"];

export type IGDBSearchResult = components["schemas"]["IGDB_SearchResult"];

// the charts route isn't in the OpenAPI schema either, see backend/tpbackend/charts/
export type PlaytimeChart = {
  labels: string[];
  datasets: { label: string; data: number[] }[];
};
export type PlaytimeChartQuery = {
  user?: number;
  game?: number;
  include_children?: boolean;
  platform?: number;
  include_child_platforms?: boolean;
  before?: number;
  after?: number;
};
