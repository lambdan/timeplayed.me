// picking colors for a game's tiles from its cover, in the browser

export type TileColors = { primary: string; secondary: string };

// node-vibrant's swatches, the order they're tried in
const SWATCHES = [
  "Vibrant",
  "DarkVibrant",
  "Muted",
  "DarkMuted",
  "LightVibrant",
  "LightMuted",
] as const;

/** black or white, whichever is easier to read on the background (WCAG contrast) */
function readableTextColor(background: string): string {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(background.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  const onWhite = 1.05 / (luminance + 0.05);
  const onBlack = (luminance + 0.05) / 0.05;
  return onWhite > onBlack ? "#ffffff" : "#000000";
}

/** background and text colors from the image, best first. Empty if it can't be read */
export async function pickColors(url: string): Promise<TileColors[]> {
  // only admins use this, so it's loaded when it's needed instead of with the site
  const { Vibrant } = await import("node-vibrant/browser");
  const palette = await Vibrant.from(url).getPalette();
  const colors: TileColors[] = [];
  for (const name of SWATCHES) {
    const swatch = palette[name];
    if (!swatch) continue;
    colors.push({
      primary: swatch.hex,
      secondary: readableTextColor(swatch.hex),
    });
  }
  return colors;
}
