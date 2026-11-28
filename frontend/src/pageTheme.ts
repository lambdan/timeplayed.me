// a page themed from a color (like a game's): Bootstrap's dark theme greys replaced by it

type RGB = [number, number, number];

// Bootstrap's dark --bs-body-bg, the page background without a theme
const DEFAULT_BG: RGB = [0x21, 0x25, 0x29];
// a light color is mixed into the default background this much, so the page stays dark
const TINT = 0.2;
// how much lighter than the page Bootstrap's dark theme makes these, kept the same
const CARD_LIGHTER = 0.04;
const TERTIARY_LIGHTER = 0.08;
const SECONDARY_LIGHTER = 0.12;
const BORDER_LIGHTER = 0.2;

function parse(hex: string): RGB {
  const h = hex.replace("#", "");
  return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)) as RGB;
}

function toHex(rgb: RGB): string {
  return (
    "#" + rgb.map((c) => Math.round(c).toString(16).padStart(2, "0")).join("")
  );
}

/** "33, 37, 41", for Bootstrap's -rgb variables */
function toRgbList(rgb: RGB): string {
  return rgb.map(Math.round).join(", ");
}

/** a moved toward b by amount (0 to 1) */
function mix(a: RGB, b: RGB, amount: number): RGB {
  return a.map((c, i) => c + (b[i] - c) * amount) as RGB;
}

function lighter(color: RGB, amount: number): RGB {
  return mix(color, [255, 255, 255], amount);
}

/** WCAG relative luminance, 0 (black) to 1 (white) */
function luminance(rgb: RGB): number {
  const [r, g, b] = rgb.map((c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * the CSS variables (and page background) for a page themed from the color. A color darker
 * than the default background is used as it is, a lighter one is a tint of it
 */
export function pageTheme(color: string): Record<string, string> {
  const rgb = parse(color);
  let page = rgb;
  if (luminance(rgb) > luminance(DEFAULT_BG)) {
    page = mix(DEFAULT_BG, rgb, TINT);
  }
  const card = lighter(page, CARD_LIGHTER);
  const tertiary = lighter(page, TERTIARY_LIGHTER);
  const secondary = lighter(page, SECONDARY_LIGHTER);
  return {
    "background-color": toHex(page),
    "--bs-body-bg": toHex(card),
    "--bs-body-bg-rgb": toRgbList(card),
    "--bs-tertiary-bg": toHex(tertiary),
    "--bs-tertiary-bg-rgb": toRgbList(tertiary),
    "--bs-secondary-bg": toHex(secondary),
    "--bs-secondary-bg-rgb": toRgbList(secondary),
    "--bs-border-color": toHex(lighter(page, BORDER_LIGHTER)),
  };
}

/** themes the whole page (the body), or back to the default with null */
export function setPageTheme(color: string | null) {
  const style = document.body.style;
  for (const property of Object.keys(pageTheme("#000000"))) {
    style.removeProperty(property);
  }
  if (!color) return;
  for (const [property, value] of Object.entries(pageTheme(color))) {
    style.setProperty(property, value);
  }
}
