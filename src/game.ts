import { STATICS } from "./index";
import { Logger } from "./logger";
import { Session } from "./session";
import { colorFromString, formatSeconds, timeSince } from "./utils";
import { readFile } from "fs/promises";
import { join } from "path";

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

  /** Constructs a Game object by ID. Async because it makes DB calls. */
  public static async fromID(gameID: number): Promise<Game | null> {
    const logger = new Logger("Game.fromID");
    const gameName = await STATICS.pg.fetchGameName(gameID);
    if (!gameName) {
      logger.error("Game name not found");
      return null;
    }

    try {
      const sessions = await STATICS.pg.fetchSessions(undefined, gameID);
      return new Game(gameID, gameName, sessions);
    } catch (error) {
      logger.error("Error fetching data:", error);
    }

    return null;
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

  /** Total playtime across all users */
  totalPlaytime(): number {
    let sum = 0;
    for (const s of this.sessions) {
      sum += s.seconds;
    }
    return sum;
  }

  get color(): string {
    return colorFromString(this.name);
  }

  /** Total playtime for a single user  */
  totalPlaytimeForUser(userID: string): number {
    let sum = 0;
    for (const s of this.sessions) {
      if (s.userID === userID) {
        sum += s.seconds;
      }
    }
    return sum;
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

  chartData() {
    const sessions = [...this.sessions].reverse();
    const playtimeByDate: Record<string, number> = {};
    // Fill in blank days
    const first = sessions[0].date;
    const today = new Date();
    let now = first;
    while (now.getTime() < today.getTime()) {
      const day = now.toISOString().split("T")[0];
      playtimeByDate[day] = 0;
      now = new Date(now.getTime() + 86400 * 1000);
    }
    // Add today if its not in there
    const todayString = today.toISOString().split("T")[0];
    if (!playtimeByDate[todayString]) {
      playtimeByDate[todayString] = 0;
    }

    // Add session data
    sessions.forEach(({ date, seconds }) => {
      const day = date.toISOString().split("T")[0]; // Convert Date to YYYY-MM-DD string
      playtimeByDate[day] = playtimeByDate[day] + seconds;
    });

    return {
      labels: Object.keys(playtimeByDate),
      values: Object.values(playtimeByDate).map((sec) => sec / 3600),
    };
  }

  /** Generates HTML for the game page */
  async page(): Promise<string> {
    let TR = "";

    for (const userId of this.players) {
      const stats = this.getGameStatsForUser(userId);
      const discordInfo = await STATICS.discord.getUser(userId);

      TR += `<tr class="align-middle">`;
      TR += `<td class="col-lg-1"><a href="/user/${userId}" ><img src="${
        discordInfo!.avatarURL
      }" class="img-thumbnail img-fluid rounded-circle"></a></td>`;
      TR += `<td class="col"><a href="/user/${userId}">${
        discordInfo!.username
      }</td></a>`;
      TR += `<td sorttable_customkey="${stats.seconds}" title="${
        stats.seconds
      } seconds" class="col align-middle">${formatSeconds(stats.seconds)}</td>`;
      TR += `<td>${stats.sessions.length}</td>`;
      TR += `<td sorttable_customkey="${
        stats.longestSession.seconds
      }" title="${stats.longestSession.date.toUTCString()}">${formatSeconds(
        stats.longestSession.seconds
      )}</td>`;
      TR += `<td sorttable_customkey="${stats.lastPlayed.getTime()}" title="${stats.lastPlayed.toUTCString()}" class="col align-middle">${timeSince(
        stats.lastPlayed
      )}</td>`;
      TR += `</tr>\n`;
    }

    let html = await readFile(join(__dirname, "../static/game.html"), "utf-8");
    html = html.replaceAll("<%TABLE_ROWS%>", TR);
    html = html.replaceAll("<%GAME_NAME%>", this.name);
    html = html.replaceAll("<%GAME_COLOR%>", this.color);
    html = html.replaceAll("<%PLAYER_COUNT%>", this.players.length + "");
    html = html.replaceAll("<%SESSIONS%>", this.sessions.length + "");
    html = html.replaceAll(
      "<%TOTAL_PLAYTIME%>",
      formatSeconds(this.totalPlaytime())
    );
    html = html.replace("<%CHART%>", this.getChart());
    return await STATICS.web.constructHTML(html, this.name);
  }

  getChart(): string {
    return `
      <canvas id="myChart"></canvas>
        <script>
        document.addEventListener("DOMContentLoaded", function () {
        if (typeof Chart === "undefined") {
            console.error("Chart.js failed to load.");
            return;
        }

        fetch("/game/${this.id}/chartData")
            .then(res => res.json())
            .then(data => {
                const ctx = document.getElementById("myChart").getContext("2d");
                new Chart(ctx, {
                    type: "bar",
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: "Hours Played",
                            data: data.values,
                            backgroundColor: "${this.color}",
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            //title: {display: true, text: "Hours played"},
                            legend: { position: "top", display: false},
                        },
                        scales: {
                            x: { stacked: true }, // Stack bars by game
                            y: { stacked: true }
                        }
                    }
                });
            })
            .catch(err => console.error("Failed to load chart data:", err));
    });
        </script>`;
  }
}
