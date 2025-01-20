export function formatSeconds(secs: number): string {
  if (secs > 7200) {
    return (secs / 3600).toFixed(1) + " hours";
  }
  if (secs > 120) {
    return Math.floor(secs / 60) + " mins";
  }
  if (secs > 60) {
    return "1 min";
  }
  return "<1 min";
}
