import { Postgres } from "./postgres";

export interface GameEntry {
  gameID: number;
  gameName: string;
  timePlayed: number;
  sessions: number;
  lastPlayed: Date;
}

export interface ProfileData {
  userID: string;
  games: GameEntry[];
  sessions: number;
  timePlayed: number;
  lastActive: Date;
}

export class User {
  private pgClient: Postgres;
  private userID: string;
  private games: GameEntry[];
  private lastActive = new Date(0);

  constructor(pgClient: Postgres, userID: string) {
    this.pgClient = pgClient;
    this.userID = userID;
    this.games = new Array<GameEntry>();
  }

  async generate() {
    await this.fillGames();
  }

  async fillGames() {
    const userActivity = await this.pgClient.fetchSessions(this.userID);

    const m = new Map<number, GameEntry>();
    for (const ua of userActivity) {
      const game_id = ua.gameID;
      const game_name = await this.pgClient.fetchGameName(game_id);

      const data: GameEntry = {
        gameID: game_id,
        timePlayed: ua.seconds,
        lastPlayed: ua.date,
        gameName: game_name || "null",
        sessions: 1,
      };

      // Update user last active
      if (ua.date.getTime() > this.lastActive.getTime()) {
        this.lastActive = ua.date;
      }

      if (m.has(data.gameID)) {
        const existing = m.get(data.gameID)!;
        existing.timePlayed += data.timePlayed;
        existing.sessions += 1;
        if (existing.lastPlayed.getTime() < data.lastPlayed.getTime()) {
          existing.lastPlayed = data.lastPlayed;
        }
      } else {
        m.set(data.gameID, data);
      }
    }
    this.games = [...m.values()];
  }

  get totalPlaytime(): number {
    let sum = 0;
    for (const g of this.games) {
      sum += g.timePlayed;
    }
    return sum;
  }

  get totalSessions(): number {
    let sum = 0;
    for (const g of this.games) {
      sum += g.sessions;
    }
    return sum;
  }

  async getData(): Promise<ProfileData> {
    return {
      userID: this.userID,
      games: this.games,
      sessions: this.totalSessions,
      timePlayed: this.totalPlaytime,
      lastActive: this.lastActive,
    };
  }
}
