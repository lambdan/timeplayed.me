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
import { Platform, PlatformName } from "./platform";

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

  async fetchSessionsByUserID(
    userID: string,
    limit?: number
  ): Promise<Session[]> {
    return await this._fetchSessions(userID, undefined, limit);
  }

  async fetchSessionsByGameID(
    gameID: number,
    limit?: number
  ): Promise<Session[]> {
    return await this._fetchSessions(undefined, gameID, limit);
  }

  async fetchSessions(limit?: number): Promise<Session[]> {
    return await this._fetchSessions(undefined, undefined, limit);
  }

  async fetchSessionsByPlatform(platformName: string): Promise<Session[]> {
    return await this._fetchSessions(
      undefined,
      undefined,
      undefined,
      platformName
    );
  }

  private async _fetchSessions(
    userID?: string,
    gameID?: number,
    limit?: number,
    platform?: string,
    orderBy = "timestamp DESC"
  ): Promise<Session[]> {
    const sessions = new Array<Session>();

    const query: string[] = ["SELECT * FROM activity"];
    const filters: string[] = [];
    const values: any[] = [];
    if (userID && gameID) {
      values.push(userID);
      filters.push(`user_id = $${values.length}`);
      values.push(gameID);
      filters.push(`game_id = $${values.length}`);
    } else if (userID) {
      values.push(userID);
      filters.push(`user_id = $${values.length}`);
    } else if (gameID) {
      values.push(gameID);
      filters.push(`game_id = $${values.length}`);
    }

    if (platform) {
      values.push(platform);
      filters.push(`platform = $${values.length}`);
    }

    // push in filters to query
    if (filters.length > 0) {
      query.push("WHERE " + filters.join(" AND "));
    }

    // push in order to query
    if (orderBy) {
      query.push(`ORDER BY ${orderBy}`);
    }
    // push in limit to query
    if (limit) {
      query.push(`LIMIT ${limit}`);
    }

    try {
      const result = await this.q(query.join(" "), values);
      for (const r of result.rows) {
        sessions.push(
          new Session({
            id: +r[0],
            date: new Date(r[1]),
            userID: r[2],
            gameID: +r[3],
            seconds: +r[4],
            platform: new Platform(r[5], []),
          })
        );
      }
    } catch (error) {
      this.logger.error("Error fetching activity:", error);
    }
    //console.log(sessions);
    return sessions;
  }

  async fetchGameById(gameID: number): Promise<Game | null> {
    try {
      const result = await this.q("SELECT * FROM game WHERE id = $1", [gameID]);
      if (result.rows.length > 0) {
        const r = result.rows[0];
        const gameName = r[1] as string;
        let smallImage = r[2];
        if (smallImage === "") {
          smallImage = null;
        }
        let largeImage = r[3];
        if (largeImage === "") {
          largeImage = null;
        }
        const steam_id = r[4] as number | null;
        const sgdb_id = r[5] as number | null;
        const sessions = await this.fetchSessionsByGameID(gameID);

        return new Game(
          gameID,
          gameName,
          sessions,
          smallImage,
          largeImage,
          steam_id,
          sgdb_id
        );
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
    const games: Game[] = [];
    try {
      const result = await this.q("SELECT id FROM game");
      for (const r of result.rows) {
        const gameID = r[0];
        const game = await this.fetchGameById(gameID);
        if (game) games.push(game);
      }
      return games;
    } catch (error) {
      this.logger.error("Error fetching games:", error);
    }
    return games;
  }

  async fetchPlatforms(): Promise<Platform[]> {
    const result: Platform[] = [];
    try {
      const res = await this.q("SELECT DISTINCT platform FROM activity");
      for (const r of res.rows) {
        const name = r[0] as PlatformName;
        const sessions = await this.fetchSessionsByPlatform(name);
        if (sessions.length > 0) {
          result.push(new Platform(name, sessions));
        }
      }
    } catch (error) {
      this.logger.error("Error fetching platforms:", error);
    }
    return result;
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
