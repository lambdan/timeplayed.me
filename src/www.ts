import { join } from "path";
import { Postgres } from "./postgres";
import { User, ProfileData } from "./user";
import { readFile } from "fs/promises";
import { Discord } from "./discord";
import { formatSeconds, timeSince } from "./utils";

const APP_VERSION = require("../package.json").version;

export class www {
  private postgres: Postgres;
  private discord: Discord;

  constructor(postgres: Postgres, discord: Discord) {
    this.postgres = postgres;
    this.discord = discord;
  }

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
    return this.constructHTML(
      await readFile(join(__dirname, "../static/frontpage.html"), "utf-8")
    );
  }

  async usersPage(): Promise<string> {
    const users = await this.postgres.fetchUserIDs();
    let TR = `<tr ><th></th><th>Username</th><th>Time Played</th><th>Last Active</th></tr>`;
    for (const u of users) {
      const discordInfo = await this.discord.getUser(u);
      const userInfo = await this.getUserData(u);
      TR += `<tr >`;
      TR += `<td class="col-lg-1"><a href="user/${u}" ><img src="${
        discordInfo!.avatarURL
      }" class="img-thumbnail img-fluid rounded-circle"></a></td>`;
      TR += `<td class="col align-middle"><a href="user/${u}">${
        discordInfo!.username
      }</td></a>`;
      TR += `<td sorttable_customkey="${userInfo.timePlayed}" title="${
        userInfo.timePlayed
      } seconds" class="col align-middle">${formatSeconds(
        userInfo.timePlayed
      )}</td>`;
      TR += `<td sorttable_customkey="${userInfo.lastActive.getTime()}" title="${userInfo.lastActive.toUTCString()}" class="col align-middle">${timeSince(
        userInfo.lastActive
      )}</td>`;
      TR += `</tr>\n`;
    }
    let html = await readFile(join(__dirname, "../static/users.html"), "utf-8");
    html = html.replace("<%TABLE_ROWS%>", TR);
    return this.constructHTML(html);
  }

  async gamesPage(): Promise<string> {
    const gs = await this.postgres.fetchGames();
    let totalTime = 0;
    let totalSessions = 0;
    let TR = "";
    for (const g of gs) {
      const stats = await this.postgres.fetchGameStatsGlobal(g.gameID);
      TR += `<tr>`;
      TR += `<td><a href="/game/${g.gameID}">` + g.gameName + "</a></td>";
      TR += "<td>" + stats.players + "</td>";
      TR += "<td>" + stats.sessions + "</td>";
      TR +=
        `<td sorttable_customkey="${stats.timePlayed}" title="${stats.timePlayed} seconds">` +
        formatSeconds(stats.timePlayed) +
        "</td>";
      TR += `</tr>\n`;
      totalTime += stats.timePlayed;
      totalSessions += stats.sessions;
    }
    let html = await readFile(join(__dirname, "../static/games.html"), "utf-8");
    html = html.replaceAll("<%TABLE_ROWS%>", TR);
    html = html.replaceAll("<%TOTAL_PLAYTIME%>", formatSeconds(totalTime));
    html = html.replaceAll("<%TOTAL_SESSIONS%>", totalSessions + "");
    html = html.replaceAll("<%GAME_COUNT%>", gs.length + "");
    return this.constructHTML(html);
  }

  async getUserData(userID: string): Promise<ProfileData> {
    const prof = new User(this.postgres, userID);
    await prof.generate();
    return await prof.getData();
  }

  async gamePage(gameID: number): Promise<string> {
    const gameName = await this.postgres.fetchGameName(gameID);
    if (!gameName) {
      return await this.errorPage("Unknown game");
    }

    const res = await this.postgres.fetchGameStatsGlobal(gameID);

    let TR = "";
    for (const userStat of res.userStats) {
      const userId = userStat[0];
      const stats = userStat[1];
      const discordInfo = await this.discord.getUser(userId);

      TR += `<tr class="align-middle">`;
      TR += `<td class="col-lg-1"><a href="user/${userId}" ><img src="${
        discordInfo!.avatarURL
      }" class="img-thumbnail img-fluid rounded-circle"></a></td>`;
      TR += `<td class="col"><a href="user/${userId}">${
        discordInfo!.username
      }</td></a>`;
      TR += `<td sorttable_customkey="${res.timePlayed}" title="${
        stats.timePlayed
      } seconds" class="col align-middle">${formatSeconds(
        stats.timePlayed
      )}</td>`;
      TR += `<td>${stats.sessions}</td>`;
      TR += `<td sorttable_customkey="${stats.lastPlayed.getTime()}" title="${stats.lastPlayed.toUTCString()}" class="col align-middle">${timeSince(
        stats.lastPlayed
      )}</td>`;
      TR += `</tr>\n`;
    }

    let html = await readFile(join(__dirname, "../static/game.html"), "utf-8");
    html = html.replaceAll("<%TABLE_ROWS%>", TR);
    html = html.replaceAll("<%GAME_NAME%>", gameName);
    html = html.replaceAll("<%PLAYER_COUNT%>", res.players + "");
    html = html.replaceAll("<%SESSIONS%>", res.sessions + "");
    html = html.replaceAll("<%TOTAL_PLAYTIME%>", formatSeconds(res.timePlayed));
    return await this.constructHTML(html);
  }

  async userPage(userID: string): Promise<string> {
    const res = await this.getUserData(userID);
    if (res.games.length === 0) {
      return await this.errorPage("Unknown user.");
    }
    const discordInfo = await this.discord.getUser(userID);

    let TR = "";
    for (const r of res.games) {
      TR += "<tr>";
      TR += `<td><a href="/game/${r.gameID}">` + r.gameName + "</a></td>";
      TR +=
        `<td sorttable_customkey="${r.timePlayed}" title="${r.timePlayed} seconds">` +
        formatSeconds(r.timePlayed) +
        "</td>";
      TR += "<td>" + r.sessions + "</td>";
      TR +=
        `<td sorttable_customkey="${r.lastPlayed.getTime()}" title="${r.lastPlayed.toUTCString()}">` +
        timeSince(r.lastPlayed) +
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
      formatSeconds(res.timePlayed) + ""
    );
    html = html.replaceAll("<%SESSIONS%>", res.sessions + "");
    html = html.replaceAll("<%LAST_ACTIVE%>", res.lastActive.toUTCString());
    html = html.replaceAll("<%LAST_ACTIVE_AGO%>", timeSince(res.lastActive));
    return this.constructHTML(html);
  }

  async errorPage(msg: string, title = "Error"): Promise<string> {
    let html = await readFile(join(__dirname, "../static/error.html"), "utf-8");
    html = html.replace("<%TITLE%>", title);
    html = html.replace("<%MSG%>", msg);
    return this.constructHTML(html);
  }
}
