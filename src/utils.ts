/** Format seconds into hours or minutes, or days if daysAfter > 0 */
export function formatSeconds(secs: number, daysAfter = 0): string {
  if (daysAfter > 0 && secs > 86400 * daysAfter) {
    const days = Math.floor(secs / 86400);
    return days + ` ${days === 1 ? "day" : "days"}`;
  }

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

export function timeSince(old_date: Date): string {
  const deltaSecs = (Date.now() - old_date.getTime()) / 1000;

  if (deltaSecs > 172800) {
    return Math.floor(deltaSecs / 86400) + " days ago";
  }

  if (deltaSecs > 7200) {
    return Math.floor(deltaSecs / 3600) + " hours ago";
  }

  if (deltaSecs > 120) {
    return Math.floor(deltaSecs / 60) + " mins ago";
  }

  return "just now";
}

export function clamp(x: number, min: number, max: number) {
  if (x > max) {
    return max;
  }
  if (x < min) {
    return min;
  }
  return x;
}

export function colorFromString(s: string): string {
  const colorKeywords: Record<string, number> = {
    red: 0,
    blue: 220,
    green: 120,
    yellow: 50,
    orange: 30,
    purple: 280,
    pink: 320,
    cyan: 180,
    brown: 20,
    grand: 120,
  };

  // Convert string to lowercase to match keywords
  const lowerStr = s.toLowerCase();
  for (const [keyword, hue] of Object.entries(colorKeywords)) {
    if (lowerStr.includes(keyword)) {
      return `hsl(${hue}, 70%, 50%)`; // Prioritize color keyword if found
    }
  }

  // If no color keyword is found, generate a unique color based on hash
  let hash = 0;
  for (let i = 0; i < s.length; i++) {
    hash = s.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = ((hash % 360) + 360) % 360; // Keep hue within 0-360
  return `hsl(${hue}, 60%, 65%)`;
}
