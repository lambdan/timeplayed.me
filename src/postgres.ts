import {
  Client,
  Configuration,
  connect,
  Query,
  ResultRecord,
} from "ts-postgres";
import { Game } from "./game";
import { Session } from "./session";
import { Logger } from "./logger";
import { PostgresTasks } from "./postgres_tasks";

let _instance: Postgres | null = null;

export class Postgres {
  private postgresClient: Client | null = null;
  private config: Configuration;
  private logger = new Logger("Postgres");

  constructor(config: Configuration) {
    this.config = config;
    this.connect();
  }

  async connect() {
    this.logger.log("Connecting to Postgres");
    this.postgresClient = await connect(this.config);
    this.logger.log("Connected!");
  }

  async q(text: Query | string, values?: any[]): Promise<ResultRecord<any>> {
    if (!this.postgresClient) {
      await this.connect();
    }
    this.logger.debug(text, values);
    return await this.postgresClient!.query(text, values);
  }

  async fetchSessions(
    userID?: string,
    gameID?: number,
    limit?: number
  ): Promise<Session[]> {
    const sessions = new Array<Session>();

    // Order by timestamp DESC to get recent first
    let query = "SELECT * FROM activity ORDER BY timestamp DESC";
    let values: any[] = [];
    if (userID && gameID) {
      query =
        "SELECT * FROM activity WHERE user_id = $1 AND game_id = $2 ORDER BY timestamp DESC";
      values = [userID, gameID];
    } else if (userID) {
      query =
        "SELECT * FROM activity WHERE user_id = $1 ORDER BY timestamp DESC";
      values = [userID];
    } else if (gameID) {
      query =
        "SELECT * FROM activity WHERE game_id = $1 ORDER BY timestamp DESC";
      values = [gameID];
    }

    if (limit) {
      values.push(limit);
      query += ` LIMIT $${values.length}`;
    }

    try {
      const result = await this.q(query, values);
      for (const r of result.rows) {
        sessions.push({
          id: +r[0],
          date: new Date(r[1]),
          userID: r[2],
          gameID: +r[3],
          seconds: +r[4],
          platform: r[5],
        });
      }
    } catch (error) {
      this.logger.error("Error fetching activity:", error);
    }
    //console.log(sessions);
    return sessions;
  }

  async fetchGameName(gameID: number): Promise<string | null> {
    try {
      const result = await this.q("SELECT name FROM game WHERE id = $1", [
        gameID,
      ]);
      if (result.rows.length > 0) {
        return result.rows[0][0] as string;
      }
    } catch (error) {
      this.logger.error("Error fetching data:", error);
    }
    return null;
  }

  async fetchGameIDFromGameName(gameName: string): Promise<number | null> {
    try {
      const result = await this.q("SELECT id FROM game WHERE name = $1", [
        gameName,
      ]);
      if (result.rows.length > 0) {
        return result.rows[0][0] as number;
      }
    } catch (error) {
      this.logger.error("Error fetching data:", error);
    }
    return null;
  }

  async fetchGames(): Promise<Game[]> {
    try {
      const result = await this.q("SELECT * FROM game");
      const games: Game[] = [];
      for (const r of result.rows) {
        const gameID = r[0];
        const gameName = r[1];
        const sessions = await this.fetchSessions(undefined, gameID);
        if (sessions.length === 0) {
          continue;
        }
        games.push(new Game(gameID, gameName, sessions));
      }
      return games;
    } catch (error) {
      this.logger.error("Error fetching games:", error);
    }
    return [];
  }

  async fetchUserIDs(): Promise<string[]> {
    try {
      const result = await this.q(
        "SELECT user_id FROM activity GROUP BY user_id ORDER BY MAX(timestamp) DESC;"
      );
      const users: string[] = [];
      for (const r of result.rows) {
        users.push(r[0]);
      }
      return users;
    } catch (error) {
      this.logger.error("Error fetching data:", error);
    }
    return [];
  }

  async insertActivity(
    date: Date,
    userID: string,
    gameID: number,
    seconds: number
  ): Promise<ResultRecord<any>> {
    if (!this.postgresClient) {
      await this.connect();
    }
    return await this.q(
      `INSERT INTO activity (timestamp, user_id, game_id, seconds)
     VALUES (to_timestamp($1), $2, $3, $4)`,
      [date.getTime() / 1000, userID, gameID, seconds]
    );
  }

  async deleteActivity(id: number): Promise<ResultRecord<any>> {
    return await this.q(`DELETE FROM activity WHERE id = $1`, [id]);
  }

  async replaceActivityGameID(
    sessionID: number,
    newGameID: number
  ): Promise<ResultRecord<any>> {
    return await this.q(
      `UPDATE activity 
     SET game_id = $1 
     WHERE id = $2`,
      [newGameID, sessionID]
    );
  }

  static GetInstance(): Postgres {
    if (_instance) {
      return _instance;
    }
    const pg = new Postgres({
      host: process.env.POSTGRES_HOST || "localhost",
      port: +(process.env.POSTGRES_PORT || 5432),
      user: process.env.POSTGRES_USER || "oblivion",
      password: process.env.POSTGRESS_PASS || "oblivion",
      database: process.env.POSTGRES_DB || "oblivionis",
    });
    _instance = pg;
    new PostgresTasks(_instance);
    return _instance;
  }
}
