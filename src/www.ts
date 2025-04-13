import { join } from "path";
import { readFile } from "fs/promises";
import { formatSeconds, sanitizeHTML, timeSince } from "./utils";
import { Game } from "./game";
import { STATICS } from ".";
import { Logger } from "./logger";
import { User } from "./user";

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
      const game = await Game.fromID(session.gameID);

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
      const user = await User.fromID(u);

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

  async errorPage(msg: string, title = "Error"): Promise<string> {
    let html = await readFile(join(__dirname, "../static/error.html"), "utf-8");
    html = html.replace("<%TITLE%>", title);
    html = html.replace("<%MSG%>", msg);
    return await this.constructHTML(html, "Error");
  }
}
