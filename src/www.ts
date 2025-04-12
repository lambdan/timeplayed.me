import { join } from "path";
import { readFile } from "fs/promises";
import { formatSeconds, sanitizeHTML, timeSince } from "./utils";
import { Game } from "./game";
import { STATICS } from ".";
import { Logger } from "./logger";

const APP_VERSION = require("../package.json").version;

export class www {
  private logger = new Logger("www");
  constructor() {}

  async constructHTML(
    content: string,
    title = "Playtime tracking using Discord"
  ): Promise<string> {
    let header = await readFile(
      join(__dirname, "../static/_header.html"),
      "utf-8"
    );
    header = header.replace("<%TITLE%>", sanitizeHTML(title));
    let footer = await readFile(
      join(__dirname, "../static/_footer.html"),
      "utf-8"
    );
    footer = footer.replace("<%VERSION%>", APP_VERSION);
    return (
      header +
      content +
      footer +
      `<!--- Constructed ${new Date().toISOString()} -->`
    );
  }

  async frontPage(): Promise<string> {
    let html = await readFile(
      join(__dirname, "../static/frontpage.html"),
      "utf-8"
    );
    html = html.replace("<%CHART%>", STATICS.totals.getChart());

    // Recent activity table
    let recentActivityTable = "";
    const sessions = await STATICS.pg.fetchSessions(undefined, undefined, 10);
    console.log(sessions);
    for (const session of sessions) {
      const game = await STATICS.pg.fetchGame(session.gameID);
      if (!game) {
        continue;
      }
      const discordInfo = await STATICS.discord.getUser(session.userID);
      recentActivityTable += '<tr class="align-middle">';
      recentActivityTable += `<td class="col-lg-1"><a href="/user/${
        session.userID
      }" ><img src="${
        discordInfo!.avatarURL
      }" class="img-thumbnail img-fluid rounded-circle"></a></td>`;
      recentActivityTable += `<td><a href="/user/${session.userID}">${
        discordInfo!.username
      }</a></td>`;
      recentActivityTable +=
        `<td><a href="/game/${session.gameID}" style="color: ${game.color}">` +
        game.name +
        "</a></td>";
      recentActivityTable += `<td>${formatSeconds(session.seconds)}</td>`;
      recentActivityTable += `<td>${timeSince(session.date)}</td>`;
      recentActivityTable += "</tr>\n";
    }
    html = html.replaceAll("<%RECENT_TABLE_ROWS%>", recentActivityTable);

    return await this.constructHTML(html);
  }

  async usersPage(): Promise<string> {
    const userIDs = await STATICS.pg.fetchUserIDs();
    let TR = `<tr ><th></th><th>Username</th><th>Games Played</th><th>Time Played</th><th>Last Active</th></tr>`;
    for (const u of userIDs) {
      const user = await STATICS.pg.fetchUser(u);
      if (!user) {
        continue;
      }
      const discordInfo = await STATICS.discord.getUser(u);

      TR += `<tr >`;
      TR += `<td class="col-lg-1"><a href="/user/${u}" ><img src="${
        discordInfo!.avatarURL
      }" class="img-thumbnail img-fluid rounded-circle"></a></td>`;
      TR += `<td class="col align-middle"><a href="/user/${u}">${
        discordInfo!.username
      }</td></a>`;
      TR += `<td class="col align-middle">${user.games.length}</td>`;
      TR += `<td sorttable_customkey="${user.totalPlaytime}" title="${
        user.totalPlaytime
      } seconds" class="col align-middle">${formatSeconds(
        user.totalPlaytime()
      )}</td>`;
      TR += `<td sorttable_customkey="${user
        .lastActive()
        .getTime()}" title="${user
        .lastActive()
        .toUTCString()}" class="col align-middle">${timeSince(
        user.lastActive()
      )}</td>`;
      TR += `</tr>\n`;
    }
    let html = await readFile(join(__dirname, "../static/users.html"), "utf-8");
    html = html.replace("<%TABLE_ROWS%>", TR);
    return await this.constructHTML(html, "Users");
  }

  async gamesPage(): Promise<string> {
    const games = await STATICS.pg.fetchGames();

    let totalTime = 0;
    let totalSessions = 0;
    let TR = "";
    for (const game of games.sort((a, b) => {
      // Sort by total playtime
      return b.totalPlaytime() - a.totalPlaytime();
    })) {
      TR += `<tr>`;
      TR +=
        `<td><a href="/game/${game.id}" style="color: ${game.color}">` +
        game.name +
        "</a></td>";
      TR += "<td>" + game.players.length + "</td>";
      TR += "<td>" + game.sessions.length + "</td>";
      TR += `<td sorttable_customkey="${game.lastPlayed.getTime()}" title="${game.lastPlayed.toUTCString()}">${timeSince(
        game.lastPlayed
      )}</td>`;
      TR +=
        `<td sorttable_customkey="${game.totalPlaytime()}" title="${game.totalPlaytime()} seconds">` +
        formatSeconds(game.totalPlaytime()) +
        "</td>";
      TR += `</tr>\n`;
      totalTime += game.totalPlaytime();
      totalSessions += game.sessions.length;
    }
    let html = await readFile(join(__dirname, "../static/games.html"), "utf-8");
    html = html.replaceAll("<%TABLE_ROWS%>", TR);
    html = html.replaceAll("<%TOTAL_PLAYTIME%>", formatSeconds(totalTime));
    html = html.replaceAll("<%TOTAL_SESSIONS%>", totalSessions + "");
    html = html.replaceAll("<%GAME_COUNT%>", games.length + "");
    return await this.constructHTML(html, "Games");
  }

