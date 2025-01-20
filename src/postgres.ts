import { Client, Configuration, connect, ResultRecord } from "ts-postgres";

export interface GameDBEntry {
  game_name: string;
  id: number;
}

export class Postgres {
  private postgresClient: Client | null = null;
  private config: Configuration;
  constructor(config: Configuration) {
    this.config = config;
  }

  async connect() {
    this.postgresClient = await connect(this.config);
  }

  async fetchActivity(userID: string): Promise<ResultRecord | null> {
    if (!this.postgresClient) {
      await this.connect();
    }
    try {
      const result = await this.postgresClient!.query(
        "SELECT * FROM activity WHERE user_id = $1",
        [userID]
      );
      return result;
    } catch (error) {
      console.error("Error fetching data:", error);
      return null;
    }
  }

  async fetchGameName(gameID: number): Promise<string | null> {
    if (!this.postgresClient) {
      await this.connect();
    }
    try {
      const result = await this.postgresClient!.query(
        "SELECT name FROM game WHERE id = $1",
        [gameID]
      );
      if (result.rows.length > 0) {
        return result.rows[0][0] as string;
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    return null;
  }

  async fetchGames(): Promise<GameDBEntry[]> {
    if (!this.postgresClient) {
      await this.connect();
    }
    try {
      const result = await this.postgresClient!.query("SELECT * FROM game");
      const games: GameDBEntry[] = [];
      for (const r of result.rows) {
        const game: GameDBEntry = {
          game_name: r[1],
          id: r[0],
        };
        games.push(game);
      }
      return games;
    } catch (error) {
      console.error("Error fetching games:", error);
    }
    return [];
  }

  async fetchUserIDs(): Promise<string[]> {
    if (!this.postgresClient) {
      await this.connect();
    }
    try {
      const result = await this.postgresClient!.query(
        "SELECT DISTINCT user_id FROM activity"
      );
      const users: string[] = [];
      for (const r of result.rows) {
        users.push(r[0]);
      }
      return users;
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    return [];
  }
}
