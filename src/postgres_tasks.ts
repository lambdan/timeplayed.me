import { Logger } from "./logger";
import { Postgres } from "./postgres";
import { sleep } from "./utils";

// Use these to replace games with multiple titles
const REPLACERS = [
  // Children sessions will be replaced with parent game ID
  {
    parent: "The Elder Scrolls V: Skyrim Special Edition",
    children: ["Skyrim Special Edition"],
  },
  {
    parent: "The Legend of Zelda: Dungeons of Infinity",
    children: ["Zelda Dungeons of Infinity"],
  },
  {
    parent: "Tony Hawk's Pro Skater 3",
    children: ["THPS3 - PARTYMOD"],
  },
];

// Games called this will be removed, use to remove bad data
const BAD_GAMES = ["Steam Deck", "EmulationStationDE"];

export class PostgresTasks {
  private postgres: Postgres;
  private taskLoopRunning = false;
  private logger = new Logger("Postgres Tasks");
  private intervalSecs = 30;
  constructor(postgres: Postgres) {
    this.postgres = postgres;
    this.taskLoop();
  }

  async taskLoop() {
    if (this.taskLoopRunning) {
      return;
    }
    this.taskLoopRunning = true;
    while (true) {
      // Check if postgres is connected

      this.logger.log("RUNNING TASKS!");

      await this.taskReplaceGameIDs();
      await this.taskRemoveShortSessions();
      await this.taskRemoveBadGameSessions();

      await sleep(this.intervalSecs * 1000);
    }
  }

  async taskReplaceGameIDs() {
    this.logger.log("Running taskReplaceGameIDs");
    for (const d of REPLACERS) {
      const parentID = await this.postgres.fetchGameIDFromGameName(d.parent);
      if (!parentID) {
        this.logger.warn("Did not find parent ID for", d.parent);
        continue;
      }
      for (const c of d.children) {
        const childID = await this.postgres.fetchGameIDFromGameName(c);
        if (!childID) {
          this.logger.warn("Did not find child ID for", c);
          continue;
        }
        const sessions = await this.postgres.fetchSessions(undefined, childID);
        for (const s of sessions) {
          await this.postgres.replaceActivityGameID(s.id, parentID);
        }
      }
    }
  }

  async taskRemoveShortSessions() {
    this.logger.log("Running taskRemoveShortSessions");
    const sessions = await this.postgres.fetchSessions();
    for (const s of sessions) {
      if (s.seconds < 60) {
        await this.postgres.deleteActivity(s.id);
      }
    }
  }

  async taskRemoveBadGameSessions() {
    this.logger.log("Running taskRemoveBadGameSessions");
    for (const game of BAD_GAMES) {
      const gameID = await this.postgres.fetchGameIDFromGameName(game);
      if (!gameID) {
        //this.logger.warn("Did not find game ID for", game);
        continue;
      }
      const sessions = await this.postgres.fetchSessions(undefined, gameID);
      for (const s of sessions) {
        await this.postgres.deleteActivity(s.id);
      }
    }
  }
}
