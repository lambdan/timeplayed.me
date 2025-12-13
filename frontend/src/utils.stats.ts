import type { Activity, Game } from "./models/models";
import type { RecapGameEntry, RecapPlatformEntry } from "./models/stats.models";
import { getGameCoverUrl } from "./utils";

export function totalPlaytime(activities: Activity[]): number {
  return activities.reduce((sum, activity) => sum + activity.seconds, 0);
}

export function uniqueGamesCount(activities: Activity[]): number {
  const gameIds = new Set<number>();
  for (const activity of activities) {
    gameIds.add(activity.game.id);
  }
  return gameIds.size;
}

export async function buildGamesList(
  activities: Activity[],
): Promise<RecapGameEntry[]> {
  const gamesMap = new Map<string, RecapGameEntry>();
  const sum_seconds = totalPlaytime(activities);

  for (const activity of activities) {
    const gameId = activity.game.id;
    if (!gamesMap.has(gameId.toString())) {
      gamesMap.set(gameId.toString(), {
        id: gameId,
        name: activity.game.name,
        seconds: 0,
        first_played: new Date(activity.timestamp),
        last_played: new Date(activity.timestamp),
        percentage: 0,
        activity_count: 0,
        average_session_seconds: 0,
      });
    }
    const entry = gamesMap.get(gameId.toString());
    if (entry) {
      entry.seconds += activity.seconds;
      const activityDate = new Date(activity.timestamp);
      if (activityDate < entry.first_played) {
        entry.first_played = activityDate;
      }
      if (activityDate > entry.last_played) {
        entry.last_played = activityDate;
      }
      entry.percentage = (entry.seconds / sum_seconds) * 100;
      entry.activity_count += 1;
      entry.average_session_seconds = entry.seconds / entry.activity_count;
    }
  }
  const arr = Array.from(gamesMap.values());
  arr.sort((a, b) => b.seconds - a.seconds); // descending order, most played first
  return arr;
}

export async function buildPlatformsList(
  activities: Activity[],
): Promise<RecapPlatformEntry[]> {
  const platformsMap = new Map<number, RecapPlatformEntry>();
  const sum_seconds = totalPlaytime(activities);
  const gamePlaytimeByPlatform = new Map<number, Map<number, number>>(); // platformId -> (gameId -> seconds)

  for (const activity of activities) {
    const platformId = activity.platform.id;
    if (!platformsMap.has(platformId)) {
      platformsMap.set(platformId, {
        id: platformId,
        name: activity.platform.name || activity.platform.abbreviation,
        seconds: 0,
        percentage: 0,
        activity_count: 0,
        average_session_seconds: 0,
        most_played_game: "",
      });
      gamePlaytimeByPlatform.set(platformId, new Map<number, number>());
    }
    const entry = platformsMap.get(platformId);
    const gamePlaytimeMap = gamePlaytimeByPlatform.get(platformId);
    if (entry && gamePlaytimeMap) {
      entry.seconds += activity.seconds;
      entry.activity_count += 1;
      entry.percentage = (entry.seconds / sum_seconds) * 100;
      entry.average_session_seconds = entry.seconds / entry.activity_count;

      // Track playtime per game for this platform
      const currentGameSeconds = gamePlaytimeMap.get(activity.game.id) || 0;
      gamePlaytimeMap.set(
        activity.game.id,
        currentGameSeconds + activity.seconds,
      );
    }
  }

  // Determine most played game for each platform
  for (const [
    platformId,
    gamePlaytimeMap,
  ] of gamePlaytimeByPlatform.entries()) {
    const entry = platformsMap.get(platformId);
    if (entry) {
      let mostPlayedGameId: number | null = null;
      let maxSeconds = 0;
      for (const [gameId, seconds] of gamePlaytimeMap.entries()) {
        if (seconds > maxSeconds) {
          maxSeconds = seconds;
          mostPlayedGameId = gameId;
        }
      }
      if (mostPlayedGameId !== null) {
        const mostPlayedGame = activities.find(
          (act) => act.game.id === mostPlayedGameId,
        )?.game;
        entry.most_played_game = mostPlayedGame ? mostPlayedGame.name : "";
      }
    }
  }

  const arr = Array.from(platformsMap.values());
  arr.sort((a, b) => b.seconds - a.seconds); // descending order, most played first
  return arr;
}
