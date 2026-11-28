import { watch } from "vue";
import { setPageColors, type ThemeColors } from "../pageTheme";

/**
 * themes the page in its own colors, null for none. Until they're known
 * (undefined) the last page's theme stays, so it changes once instead of flickering.
 * Pages using this need meta.ownColors in the router, the others are reset
 */
export function usePageColors(colors: () => ThemeColors | null | undefined) {
  watch(
    colors,
    (c) => {
      if (c !== undefined) setPageColors(c);
    },
    { immediate: true },
  );
}
