import { Logger } from "../logger";
import { CachedGrid, Grid, GridResult, SearchResult } from "./models";

const BASE_URL = "https://www.steamgriddb.com/api/v2";
const CACHE_EXPIRY = 1000 * 60 * 60 * 24; // 24 hours

let _instance: SteamGridDB | null = null;

export class SteamGridDB {
  private logger = new Logger("SteamGridDB");
  private apiKey: string;
  private cache = new Map<number, CachedGrid>();

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      "Content-Type": "application/json",
    };
    headers["Authorization"] = `Bearer ${this.apiKey}`;
    return headers;
  }

  /**
   * Search for a game by name
   */
  async searchGames(query: string): Promise<SearchResult> {
    const url = `${BASE_URL}/search/autocomplete/${encodeURIComponent(query)}`;
    this.logger.debug("Searching for games:", url);
    const response = await fetch(url, {
      method: "GET",
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      this.logger.error(
        "Failed to fetch from SteamGridDB:",
        response.statusText
      );
      return {
        success: false,
      } as SearchResult;
    }
    this.logger.debug("Received OK response from SteamGridDB :D");
    const data = await response.json();
    return data as SearchResult;
  }

  /**
   * Gets available grids for a game
   * @param gameId The ID of the game to fetch grids for
   * @param page The page number to fetch (default is 0)
   */
  async getGridsForGameId(gameId: number, page = 0): Promise<GridResult> {
    const url = `${BASE_URL}/grids/game/${gameId}?page=${page}`;
    this.logger.debug("Fetching grids for game ID:", gameId, url);
    const response = await fetch(url, {
      method: "GET",
      headers: this.getHeaders(),
    });
    if (!response.ok) {
      this.logger.error(
        "Failed to fetch grids from SteamGridDB:",
        response.statusText
      );
      return {
        success: false,
      } as GridResult;
    }
    this.logger.debug("Received OK response from SteamGridDB :D");
    const data = await response.json();
    this.logger.debug("Fetched grids:", data);
    return data as GridResult;
  }

  /**
   * Tries to figure out the best grid for a game
   * @param gameId The ID of the game to find the best grid for
   * @returns The best grid for the game, or null if no suitable grid is found
   * */
  async bestGridForGame(gameId: number): Promise<Grid | null> {
    let best: Grid | null = null;
    let bestScore = 0;
    const gridsResult = await this.getGridsForGameId(gameId);
    if (!gridsResult.success || gridsResult.data.length === 0) {
      this.logger.error("No grids found for game ID:", gameId);
      return null;
    }
    for (const grid of gridsResult.data) {
      let thisScore = 0;

      if (grid.nsfw) {
        // Really dont want to show NSFW
        thisScore -= 999_999_999;
      }

      if (grid.style === "alternate") {
        thisScore += 10;
      }

      if (grid.language === "en") {
        thisScore += 1;
      }

      if (grid.width === 600 && grid.height === 900) {
        thisScore += 1;
      }

      thisScore += grid.upvotes;
      thisScore -= grid.downvotes;

      if (thisScore > bestScore) {
        bestScore = thisScore;
        best = grid;
      }
    }
    if (!best) {
      this.logger.error("No best grid found for game ID:", gameId);
      return null;
    }
    this.logger.debug("Best grid found for game ID:", gameId, best, bestScore);
    return best;
  }

  /**
   * Searches for a game by name and returns the top hit's ID
   * @param name The name of the game to search for
   * @returns The ID of the top hit game, or null if no games are found
   */
  async topHitForGame(name: string): Promise<number | null> {
    const searchResult = await this.searchGames(name);
    if (!searchResult.success || searchResult.data.length === 0) {
      this.logger.error("No games found for:", name);
      return null;
    }
    this.logger.debug("Top hit for game:", name, searchResult.data[0]);
    // Return the first game's ID
    return searchResult.data[0].id;
  }

  /**
   * Wrapper function to get the best grid and cache it
   */
  async cacheAndGetGridForGame(gameId: number): Promise<Grid | null> {
    if (this.cache.has(gameId)) {
      const cached = this.cache.get(gameId)!;
      if (cached.date.getTime() + CACHE_EXPIRY > Date.now()) {
        this.logger.debug("Returning cached grid for:", gameId);
        return cached.grid;
      }
    }

    const best = await this.bestGridForGame(gameId);
    if (!best) {
      return null;
    }

    this.cache.set(gameId, {
      grid: best,
      date: new Date(),
    });
    return best;
  }

  static GetInstance(): SteamGridDB {
    if (!_instance) {
      _instance = new SteamGridDB(process.env.SGDB_TOKEN!);
    }
    return _instance;
  }
}
