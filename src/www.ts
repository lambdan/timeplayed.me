import { join } from "path";
import { readFile } from "fs/promises";
import { formatSeconds, timeSince } from "./utils";
import { Game } from "./game";
import { STATICS } from ".";

const APP_VERSION = require("../package.json").version;

export class www {
  constructor() {}

  async constructHTML(content: string): Promise<string> {
    const header = await readFile(
      join(__dirname, "../static/_header.html"),
      "utf-8"
    );
    let footer = await readFile(
      join(__dirname, "../static/_footer.html"),
      "utf-8"
    );
    footer = footer.replace("<%VERSION%>", APP_VERSION);
    return header + content + footer;
  }

  async frontPage(): Promise<string> {
    let html = await readFile(
      join(__dirname, "../static/frontpage.html"),
      "utf-8"
    );
    html = html.replace("<%CHART%>", STATICS.totals.getChart());

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
        user.totalPlaytime
      )}</td>`;
      TR += `<td sorttable_customkey="${user.lastActive.getTime()}" title="${user.lastActive.toUTCString()}" class="col align-middle">${timeSince(
        user.lastActive
      )}</td>`;
      TR += `</tr>\n`;
    }
    let html = await readFile(join(__dirname, "../static/users.html"), "utf-8");
    html = html.replace("<%TABLE_ROWS%>", TR);
    return await this.constructHTML(html);
  }

  async gamesPage(): Promise<string> {
    const sortByLastPlayed = (a: Game, b: Game): number => {
      return b.lastPlayed.getTime() - a.lastPlayed.getTime();
    };

    const games = await STATICS.pg.fetchGames();
    let totalTime = 0;
    let totalSessions = 0;
    let TR = "";
    for (const game of games.sort(sortByLastPlayed)) {
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
        `<td sorttable_customkey="${game.totalPlaytime}" title="${game.totalPlaytime} seconds">` +
        formatSeconds(game.totalPlaytime) +
        "</td>";
      TR += `</tr>\n`;
      totalTime += game.totalPlaytime;
      totalSessions += game.sessions.length;
    }
    let html = await readFile(join(__dirname, "../static/games.html"), "utf-8");
    html = html.replaceAll("<%TABLE_ROWS%>", TR);
    html = html.replaceAll("<%TOTAL_PLAYTIME%>", formatSeconds(totalTime));
    html = html.replaceAll("<%TOTAL_SESSIONS%>", totalSessions + "");
    html = html.replaceAll("<%GAME_COUNT%>", games.length + "");
    return await this.constructHTML(html);
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
      formatSeconds(game.totalPlaytime)
    );
    html = html.replace("<%CHART%>", game.getChart());
    return await this.constructHTML(html);
  }

  async userPage(userID: string): Promise<string> {
    const user = await STATICS.pg.fetchUser(userID);
    if (!user) {
      return await this.errorPage("Unknown user.");
    }
    const discordInfo = await STATICS.discord.getUser(userID);

    let TR = "";
    for (const game of user.games) {
      const stats = game.getGameStatsForUser(userID);
      TR += "<tr>";
      TR +=
        `<td><a href="/game/${game.id}" style="color: ${game.color}">` +
        game.name +
        "</a></td>";
      TR +=
        `<td sorttable_customkey="${stats.seconds}" title="${stats.seconds} seconds">` +
        formatSeconds(stats.seconds) +
        "</td>";
      TR += "<td>" + stats.sessions.length + "</td>";
      TR += `<td sorttable_customkey="${
        stats.longestSession.seconds
      }" title="${stats.longestSession.date.toUTCString()}">${formatSeconds(
        stats.longestSession.seconds
      )}</td>`;
      TR +=
        `<td sorttable_customkey="${stats.lastPlayed.getTime()}" title="${stats.lastPlayed.toUTCString()}">` +
        timeSince(stats.lastPlayed) +
        "</td>";
      TR += "</tr>\n";
    }
    let html = await readFile(join(__dirname, "../static/user.html"), "utf-8");
    html = html.replaceAll("<%USERNAME%>", discordInfo!.username);
    //html = html.replace("<%BORDER_COLOR%>", discordInfo!.bannerColor);
    html = html.replaceAll("<%AVATAR_URL%>", discordInfo!.avatarURL);
    html = html.replaceAll("<%TABLE_ROWS%>", TR);
    html = html.replaceAll(
      "<%TOTAL_PLAYTIME%>",
      formatSeconds(user.totalPlaytime) + ""
    );
    html = html.replaceAll("<%SESSIONS%>", user.sessions.length + "");
    html = html.replaceAll("<%LAST_ACTIVE%>", user.lastActive.toUTCString());
    html = html.replaceAll("<%LAST_ACTIVE_AGO%>", timeSince(user.lastActive));
    html = html.replaceAll("<%TOTAL_GAMES%>", user.games.length + "");
    html = html.replaceAll(
      "<%GAME_PLAYTIME_AVG%>",
      formatSeconds(user.totalPlaytime / user.games.length)
    );
    html = html.replaceAll(
      "<%SESSIONS_AVERAGE%>",
      Math.floor(user.sessions.length / user.games.length) + ""
    );
    html = html.replaceAll(
      "<%SESSION_LENGTH_AVG%>",
      formatSeconds(user.totalPlaytime / user.sessions.length)
    );
    html = html.replaceAll("<%CHART%>", user.getChart());
    return await this.constructHTML(html);
  }

  async errorPage(msg: string, title = "Error"): Promise<string> {
    let html = await readFile(join(__dirname, "../static/error.html"), "utf-8");
    html = html.replace("<%TITLE%>", title);
    html = html.replace("<%MSG%>", msg);
    return await this.constructHTML(html);
  }
}