  async gamePage(gameID: number): Promise<string> {
    const game = await STATICS.pg.fetchGame(gameID);

    if (!game) {
      return await this.errorPage("Unknown game");
    }

    let TR = "";

    for (const userId of game.players) {
      const stats = game.getGameStatsForUser(userId);
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
    html = html.replaceAll("<%GAME_NAME%>", game.name);
    html = html.replaceAll("<%GAME_COLOR%>", game.color);
    html = html.replaceAll("<%PLAYER_COUNT%>", game.players.length + "");
    html = html.replaceAll("<%SESSIONS%>", game.sessions.length + "");
    html = html.replaceAll(
      "<%TOTAL_PLAYTIME%>",
      formatSeconds(game.totalPlaytime())
    );
    html = html.replace("<%CHART%>", game.getChart());
    return await this.constructHTML(html, game.name);
  }

  async userPage(userID: string): Promise<string> {
    const user = await STATICS.pg.fetchUser(userID);
    if (!user) {
      return await this.errorPage("Unknown user.");
    }
    const discordInfo = await STATICS.discord.getUser(userID);
    let html = await readFile(join(__dirname, "../static/user.html"), "utf-8");

    // Recent activity table
    let recentActivity = "";
    let recentActivityCount = 0;
    const sessionsRecent = user.sessions.sort(
      (a, b) => b.date.getTime() - a.date.getTime()
    );
    for (let i = 0; i < Math.min(10, sessionsRecent.length); i++) {
      const session = sessionsRecent[i];
      const game = await STATICS.pg.fetchGame(session.gameID);
      if (!game) {
        continue;
      }
      recentActivity += "<tr>";
      recentActivity +=
        `<td><a href="/game/${session.gameID}" style="color: ${game.color}">` +
        game.name +
        "</a></td>";
      recentActivity += `<td>${formatSeconds(session.seconds)}</td>`;
      recentActivity += `<td>${timeSince(session.date)}</td>`;

      recentActivity += "</tr>\n";
      recentActivityCount++;
    }
    html = html.replaceAll("<%TABLE_RECENT_ROWS%>", recentActivity);

    // Top games table
    let topGamesTable = "";
    const games = [...user.games];
    games.sort((a, b) => {
      return b.totalPlaytimeForUser(userID) - a.totalPlaytimeForUser(userID);
    });
    for (const game of games) {
      console.log(game.name);
      const gameStat = game.getGameStatsForUser(userID);
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
    //html = html.replace("<%BORDER_COLOR%>", discordInfo!.bannerColor);
    html = html.replaceAll("<%AVATAR_URL%>", discordInfo!.avatarURL);
    html = html.replaceAll("<%TABLE_ROWS%>", topGamesTable);
    html = html.replaceAll(
      "<%TOTAL_PLAYTIME%>",
      formatSeconds(user.totalPlaytime()) + ""
    );
    html = html.replaceAll("<%SESSIONS%>", user.sessions.length + "");
    html = html.replaceAll("<%LAST_ACTIVE%>", user.lastActive().toUTCString());
    /*html = html.replaceAll("<%LAST_ACTIVE_AGO%>", timeSince(user.lastActive()));*/
    html = html.replaceAll("<%GAMES_PLAYED%>", user.games.length + "");
    html = html.replaceAll(
      "<%AVERAGE_PLAYTIME_GAME%>",
      formatSeconds(user.averagePlaytimePerGame())
    );
    html = html.replaceAll(
      "<%AVERAGE_SESSIONS_GAME%>",
      Math.floor(user.averageSessionsPerGame()) + ""
    );
    html = html.replaceAll(
      "<%AVERAGE_SESSION_LENGTH%>",
      formatSeconds(user.averageSessionLength())
    );
    html = html.replaceAll("<%ACTIVE_DAYS%>", user.activeDays() + "");
    html = html.replaceAll(
      "<%LONGEST_BREAK%>",
      formatSeconds(user.longestBreak(), 1)
    );
    html = html.replaceAll(
      "<%MOST_CONSECUTIVE_DAYS%>",
      user.mostConsecutiveDays() + ""
    );
    html = html.replaceAll(
      "<%FIRST_SESSION%>",
      user.firstSessionDate().toUTCString()
    );

    /*html = html.replaceAll(
      "<%FIRST_SESSION_AGO%>",
      timeSince(user.firstSession())
    );*/
    html = html.replaceAll("<%CHART%>", user.getChart());
    return await this.constructHTML(html, discordInfo.username);
  }

  async errorPage(msg: string, title = "Error"): Promise<string> {
    let html = await readFile(join(__dirname, "../static/error.html"), "utf-8");
    html = html.replace("<%TITLE%>", title);
    html = html.replace("<%MSG%>", msg);
    return await this.constructHTML(html, "Error");
  }
}
