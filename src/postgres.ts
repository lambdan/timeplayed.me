import { Client, Configuration, connect, ResultRecord } from "ts-postgres";

export interface GameDBEntry {
  game_name: string;
  id: number;
}

export interface GameStats {
  time_played: number;
  sessions: number;
  players: number;
  lastPlayed: Date;
  userStats: Map<string, UserGameStats>;
}

export interface UserGameStats {
  time_played: number;
  sessions: number;
  lastPlayed: Date;
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
      sessions: 0,
      time_played: 0,
      players: 0,
      lastPlayed: new Date(0),
      userStats: new Map<string, UserGameStats>(),
    };

    if (!this.postgresClient) {
      await this.connect();
    }
    try {
      const result = await this.postgresClient!.query(
        "SELECT * FROM activity WHERE game_id = $1 ORDER BY id DESC",
        [gameID]
      );

      for (const r of result.rows) {
        const userId = r[2];
        const timePlayed = r[4];
        const sessionDate = new Date(r[1]);

        // Update global game stats
        if (sessionDate.getTime() > gs.lastPlayed.getTime()) {
          gs.lastPlayed = sessionDate;
        }
        gs.sessions += 1;
        gs.time_played += timePlayed;

        // Update individual user stats
        // Create entry for this user if not exist
        if (!gs.userStats.has(userId)) {
          gs.userStats.set(userId, {
            time_played: 0,
            sessions: 0,
            lastPlayed: new Date(0),
          });
        }
        // Update the entry
        const existing = gs.userStats.get(userId)!;
        existing.sessions += 1;
        existing.time_played += timePlayed;
        if (sessionDate.getTime() > existing.lastPlayed.getTime()) {
          existing.lastPlayed = sessionDate;
        }
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    }

    gs.players = gs.userStats.size;
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
