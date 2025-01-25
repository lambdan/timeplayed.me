export class Session {
  id: number;
  date: Date;
  userID: string;
  gameID: number;
  seconds: number;
  constructor(
    id: number,
    date: Date,
    userID: string,
    gameID: number,
    seconds: number
  ) {
    this.id = id;
    this.date = date;
    this.userID = userID;
    this.gameID = gameID;
    this.seconds = seconds;
  }
}