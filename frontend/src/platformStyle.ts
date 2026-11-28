import type { Platform } from "./api.models";

// the platform's own colors and icon, with the defaults for ones that have none

export function platformBackground(platform: Platform): string {
  if (platform.color_primary) {
    return "#" + platform.color_primary;
  }
  return "#6c757d"; // bg-secondary
}

export function platformTextColor(platform: Platform): string {
  if (platform.color_secondary) {
    return "#" + platform.color_secondary;
  }
  return "#ffffff"; // text-white
}

export function platformIcon(platform: Platform): string {
  if (platform.icon) {
    return "bi-" + platform.icon;
  }
  return "bi-controller";
}
