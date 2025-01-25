import { Client, Configuration, connect, ResultRecord } from "ts-postgres";
import { Game } from "./game";
import { Session } from "./session";

export class Postgres {
  private postgresClient: Client | null = null;
  private config: Configuration;
  constructor(config: Configuration) {
    this.config = config;
  }

  async connect() {
    this.postgresClient = await connect(this.config);
  }

  async fetchSessions(userID?: string, gameID?: number): Promise<Session[]> {
    const sessions = new Array<Session>();
    if (!this.postgresClient) {
      await this.connect();
    }

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

    console.log(query, values);

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
      console.error("Error fetching activity:", error);
    }
    //console.log(sessions);
    return sessions;
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

  async fetchGame(gameID: number): Promise<Game | null> {
    if (!this.postgresClient) {
      await this.connect();
    }
    const gameName = await this.fetchGameName(gameID);
    if (!gameName) {
      console.error("Game name not found");
      return null;
    }

    try {
      const sessions = await this.fetchSessions(undefined, gameID);
      return new Game(gameID, gameName, sessions);
    } catch (error) {
      console.error("Error fetching data:", error);
    }

    return null;
  }

  async fetchGames(): Promise<Game[]> {
    if (!this.postgresClient) {
      await this.connect();
    }
    try {
      const result = await this.postgresClient!.query(
        "SELECT * FROM game ORDER BY name ASC"
      );
      const games: Game[] = [];
      for (const r of result.rows) {
        const gameID = r[0];
        const gameName = r[1];
        const sessions = await this.fetchSessions(undefined, gameID);
        games.push(new Game(gameID, gameName, sessions));
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
