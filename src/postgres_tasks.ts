import { Logger } from "./logger";
import { MergeGame } from "./models";
import { Postgres } from "./postgres";
import { sleep } from "./utils";

// Use these to replace games with multiple titles
const MERGE_GAMES: MergeGame[] = [
  // Children will be merged into parent
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
    children: ["THPS3 - PARTYMOD", "thps3"],
  },
  {
    parent: "Grand Theft Auto V",
    children: [
      "Grand Theft Auto V Enhanced",
      "GTA V Enhanced",
      "GTA V",
      "GTA V Enhanced Edition",
      "GTA V EE",
    ],
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

      this.logger.debug("RUNNING TASKS!");

      //await this.taskMergeGames();
      //await this.taskRemoveShortSessions();
      //await this.taskRemoveBadGames();

      await sleep(this.intervalSecs * 1000);
    }
  }

  async taskMergeGames() {
    this.logger.debug("Running taskReplaceGameIDs");
    for (const d of MERGE_GAMES) {
      const parentID = await this.postgres.fetchGameIDFromGameName(d.parent);
      if (!parentID) {
        this.logger.debug("Did not find parent ID for", d.parent);
        continue;
      }
      for (const c of d.children) {
        const childID = await this.postgres.fetchGameIDFromGameName(c);
        if (!childID) {
          this.logger.debug("Did not find child ID for", c);
          continue;
        }
        const sessions = await this.postgres.fetchSessionsByGameID(childID);
        for (const s of sessions) {
          await this.postgres.replaceActivityGameID(s.id, parentID);
        }
      }
    }
  }

  /*async taskRemoveShortSessions() {
    this.logger.debug("Running taskRemoveShortSessions");
    const sessions = await this.postgres.fetchSessions();
    for (const s of sessions) {
      if (s.seconds < 60) {
        await this.postgres.deleteActivity(s.id);
      }
    }
  }*/

  async taskRemoveBadGames() {
    this.logger.debug("Running taskRemoveBadGameSessions");
    for (const game of BAD_GAMES) {
      const gameID = await this.postgres.fetchGameIDFromGameName(game);
      if (!gameID) {
        //this.logger.warn("Did not find game ID for", game);
        continue;
      }
      const sessions = await this.postgres.fetchSessionsByGameID(gameID);
      for (const s of sessions) {
        await this.postgres.deleteActivity(s.id);
      }
    }
  }
}
