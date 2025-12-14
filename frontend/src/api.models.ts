import type { components, paths } from "./api.schema";

export type Totals = components["schemas"]["Totals"];

export type User = components["schemas"]["PublicUserModel"];
export type UserWithStats = components["schemas"]["UserWithStats"];
export type PaginatedUsersWithStats =
  components["schemas"]["PaginatedUserWithStats"];

export type Activity = components["schemas"]["PublicActivityModel"];
export type PaginatedActivities = components["schemas"]["PaginatedActivities"];

export type Platform = components["schemas"]["PublicPlatformModel"];
export type PlatformWithStats = components["schemas"]["PlatformWithStats"];
export type PaginatedPlatformsWithStats =
  components["schemas"]["PaginatedPlatformsWithStats"];

export type Game = components["schemas"]["PublicGameModel"];
export type GameWithStats = components["schemas"]["GameWithStats"];
export type PaginatedGamesWithStats =
  components["schemas"]["PaginatedGameWithStats"];

// TODO TEMP
export type SGDBGrid = {
  id: number;
  score: number;
  width: number;
  height: number;
  style: string;
  mime: string;
  language: string;
  url: string;
  thumbnail: string;
  type: string;
  author: {
    name: string;
    steam64: string;
    avatar: string;
  };
};

export type SGDBGame = {
  id: number;
  name: string;
  //types: ["steam", "gog", "origin"];
  verified: boolean;
  /**
   * "2015-05-19T00:00:00"
   */
  release_date: string | undefined;
};
