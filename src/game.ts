import { Discord } from "./discord";
import { Logger } from "./logger";
import { Postgres } from "./postgres";
import { Session } from "./session";
import { colorFromString, formatSeconds, timeSince } from "./utils";
import { readFile } from "fs/promises";
import { join } from "path";
import { www } from "./www";
import { SteamGridDB } from "./SteamGridDB/steamgriddb";

export interface GameStatsForPlayer {
  seconds: number;
  lastPlayed: Date;
  longestSession: Session;
  sessions: Session[];
}

export class Game {
  readonly id: number;
  readonly name: string;
  readonly steam_id: number | null;
  readonly sgdb_id: number | null;
  readonly image_url: string | null;
  readonly aliases: string[];
  readonly release_year: number | null;

  readonly sessions: Session[];
  constructor(
    id: number,
    name: string,
    sessions: Session[],
    steam_id: number | null,
    sgdb_id: number | null,
    image_url: string | null,
    aliases: string[],
    release_year: number | null,
  ) {
    this.id = id;
    this.name = name;
    this.sessions = sessions;
    this.steam_id = steam_id;
    this.sgdb_id = sgdb_id;
    this.image_url = image_url;
    this.aliases = aliases;
    this.release_year = release_year;
  }

  /** Constructs a Game object by ID. Async because it makes DB calls. */
  public static async fromID(gameID: number): Promise<Game | null> {
    const logger = new Logger("Game.fromID");
    return await Postgres.GetInstance().fetchGameById(gameID);
  }

  firstPlayed(): Date {
    let earliest = new Date();
    for (const s of this.sessions) {
      if (s.date.getTime() < earliest.getTime()) {
        earliest = s.date;
      }
    }
    return earliest;
  }

  lastPlayed(): Date {
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
    return "";
    //return colorFromString(this.name);
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

  playedPlatforms(): string[] {
    const platforms = new Set<string>();
    for (const s of this.sessions) {
      platforms.add(s.platform.displayName());
    }
    return [...platforms];
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
      const discordInfo = await (await Discord.GetInstance()).getUser(userId);

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
    html = html.replace("<%PLATFORM_LIST%>", this.playedPlatforms().join(", "));
    html = html.replace("<%CHART%>", this.getChart());
    html = html.replace("<%GAME_IMAGE%>", await this.getCapsuleImage());
    html = html.replace("<%FIRST_PLAYED%>", this.firstPlayed().toUTCString());
    html = html.replace("<%LAST_PLAYED%>", this.lastPlayed().toUTCString());
    html = html.replace("<%GAME_ID%>", this.id.toString());
    html = html.replace("<%STEAM_ID%>", this.steam_id?.toString() || "-");
    html = html.replace("<%SGDB_ID%>", this.sgdb_id?.toString() || "-");
    html = html.replace("<%ALIASES%>", this.aliases?.join(", ") || "-");
    html = html.replace("<%YEAR%>", this.release_year?.toString() || "-");
    return await www.GetInstance().constructHTML(html, this.name);
  }

  /**
   * Returns URL to image,
   * either directly set or from Steam if Steam ID is set
   *  or placeholder if no image is set
   *
   * @param thumb - If true, returns a thumbnail image (267x400), otherwise returns a large image (600x900)
   */
  async getCapsuleImage(thumb = false): Promise<string> {
    if (this.image_url) {
      return this.image_url;
    }

    if (this.steam_id) {
      return `https://shared.steamstatic.com/store_item_assets/steam/apps/${this.steam_id}/library_600x900.jpg`;
    }

    let sgdbId = this.sgdb_id;
    if (!sgdbId) {
      sgdbId = await SteamGridDB.GetInstance().topHitForGame(this.name);
    }
    if (sgdbId) {
      const grid = await SteamGridDB.GetInstance().cacheAndGetGridForGame(
        sgdbId
      );
      if (grid) {
        return thumb ? grid.thumb : grid.url;
      }
    }

    return thumb
      ? "https://placehold.co/267x400?text=No+Image"
      : "https://placehold.co/600x900?text=No+Image";
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
