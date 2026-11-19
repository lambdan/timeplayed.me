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

// the cover lookups (igdb, sgdb, steam) are not in the OpenAPI schema, these mirror
// the parts we use of the models in backend/tpbackend/{igdb,sgdb,steam}/models.py
export type IGDBGameInfo = {
  id: number;
  name: string;
  first_release_date?: number | null;
  url: string;
  cover?: { id: number; image_id: string } | null;
};
export type SGDBGrid = {
  id: number | null;
  url: string | null;
  author: { name: string | null } | null;
};
export type SteamCover = { url: string; store_url: string };

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
  before?: number;
  after?: number;
};

export interface GameCoverData {
  imageUrl: string;
  sourceUrl?: string;
  source: "SteamGridDB" | "IGDB" | "Steam" | "Custom" | "None";
  credits?: string;
}
