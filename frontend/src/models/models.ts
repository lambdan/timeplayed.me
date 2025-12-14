export interface ActivitiesQuery {
  offset: number;
  limit: number;
  userId?: string;
  gameId?: string;
  platformId?: string;
  before?: number | Date;
  after?: number | Date;
  order?: "asc" | "desc";
}

export interface UsersQuery {
  offset: number;
  limit: number;
  gameId?: number;
  before?: number | Date;
  after?: number | Date;
}
