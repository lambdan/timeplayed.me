import { TimeplayedAPI } from "./api.client";

export async function fetchOrGetCachedGameName(
  gameId: number,
): Promise<string> {
  const storageKey = `game_name_${gameId}`;
  const cachedName = sessionStorage.getItem(storageKey);
  if (cachedName) {
    return cachedName;
  }
  const game = await TimeplayedAPI.getGame(gameId);
  const gameName = game.game.name;
  sessionStorage.setItem(storageKey, gameName);
  return gameName;
}
