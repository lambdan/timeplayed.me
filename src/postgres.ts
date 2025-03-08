import { Client, Configuration, connect, ResultRecord } from "ts-postgres";
import { Game } from "./game";
import { Session } from "./session";
import { User } from "./user";
import { sleep } from "./utils";
import { Logger } from "./logger";

const REPLACERS = [
  // TODO Read this from JSON or something
  // Children sessions will be replaced with parent game ID
  {
    parent: "The Elder Scrolls V: Skyrim Special Edition",
    children: ["Skyrim Special Edition"],
  },
];

export class Postgres {
  private postgresClient: Client | null = null;
  private config: Configuration;
  private taskLoopRunning = false;
  private logger = new Logger("Postgres");

  constructor(config: Configuration) {
    this.config = config;
    this.connect();
    this.taskLoop();
  }

  async connect() {
    this.logger.log("Connecting to Postgres");
    this.postgresClient = await connect(this.config);
    this.logger.log("Connected!");
  }

  async taskLoop() {
    if (this.taskLoopRunning) {
      return;
    }
    this.taskLoopRunning = true;
    while (true) {
      this.logger.warn(new Date(), "RUNNING TASKS!");
      if (!this.postgresClient) {
        await this.connect();
      }

      await this.replaceGameIDsTask();
      await this.removeShortSessionsTask();

      await sleep(30 * 1000);
    }
  }

  async fetchSessions(userID?: string, gameID?: number): Promise<Session[]> {
    const sessions = new Array<Session>();

    // Order by id DESC to get recent first
    let query = "SELECT * FROM activity ORDER BY id DESC";
    let values: any[] = [];
    if (userID && gameID) {
      query =
        "SELECT * FROM activity WHERE user_id = $1 AND game_id = $2 ORDER BY id DESC";
      values = [userID, gameID];
    } else if (userID) {
      query = "SELECT * FROM activity WHERE user_id = $1 ORDER BY id DESC";
      values = [userID];
    } else if (gameID) {
      query = "SELECT * FROM activity WHERE game_id = $1 ORDER BY id DESC";
      values = [gameID];
    }

    this.logger.log(query, values);

    try {
      const result = await this.postgresClient!.query(query, values);
      for (const r of result.rows) {
        sessions.push({
          id: +r[0],
          date: new Date(r[1]),
          userID: r[2],
          gameID: +r[3],
          seconds: +r[4],
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
      const result = await this.postgresClient!.query(
        "SELECT name FROM game WHERE id = $1",
        [gameID]
      );
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
      const result = await this.postgresClient!.query(
        "SELECT id FROM game WHERE name = $1",
        [gameName]
      );
      if (result.rows.length > 0) {
        return result.rows[0][0] as number;
      }
    } catch (error) {
      this.logger.error("Error fetching data:", error);
    }
    return null;
  }

  async fetchGame(gameID: number): Promise<Game | null> {
    const gameName = await this.fetchGameName(gameID);
    if (!gameName) {
      this.logger.error("Game name not found");
      return null;
    }

    try {
      const sessions = await this.fetchSessions(undefined, gameID);
      return new Game(gameID, gameName, sessions);
    } catch (error) {
      this.logger.error("Error fetching data:", error);
    }

    return null;
  }

  async fetchUser(userID: string): Promise<User | null> {
    const sessions = await this.fetchSessions(userID);
    if (sessions.length === 0) {
      return null;
    }

    const gotGames = new Set<number>();
    const games: Game[] = [];
    for (const s of sessions) {
      if (gotGames.has(s.gameID)) {
        continue;
      }
      gotGames.add(s.gameID);
      const game = await this.fetchGame(s.gameID);
      if (game) {
        games.push(game);
      }
    }

    return new User(userID, sessions, games);
  }

  async fetchGames(): Promise<Game[]> {
    try {
      const result = await this.postgresClient!.query(
        //"SELECT * FROM game ORDER BY name ASC"
        "SELECT * FROM game"
      );
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
    return await this.postgresClient!.query(
      `INSERT INTO activity (timestamp, user_id, game_id, seconds)
     VALUES (to_timestamp($1), $2, $3, $4)`,
      [date.getTime() / 1000, userID, gameID, seconds]
    );
  }

  async deleteActivity(id: number): Promise<ResultRecord<any>> {
    return await this.postgresClient!.query(
      `DELETE FROM activity WHERE id = $1`,
      [id]
    );
  }

  async replaceActivityGameID(
    sessionID: number,
    newGameID: number
  ): Promise<ResultRecord<any>> {
    return await this.postgresClient!.query(
      `UPDATE activity 
     SET game_id = $1 
     WHERE id = $2`,
      [newGameID, sessionID]
    );
  }

  async replaceGameIDsTask() {
    for (const d of REPLACERS) {
      const parentID = await this.fetchGameIDFromGameName(d.parent);
      if (!parentID) {
        this.logger.warn("Did not find parent ID for", d.parent);
        continue;
      }
      for (const c of d.children) {
        const childID = await this.fetchGameIDFromGameName(c);
        if (!childID) {
          this.logger.warn("Did not find child ID for", c);
          continue;
        }
        const sessions = await this.fetchSessions(undefined, childID);
        for (const s of sessions) {
          await this.replaceActivityGameID(s.id, parentID);
        }
      }
    }
  }

  async removeShortSessionsTask() {
    const sessions = await this.fetchSessions();
    for (const s of sessions) {
      if (s.seconds < 60) {
        await this.deleteActivity(s.id);
      }
    }
  }
}
