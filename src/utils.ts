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

export function timeSince(
  old_date: Date,
  return_date_after = 86400 * 30
): string {
  const deltaSecs = (Date.now() - old_date.getTime()) / 1000;

  if (return_date_after > 0 && deltaSecs > return_date_after) {
    return old_date.toUTCString();
  }

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
