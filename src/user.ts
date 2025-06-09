import { Game } from "./game";
import { Session } from "./session";
import { readFile } from "fs/promises";
import { join } from "path";
import { formatSeconds, timeSince } from "./utils";
import { Discord } from "./discord";
import { Postgres } from "./postgres";
import { www } from "./www";

export class User {
  readonly id: string;
  readonly sessions: Session[];
  readonly games: Game[];

  constructor(userID: string, sessions: Session[], games: Game[]) {
    this.id = userID;
    this.sessions = sessions;
    this.games = games;
  }

  /** Constructs a User object by ID. Async because it makes DB calls. */
  public static async fromID(userID: string): Promise<User | null> {
    const sessions = await Postgres.GetInstance().fetchSessions(userID);
    if (sessions.length === 0) {
      return null;
    }

    const gotGames = new Set<number>();
    const games: Game[] = [];
    for (const s of sessions) {
      if (gotGames.has(s.gameID)) {
        continue;
      }
      gotGames.add(s.gameID);
      const game = await Game.fromID(s.gameID);
      if (game) {
        games.push(game);
      }
    }

    return new User(userID, sessions, games);
  }

  /** Returns total playtime for user in seconds */
  totalPlaytime(): number {
    let sum = 0;
    for (const s of this.sessions) {
      sum += s.seconds;
    }
    return sum;
  }

  /** Returns the date of users first session (effectively a registration date) */
  firstSessionDate(): Date {
    return this.sessions[this.sessions.length - 1].date;
    /*
    let oldest = this.sessions[0].date.getTime();
    for (const s of this.sessions) {
      oldest = Math.min(oldest, s.date.getTime());
    }
    return new Date(oldest);*/
  }

  /** Returns when users last session was, effectively when they were last active */
  lastActive(): Date {
    return this.sessions[0].date;
    /*let latest = 0;
    for (const s of this.sessions) {
      latest = Math.max(latest, s.date.getTime());
    }
    return new Date(latest);*/
  }

  /** Returns how many days the user has been active */
  activeDays(): number {
    const days = new Set<string>();
    for (const s of this.sessions) {
      days.add(s.date.toISOString().split("T")[0]);
    }
    return days.size;
  }

  /** Longest gap between sessions, in milliseconds */
  longestGap(): number {
    let longest = 0;
    const sessions = [...this.sessions].reverse();
    for (let i = 1; i < sessions.length; i++) {
      const previous = sessions[i - 1].date;
      const now = sessions[i].date;
      const delta = now.getTime() - previous.getTime();
      //console.warn(previous, now, delta);
      longest = Math.max(longest, delta);
    }
    //console.warn("LONGEST:", longest);
    return longest;
  }

  /** Longest break, in seconds */
  longestBreak(): number {
    const deltaFromNow = Date.now() - this.lastActive().getTime();
    const longest = Math.max(this.longestGap(), deltaFromNow);
    return Math.floor(longest / 1000);
  }

  /** How many days the user played games in a row */
  mostConsecutiveDays(): number {
    const daysPlayed = new Set<string>();
    const sessions = [...this.sessions].reverse();
    for (const s of sessions) {
      const day = s.date.toISOString().split("T")[0];
      daysPlayed.add(day);
    }

    let longestStreak = 0;
    const thisStreak = new Set<string>();
    for (const s of sessions) {
      const thisDay = s.date.toISOString().split("T")[0];
      thisStreak.add(thisDay);
      const nextDay = new Date(s.date.getTime() + 86400 * 1000)
        .toISOString()
        .split("T")[0];

      if (!daysPlayed.has(nextDay)) {
        longestStreak = Math.max(longestStreak, thisStreak.size);
        thisStreak.clear();
      }
    }
    return longestStreak;
  }

  /** Average session length in seconds */
  averageSessionLength(): number {
    return this.totalPlaytime() / this.sessions.length;
  }

  /** Average sessions per game  */
  averageSessionsPerGame(): number {
    return this.sessions.length / this.games.length;
  }

  /** Average playtime per game */
  averagePlaytimePerGame(): number {
    return this.totalPlaytime() / this.games.length;
  }

