import type { components, paths } from "./api.schema";

export type Totals = components["schemas"]["Total"];

export type User = components["schemas"]["API_User"];
export type UserWithStats = components["schemas"]["API_UserWithStats"];

export type Activity = components["schemas"]["API_Activity"];
export type ActivitiesQuery =
  paths["/api/activities"]["get"]["parameters"]["query"];

export type Platform = components["schemas"]["API_Platform"];
export type PlatformWithStats = components["schemas"]["API_PlatformWithStats"];

export type Game = components["schemas"]["API_Game"];
export type GameWithStats = components["schemas"]["API_GameWithStats"];

export type SGDBGrid = components["schemas"]["SGDB_Grid"];
//export type SGDBGame = components["schemas"]["SGDB_Game"];

export interface GameCoverData {
  imageUrl: string;
  sourceUrl?: string;
  source: "SteamGridDB" | "Steam" | "Custom" | "None";
  credits?: string;
}
