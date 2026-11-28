// pages with colors of their own (games, platforms, users) themed from them:
// Bootstrap's dark theme greys replaced by the primary color, the charts in the secondary

import { computed, ref, watchEffect } from "vue";

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
// text needs this much contrast to be readable (WCAG AA)
const MIN_CONTRAST = 4.5;

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

/** the page background: a color darker than the default is used as it is, a lighter one is a tint */
function pageBackground(color: RGB): RGB {
  if (luminance(color) > luminance(DEFAULT_BG)) {
    return mix(DEFAULT_BG, color, TINT);
  }
  return color;
}

/** WCAG contrast ratio, 1 (none) to 21 (black on white) */
function contrast(a: RGB, b: RGB): number {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (light + 0.05) / (dark + 0.05);
}

/**
 * the accent color (for charts) on a page themed from primary: secondary,
 * if it can be read on the cards. Many are black or white text colors for tiles,
 * black can't be read on a dark page
 */
function pageAccent(primary: string, secondary: string | null): string | null {
  if (!secondary) return null;
  const card = lighter(pageBackground(parse(primary)), CARD_LIGHTER);
  if (contrast(parse(secondary), card) < MIN_CONTRAST) return null;
  return secondary;
}

/** the CSS variables (and page background) for a page themed from the color */
function pageTheme(primary: string): Record<string, string> {
  const page = pageBackground(parse(primary));
  const card = lighter(page, CARD_LIGHTER);
  const tertiary = lighter(page, TERTIARY_LIGHTER);
  const secondaryBg = lighter(page, SECONDARY_LIGHTER);
  return {
    "background-color": toHex(page),
    "--bs-body-bg": toHex(card),
    "--bs-body-bg-rgb": toRgbList(card),
    "--bs-tertiary-bg": toHex(tertiary),
    "--bs-tertiary-bg-rgb": toRgbList(tertiary),
    "--bs-secondary-bg": toHex(secondaryBg),
    "--bs-secondary-bg-rgb": toRgbList(secondaryBg),
    "--bs-border-color": toHex(lighter(page, BORDER_LIGHTER)),
  };
}

/** a primary and secondary color, as "#rrggbb", null for none */
export type ThemeColors = { primary: string | null; secondary: string | null };

// the page's own, null for the default
const pageColors = ref<ThemeColors | null>(null);

/** "#rrggbb" from an API color ("rrggbb" or null), null for none */
export function themeColor(color: string | null | undefined): string | null {
  return color ? "#" + color : null;
}

/** the page's own colors, null for the default */
export function setPageColors(colors: ThemeColors | null) {
  pageColors.value = colors;
}

/** the chart color, undefined for the default */
export const chartColor = computed(() => {
  const primary = pageColors.value?.primary;
  if (!primary) return undefined;
  return pageAccent(primary, pageColors.value?.secondary ?? null) ?? undefined;
});

// themes the whole page (the body)
watchEffect(() => {
  const style = document.body.style;
  for (const property of Object.keys(pageTheme("#000000"))) {
    style.removeProperty(property);
  }
  const primary = pageColors.value?.primary;
  if (!primary) return;
  for (const [property, value] of Object.entries(pageTheme(primary))) {
    style.setProperty(property, value);
  }
});
