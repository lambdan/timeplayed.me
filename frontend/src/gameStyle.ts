import type { Game } from "./api.models";

// the game's colors (its own or its parent's) for tiles. undefined for the default tiles

export function gameBackground(game: Game): string | undefined {
  if (game.color_primary) {
    return "#" + game.color_primary;
  }
  return undefined;
}

export function gameTextColor(game: Game): string | undefined {
  if (game.color_secondary) {
    return "#" + game.color_secondary;
  }
  if (game.color_primary) {
    return "#ffffff"; // text-white, like platforms
  }
  return undefined;
}
