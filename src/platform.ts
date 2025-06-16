import { Session } from "./session";

const VALID_PLATFORMS = [
  "pc",
  "switch",
  "switch2",
  "ps1",
  "ps2",
  "ps3",
  "ps4",
  "ps5",
  "xbox",
  "xbox360",
  "xboxone",
  "xboxseries",
  "steam-deck",
  "nes",
  "snes",
  "n64",
  "gamecube",
  "wii",
  "wiiu",
  "ds",
  "3ds",
  "psp",
  "vita",
] as const;
export type PlatformName = (typeof VALID_PLATFORMS)[number];

export class Platform {
  name: PlatformName;
  sessions: Session[];

  private _cachedTotalPlaytime = 0;

  constructor(internalName: PlatformName, sessions: Session[]) {
    this.name = internalName;
    this.sessions = sessions;
  }

  /** "Pretty name" of the platform */
  displayName(): string {
    switch (this.name) {
      case "steam-deck":
        return "Steam Deck";
      case "switch":
        return "Nintendo Switch";
      case "switch2":
        return "Nintendo Switch 2";
      default:
        return this.name.toUpperCase();
    }
  }

  /**
   * Returns bootstrap icon class for the platform.
   */
  bootstrapIcon(): string {
    switch (this.name) {
      case "switch":
      case "switch2":
        return "bi-nintendo-switch";
      case "ps1":
      case "ps2":
      case "ps3":
      case "ps4":
      case "ps5":
        return "bi-playstation";
      case "xbox":
      case "xbox360":
      case "xboxone":
      case "xboxseries":
        return "bi-xbox";
      case "steam-deck":
        return "bi-steam";
      case "pc":
        return "bi-pc-display";
      default:
        return "bi-controller"; // Fallback
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
    return ""; // disabled for now... colors need to look good on both dark and light mode
    switch (this.name.toLowerCase()) {
      case "pc":
        return "black";
      //return "rgb(171, 137, 1)"; // PCMR
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