  chartData() {
    const sessions = [...this.sessions].reverse();
    const playtimeByDateAndGame: Record<string, Record<number, number>> = {};

    // 1. Calculate the first and last dates
    const first = sessions[0].date;
    const today = new Date();

    // 2. Generate an array of all dates from first to last
    let now = new Date(first.getTime());
    const allDatesInRange: string[] = [];

    while (now <= today) {
      allDatesInRange.push(now.toISOString().split("T")[0]); // YYYY-MM-DD
      now = new Date(now.getTime() + 86400 * 1000); // Add 1 day (86400 seconds)
    }
    // Add today if its not in there
    const todayString = today.toISOString().split("T")[0];
    if (!allDatesInRange.includes(todayString)) {
      allDatesInRange.push(todayString);
    }

    // 3. Initialize playtime data for all dates and games
    allDatesInRange.forEach((day) => {
      playtimeByDateAndGame[day] = {};
    });

    // 4. Populate playtime data from the sessions
    sessions.forEach(({ date, gameID, seconds }) => {
      const day = date.toISOString().split("T")[0]; // YYYY-MM-DD
      if (!playtimeByDateAndGame[day]) {
        playtimeByDateAndGame[day] = {};
      }

      playtimeByDateAndGame[day][gameID] =
        (playtimeByDateAndGame[day][gameID] || 0) + seconds;
    });

    // 5. Extract unique game IDs and game names
    const games = new Map<number, Game>();
    this.games.forEach((g) => {
      games.set(g.id, g);
    });

    const uniqueGameIDs = Array.from(
      new Set(sessions.map((session) => session.gameID))
    );

    // 6. Format data for Chart.js
    const labels = allDatesInRange; // Dates (x-axis)
    const datasets = uniqueGameIDs.map((gameID) => ({
      label: `${games.get(gameID)!.name}`,
      data: labels.map((date) => {
        return (
          ((playtimeByDateAndGame[date] &&
            playtimeByDateAndGame[date][gameID]) ||
            0) / 3600
        ); // Convert seconds to hours
      }),
      backgroundColor: `${games.get(gameID)!.color}`, // Set specific game color
    }));

    return { labels, datasets };
  }

  /** Generates the HTML string for the user page */
  async page(): Promise<string> {
    const discordInfo = await (await Discord.GetInstance()).getUser(this.id);
    let html = await readFile(join(__dirname, "../static/user.html"), "utf-8");

    // Recent activity table
    let recentActivity = "";
    let recentActivityCount = 0;
    const sessionsRecent = this.sessions.sort(
      (a, b) => b.date.getTime() - a.date.getTime()
    );
    for (let i = 0; i < Math.min(10, sessionsRecent.length); i++) {
      const session = sessionsRecent[i];
      const game = await Game.fromID(session.gameID);

      if (!game) {
        continue;
      }
      recentActivity += "<tr>";
      //recentActivity += `<td>${session.id}</td>`;
      recentActivity +=
        `<td><a href="/game/${session.gameID}" style="color: ${game.color}">` +
        game.name +
        "</a>" + `<br><small>${session.platform}</small>` + "</td>";
      recentActivity += `<td>${formatSeconds(session.seconds)}</td>`;
      recentActivity += `<td>${timeSince(session.date)}</td>`;
      //recentActivity += `<td>${session.platform}</td>`;

      recentActivity += "</tr>\n";
      recentActivityCount++;
    }
    html = html.replaceAll("<%TABLE_RECENT_ROWS%>", recentActivity);

    // Top games table
    let topGamesTable = "";
    const games = [...this.games];
    games.sort((a, b) => {
      return b.totalPlaytimeForUser(this.id) - a.totalPlaytimeForUser(this.id);
    });
    for (const game of games) {
      console.log(game.name);
      const gameStat = game.getGameStatsForUser(this.id);
      topGamesTable += "<tr>";
      topGamesTable +=
        `<td><a href="/game/${game.id}" style="color: ${game.color}">` +
        game.name +
        "</a></td>";
      topGamesTable +=
        `<td sorttable_customkey="${gameStat.seconds}" title="${gameStat.seconds} seconds">` +
        formatSeconds(gameStat.seconds) +
        "</td>";
      topGamesTable += "<td>" + gameStat.sessions.length + "</td>";
      topGamesTable += `<td sorttable_customkey="${
        gameStat.longestSession.seconds
      }" title="${gameStat.longestSession.date.toUTCString()}">${formatSeconds(
        gameStat.longestSession.seconds
      )}</td>`;
      topGamesTable +=
        `<td sorttable_customkey="${gameStat.lastPlayed.getTime()}" title="${gameStat.lastPlayed.toUTCString()}">` +
        timeSince(gameStat.lastPlayed) +
        "</td>";
      topGamesTable += "</tr>\n";
    }

    html = html.replaceAll("<%USERNAME%>", discordInfo!.username);
    html = html.replaceAll("<%AVATAR_URL%>", discordInfo!.avatarURL);
    html = html.replaceAll("<%TABLE_ROWS%>", topGamesTable);
    html = html.replaceAll(
      "<%TOTAL_PLAYTIME%>",
      formatSeconds(this.totalPlaytime()) + ""
    );
    html = html.replaceAll("<%SESSIONS%>", this.sessions.length + "");
    html = html.replaceAll("<%LAST_ACTIVE%>", this.lastActive().toUTCString());
    /*html = html.replaceAll("<%LAST_ACTIVE_AGO%>", timeSince(user.lastActive()));*/
    html = html.replaceAll("<%GAMES_PLAYED%>", this.games.length + "");
    html = html.replaceAll(
      "<%AVERAGE_PLAYTIME_GAME%>",
      formatSeconds(this.averagePlaytimePerGame())
    );
    html = html.replaceAll(
      "<%AVERAGE_SESSIONS_GAME%>",
      Math.floor(this.averageSessionsPerGame()) + ""
    );
    html = html.replaceAll(
      "<%AVERAGE_SESSION_LENGTH%>",
      formatSeconds(this.averageSessionLength())
    );
    html = html.replaceAll("<%ACTIVE_DAYS%>", this.activeDays() + "");
    html = html.replaceAll(
      "<%LONGEST_BREAK%>",
      formatSeconds(this.longestBreak(), 1)
    );
    html = html.replaceAll(
      "<%MOST_CONSECUTIVE_DAYS%>",
      this.mostConsecutiveDays() + ""
    );
    html = html.replaceAll(
      "<%FIRST_SESSION%>",
      this.firstSessionDate().toUTCString()
    );

    html = html.replaceAll("<%CHART%>", this.getChart());
    html = html.replaceAll("<%ALL_SESSIONS_URL%>", `/user/${this.id}/sessions`);
    return await www.GetInstance().constructHTML(html, discordInfo.username);
  }

