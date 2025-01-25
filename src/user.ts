import { Game } from "./game";
import { Session } from "./session";

export class User {
  readonly userID: string;
  readonly sessions: Session[];
  readonly games: Game[];

  constructor(userID: string, sessions: Session[], games: Game[]) {
    this.userID = userID;
    this.sessions = sessions;
    this.games = games;
  }

  get totalPlaytime(): number {
    let sum = 0;
    for (const s of this.sessions) {
      sum += s.seconds;
    }
    return sum;
  }

  get lastActive(): Date {
    let latest = new Date(0);
    for (const s of this.sessions) {
      if (s.date.getTime() > latest.getTime()) {
        latest = s.date;
      }
    }
    return latest;
  }
}
