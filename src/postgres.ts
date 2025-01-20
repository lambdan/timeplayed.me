import { Client, Configuration, connect, ResultRecord } from "ts-postgres";

export interface GameDBEntry {
  game_name: string;
  id: number;
}

export interface GameStats {
  players: number;
  time_played: number;
}

export interface UserActivity {
  timestamp: Date;
  game_id: number;
  seconds: number;
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

  async fetchActivity(userID: string): Promise<UserActivity[]> {
    const activity = new Array<UserActivity>();
    if (!this.postgresClient) {
      await this.connect();
    }
    try {
      const result = await this.postgresClient!.query(
        "SELECT * FROM activity WHERE user_id = $1 ORDER BY id DESC",
        [userID]
      );

      for (const r of result.rows) {
        activity.push({
          timestamp: new Date(r[1]),
          game_id: +r[3],
          seconds: +r[4],
        });
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    return activity;
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

  async fetchGameStatsGlobal(gameID: number): Promise<GameStats> {
    const gs: GameStats = {
      players: 0,
      time_played: 0,
    };
    const players = new Set<string>();
    if (!this.postgresClient) {
      await this.connect();
    }
    try {
      const result = await this.postgresClient!.query(
        "SELECT * FROM activity WHERE game_id = $1",
        [gameID]
      );

      for (const r of result.rows) {
        players.add(r[2]);
        gs.time_played += r[4];
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    gs.players = players.size;
    return gs;
  }

  async fetchGames(): Promise<GameDBEntry[]> {
    if (!this.postgresClient) {
      await this.connect();
    }
    try {
      const result = await this.postgresClient!.query(
        "SELECT * FROM game ORDER BY name ASC"
      );
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
        // Select distinct user_ids, order by recency
        "SELECT user_id FROM activity GROUP BY user_id ORDER BY MAX(timestamp) DESC;"
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