  async sessionsPage(offset = 0): Promise<string> {
    const OFFSET_INC = 1000;

    const discordInfo = await (await Discord.GetInstance()).getUser(this.id);
    let html = await readFile(
      join(__dirname, "../static/user_sessions.html"),
      "utf-8"
    );

    let sessionsTable = "";
    const sessions = this.sessions.slice(offset, offset + OFFSET_INC);
    const sessionsRecent = sessions.sort(
      (a, b) => b.date.getTime() - a.date.getTime()
    );
    for (let i = 0; i < Math.min(OFFSET_INC, sessionsRecent.length); i++) {
      const session = sessionsRecent[i];
      const game = await Game.fromID(session.gameID);

      if (!game) {
        continue;
      }
      sessionsTable += "<tr>";
      sessionsTable += `<td>${session.id}</td>`;
      sessionsTable +=
        `<td><a href="/game/${session.gameID}" style="color: ${game.color}">` +
        game.name +
        "</a></td>";
      sessionsTable += `<td>${formatSeconds(session.seconds)} (${session.seconds} secs)</td>`;
      sessionsTable += `<td>${session.date.toUTCString()}</td>`;
      sessionsTable += `<td>${session.platform}</td>`;

      sessionsTable += "</tr>\n";
    }
    html = html.replaceAll("<%USERNAME%>", discordInfo!.username);
    html = html.replaceAll("<%TABLE_ROWS%>", sessionsTable);

    const nextOffset = offset + OFFSET_INC;
    if (offset > 0) {
      html = html.replaceAll(
        "<%PREV_LINK%>",
        `<a href="/user/${this.id}/sessions?offset=${Math.max(0, offset - OFFSET_INC)}">Previous</a>`
      );
    } else {
      html = html.replaceAll("<%PREV_LINK%>", "");
    }

    if (nextOffset < this.sessions.length) {
      html = html.replaceAll(
        "<%NEXT_LINK%>",
        `<a href="/user/${this.id}/sessions?offset=${nextOffset}">Next</a>`
      );
    } else {
      html = html.replaceAll("<%NEXT_LINK%>", "");
    }

    return await www
      .GetInstance()
      .constructHTML(html, discordInfo.username + " - all sessions");
  }

  getChart(): string {
    return `
      <canvas id="myChart"></canvas>
        <script>
        document.addEventListener("DOMContentLoaded", function () {
        fetch("/user/${this.id}/chartData")
            .then(res => res.json())
            .then(data => {
                const ctx = document.getElementById("myChart").getContext("2d");
                new Chart(ctx, {
                    type: "bar",
                    data: {
                        labels: data.labels, // Dates
                        datasets: data.datasets // Games as datasets
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
