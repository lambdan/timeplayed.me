import { Platform } from "./platform";

export class Session {
  id: number;
  date: Date;
  userID: string;
  gameID: number;
  seconds: number;
  platform: Platform;
  constructor(settings: {
    id: number;
    date: Date;
    userID: string;
    gameID: number;
    seconds: number;
    platform: Platform;
  }) {
    this.id = settings.id;
    this.date = settings.date;
    this.userID = settings.userID;
    this.gameID = settings.gameID;
    this.seconds = settings.seconds;
    this.platform = settings.platform;
  }
}
