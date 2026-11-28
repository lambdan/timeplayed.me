// a user's colors for tiles. undefined for the default tiles

type Colored = {
  color_primary: string | null;
  color_secondary: string | null;
};

export function tileBackground(item: Colored): string | undefined {
  if (item.color_primary) {
    return "#" + item.color_primary;
  }
  return undefined;
}

export function tileTextColor(item: Colored): string | undefined {
  if (item.color_secondary) {
    return "#" + item.color_secondary;
  }
  if (item.color_primary) {
    return "#ffffff"; // text-white, like platforms
  }
  return undefined;
}
