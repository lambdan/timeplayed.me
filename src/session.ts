export class Session {
  id: number;
  date: Date;
  userID: string;
  gameID: number;
  seconds: number;
  platform: string;
  constructor(
    id: number,
    date: Date,
    userID: string,
    gameID: number,
    seconds: number,
    platform: string
  ) {
    this.id = id;
    this.date = date;
    this.userID = userID;
    this.gameID = gameID;
    this.seconds = seconds;
    this.platform = platform;
  }
}