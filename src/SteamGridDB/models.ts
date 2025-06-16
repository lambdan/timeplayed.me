export interface SearchResult {
  success: boolean;
  data: {
    id: number;
    name: string;
    types: string[];
    verified: boolean;
    release_date: number; // Unix timestamp
  }[];
}

export interface Author {
  name: string;
  steam64: string;
  avatar: string;
}

export interface Grid {
  id: number;
  score: number;
  style: string;
  url: string;
  thumb: string;
  verified: boolean;
  tags: string[];
  author: Author;
  width: number;
  height: number;
  nsfw: boolean;
  humor: boolean;
  notes: string | null;
  mime: string;
  language: string;
  epilepsy: boolean;
  lock: boolean;
  upvotes: number;
  downvotes: number;
}

export interface GridResult {
  success: boolean;
  page: number;
  total: number;
  limit: number;
  data: Grid[];
}

export interface CachedGrid {
  grid: Grid;
  date: Date;
}

export interface CachedSearchResult {
  searchResult: SearchResult;
  date: Date;
}