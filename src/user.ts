import { Postgres } from "./postgres";

export interface GameEntry {
  game_id: number;
  game_name: string;
  time_played: number;
  sessions: number;
  last_played: Date;
}

export interface ProfileData {
  userID: string;
  games: GameEntry[];
  sessions: number;
  playtime: number;
}

export class User {
  private pgClient: Postgres;
  private userID: string;
  private games: GameEntry[];

  constructor(pgClient: Postgres, userID: string) {
    this.pgClient = pgClient;
    this.userID = userID;
    this.games = new Array<GameEntry>();
  }

  async generate() {
    await this.fillGames();
  }

  async fillGames() {
    const data = await this.pgClient.fetchActivity(this.userID);

    const m = new Map<number, GameEntry>();
    for (const d of data) {
      const game_id = d.game_id;
      const game_name = await this.pgClient.fetchGameName(game_id);

      const data: GameEntry = {
        game_id: game_id,
        time_played: d.seconds,
        last_played: d.timestamp,
        game_name: game_name || "null",
        sessions: 1,
      };

      if (m.has(data.game_id)) {
        const existing = m.get(data.game_id)!;
        existing.time_played += data.time_played;
        existing.sessions += 1;
        if (existing.last_played.getTime() < data.last_played.getTime()) {
          existing.last_played = data.last_played;
        }
      } else {
        m.set(data.game_id, data);
      }
    }
    this.games = [...m.values()];
  }

  totalPlaytime(): number {
    let sum = 0;
    for (const g of this.games) {
      sum += g.time_played;
    }
    return sum;
  }

  totalSessions(): number {
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
      sessions: this.totalSessions(),
      playtime: this.totalPlaytime(),
    };
  }
}
