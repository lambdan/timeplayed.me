import { join } from "path";
import { Postgres } from "./postgres";
import { User, ProfileData } from "./user";
import { readFile } from "fs/promises";
import { Discord } from "./discord";

const APP_VERSION = require("../package.json").version;

function formatSeconds(secs: number): string {
  if (secs > 3600) {
    return (secs / 3600).toFixed(2) + " hours";
  }
  return (secs / 60).toFixed(2) + " minutes";
  /*
  let val = secs;
  let word = "second";
  if (secs > 3600) {
    word = "hour";
    val = Math.floor(secs / 3600);
  } else if (secs > 60) {
    word = "minute";
    val = Math.floor(secs / 60);
  }
  return `${val} ${word}${val > 1 ? "s" : ""}`;
  */
}

export class www {
  private postgres: Postgres;
  private discord: Discord;

  constructor(postgres: Postgres, discord: Discord) {
    this.postgres = postgres;
    this.discord = discord;
  }

  async constructHTML(content: string): Promise<string> {
    const header = await readFile(join(__dirname, "_header.html"), "utf-8");
    let footer = await readFile(join(__dirname, "_footer.html"), "utf-8");
    footer = footer.replace("<%VERSION%>", APP_VERSION);
    return header + content + footer;
  }

  async frontpage(): Promise<string> {
    return this.constructHTML(
      await readFile(join(__dirname, "frontpage.html"), "utf-8")
    );
  }

  async users(): Promise<string> {
    const users = await this.postgres.fetchUserIDs();
    let TR = ""; //<tr><th></th><th>Username</th>";
    for (const u of users) {
      const discordInfo = await this.discord.getUser(u);
      TR += `<tr>`;
      TR += `<td class="col-1"><a href="user/${u}" ><img src="${
        discordInfo!.avatarURL
      }" class="img-thumbnail img-fluid rounded-circle"></a></td>`;
      TR += `<td class="col align-middle"><a href="user/${u}">${
        discordInfo!.username
      }</td></a>`;
      TR += `</tr>`;
    }
    let html = await readFile(join(__dirname, "users.html"), "utf-8");
    html = html.replace("<%TABLE_ROWS%>", TR);
    return this.constructHTML(html);
  }

  async getProfile(userID: string): Promise<ProfileData> {
    const prof = new User(this.postgres, userID);
    await prof.generate();
    return await prof.getData();
  }

  async getProfileHTML(userID: string): Promise<string> {
    const res = await this.getProfile(userID);
    const discordInfo = await this.discord.getUser(userID);

    let TR =
      "<tr><th>Game</th><th>Time played</th><th>Sessions</th><th>Last played</th>";
    for (const r of res.games) {
      TR += "<tr>";
      TR += "<td>" + r.game_name + "</td>";
      TR += "<td>" + formatSeconds(r.time_played) + "</td>";
      TR += "<td>" + r.sessions + "</td>";
      TR += "<td>" + r.last_played.toUTCString() + "</td>";
      TR += "</tr>";
    }
    let html = await readFile(join(__dirname, "user.html"), "utf-8");
    html = html.replace("<%USERNAME%>", discordInfo!.username);
    html = html.replace("<%AVATAR_URL%>", discordInfo!.avatarURL);
    html = html.replace("<%TABLE_ROWS%>", TR);
    html = html.replace("<%TOTAL_PLAYTIME%>", formatSeconds(res.playtime) + "");
    html = html.replace("<%SESSIONS%>", res.sessions + "");
    return this.constructHTML(html);
  }
}
