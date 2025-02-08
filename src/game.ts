import { Session } from "./session";
import { colorFromString } from "./utils";

export interface GameStatsForPlayer {
  seconds: number;
  lastPlayed: Date;
  longestSession: Session;
  sessions: Session[];
}

export class Game {
  readonly id: number;
  readonly name: string;
  readonly sessions: Session[];
  constructor(id: number, name: string, sessions: Session[]) {
    this.id = id;
    this.name = name;
    this.sessions = sessions;
  }

  get lastPlayed(): Date {
    let latest = new Date(0);
    for (const s of this.sessions) {
      if (s.date.getTime() > latest.getTime()) {
        latest = s.date;
      }
    }
    return latest;
  }

  get totalSessions(): number {
    return this.sessions.length;
  }

  get totalPlaytime(): number {
    let sum = 0;
    for (const s of this.sessions) {
      sum += s.seconds;
    }
    return sum;
  }

  get color(): string {
    return colorFromString(this.name);
  }

  /**
   * Returns user IDs that have played this game
   */
  get players(): string[] {
    let userIds = new Set<string>();
    for (const s of this.sessions) {
      userIds.add(s.userID);
    }
    return [...userIds];
  }

  getGameStatsForUser(userID: string): GameStatsForPlayer {
    const playerSessions: Session[] = [];
    for (const s of this.sessions) {
      if (s.userID === userID) {
        playerSessions.push(s);
      }
    }
    let lastPlayed = new Date(0);
    let totalPlayed = 0;
    let longestSession = playerSessions[0];
    for (const s of playerSessions) {
      totalPlayed += s.seconds;
      if (s.date.getTime() > lastPlayed.getTime()) {
        lastPlayed = s.date;
      }
      if (s.seconds > longestSession.seconds) {
        longestSession = s;
      }
    }
    return {
      seconds: totalPlayed,
      lastPlayed: lastPlayed,
      sessions: playerSessions,
      longestSession: longestSession,
    };
  }
}
