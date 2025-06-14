import { Session } from "./session";

export class Platform {
  internalName: string;
  sessions: Session[];

  private _cachedTotalPlaytime = 0;

  constructor(internalName: string, sessions: Session[]) {
    this.internalName = internalName;
    this.sessions = sessions;
  }

  /** "Pretty name" of the platform */
  displayName(): string {
    switch (this.internalName.toLowerCase()) {
      case "steam-deck":
        return "Steam Deck";
      case "switch":
        return "Nintendo Switch";
      case "switch2":
        return "Nintendo Switch 2";
      default:
        return this.internalName.toUpperCase();
    }
  }

  /** Total playtime in seconds of the platform */
  totalPlaytime(): number {
    if (this._cachedTotalPlaytime > 0) {
      return this._cachedTotalPlaytime;
    }
    let sum = 0;
    for (const s of this.sessions) {
      sum += s.seconds;
    }
    this._cachedTotalPlaytime = sum;
    return sum;
  }

  /** How many players have used this platform */
  playerCount(): number {
    const userIds = new Set<string>();
    for (const s of this.sessions) {
      userIds.add(s.userID);
    }
    return userIds.size;
  }

  /** How many games have been played on this platform */
  gamesCount(): number {
    const gameIds = new Set<number>();
    for (const s of this.sessions) {
      gameIds.add(s.gameID);
    }
    return gameIds.size;
  }

  /** Color for the platform */
  color(): string {
    switch (this.internalName.toLowerCase()) {
      case "pc":
        return "orange";
      case "steam-deck":
        return "#6E56C0"; // Steam Deck purple
      case "xbox":
        return "lime";
      case "xbox360":
      case "xboxone":
      case "xboxseries":
        return "#0e7a0d";
      case "ps4":
        return "#006FCD";
      case "ps5":
        return "black";
      case "switch":
      case "switch2":
        return "#E60012";
      default:
        return "black";
    }
  }
}
