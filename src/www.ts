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
    let TR = `<tr ><th></th><th>Username</th><th>Time Played</th></tr>`;
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
      TR += `<td sorttable_customkey="${userInfo.playtime}" title="${
        userInfo.playtime
      } seconds" class="col align-middle">${formatSeconds(
        userInfo.playtime
      )}</td>`;
      TR += `</tr>`;
    }
    let html = await readFile(join(__dirname, "../static/users.html"), "utf-8");
    html = html.replace("<%TABLE_ROWS%>", TR);
    return this.constructHTML(html);
  }

  async gamesPage(): Promise<string> {
    const gs = await this.postgres.fetchGames();
    let TR = `<tr ><th>Name</th><th>Players</th><th >Time Played</th></tr>`;
    for (const g of gs) {
      const stats = await this.postgres.fetchGameStatsGlobal(g.id);
      TR += `<tr>`;
      TR += "<td>" + g.game_name + "</td>";
      TR += "<td>" + stats.players + "</td>";
      TR +=
        `<td sorttable_customkey="${stats.time_played}" title="${stats.time_played} seconds">` +
        formatSeconds(stats.time_played) +
        "</td>";
      TR += `</tr>`;
    }
    let html = await readFile(join(__dirname, "../static/games.html"), "utf-8");
    html = html.replace("<%TABLE_ROWS%>", TR);
    return this.constructHTML(html);
  }

  async getUserData(userID: string): Promise<ProfileData> {
    const prof = new User(this.postgres, userID);
    await prof.generate();
    return await prof.getData();
  }

  async userPage(userID: string): Promise<string> {
    const res = await this.getUserData(userID);
    if (res.games.length === 0) {
      return await this.errorPage("Unknown user.");
    }
    const discordInfo = await this.discord.getUser(userID);

    let TR =
      "<tr><th>Game</th><th>Time played</th><th>Sessions</th><th>Last played</th>";
    for (const r of res.games) {
      TR += "<tr>";
      TR += "<td>" + r.game_name + "</td>";
      TR +=
        `<td sorttable_customkey="${r.time_played}" title="${r.time_played} seconds">` +
        formatSeconds(r.time_played) +
        "</td>";
      TR += "<td>" + r.sessions + "</td>";
      TR +=
        `<td sorttable_customkey="${r.last_played.getTime()}" title="${r.last_played.toUTCString()}">` +
        timeSince(r.last_played) +
        "</td>";
      TR += "</tr>";
    }
    let html = await readFile(join(__dirname, "../static/user.html"), "utf-8");
    html = html.replace("<%USERNAME%>", discordInfo!.username);
    html = html.replace("<%AVATAR_URL%>", discordInfo!.avatarURL);
    html = html.replace("<%TABLE_ROWS%>", TR);
    html = html.replace("<%TOTAL_PLAYTIME%>", formatSeconds(res.playtime) + "");
    html = html.replace("<%SESSIONS%>", res.sessions + "");
    html = html.replace("<%LAST_ACTIVE%>", res.lastActive.toUTCString());
    html = html.replace("<%LAST_ACTIVE_AGO%>", timeSince(res.lastActive));
    return this.constructHTML(html);
  }

  async errorPage(msg: string, title = "Error"): Promise<string> {
    let html = await readFile(join(__dirname, "../static/error.html"), "utf-8");
    html = html.replace("<%TITLE%>", title);
    html = html.replace("<%MSG%>", msg);
    return this.constructHTML(html);
  }
}
