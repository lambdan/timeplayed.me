import type { GameWithStats } from "./api.models";
import { TimeplayedAPI } from "./api.client";

export type StatsFilters = {
  user?: number;
  platform?: number;
  after?: number;
  before?: number;
};

/**
 * How a combined game (it and its child games) is shown in a list of what was played,
 * with the list's filters:
 * - all of it from one child (like only the Switch 2 Edition): that child instead
 * - all of it from the game itself: the game, with nothing to expand
 * - otherwise the game, expandable into the parts that were played
 */
export async function playedFamilyRow(
  game: GameWithStats,
  filters: StatsFilters,
): Promise<{ game: GameWithStats; expandable: boolean }> {
  if (game.children_ids.length === 0) return { game, expandable: false };
  const [own, children] = await Promise.all([
    // the list endpoint, the single one says 404 when nothing matches the filters
    TimeplayedAPI.getGameStatsMany([game.id], filters),
    TimeplayedAPI.getGameStatsMany(game.children_ids, {
      ...filters,
      include_children: true,
    }),
  ]);
  const ownSeconds = own[0]?.stats.seconds ?? 0;
  const played = children.filter((c) => c.stats.seconds > 0);
  if (ownSeconds === 0 && played.length === 1) {
    return playedFamilyRow(played[0]!, filters);
  }
  return { game, expandable: played.length > 0 };
}
