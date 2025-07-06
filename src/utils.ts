export function formatDate(date?: Date | number): string {
  if (!date) return "";
  if (typeof date === "number") {
    date = new Date(date);
  }
  return date.toLocaleString();
}

export function formatDuration(secs?: number): string {
  if (!secs) return "";
  // HH:MM:SS
  const hours = Math.floor(secs / 3600);
  const minutes = Math.floor((secs % 3600) / 60);
  const seconds = Math.floor(secs % 60);
  return `${hours.toString().padStart(2, "0")}:${minutes
    .toString()
    .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
}

export function timeAgo(other?: Date | number): string {
  if (!other) return "";

  if (typeof other === "number") {
    other = new Date(other);
  }

  const now = new Date();
  const seconds = Math.floor((now.getTime() - other.getTime()) / 1000);

  const intervals = [
    { label: "year", seconds: 31536000 },
    { label: "month", seconds: 2592000 },
    { label: "day", seconds: 86400 },
    { label: "hour", seconds: 3600 },
    { label: "minute", seconds: 60 },
    { label: "second", seconds: 1 },
  ];

  for (const i of intervals) {
    const count = Math.floor(seconds / i.seconds);
    if (count > 0) return `${count} ${i.label}${count !== 1 ? "s" : ""} ago`;
  }

  return "just now";
}

export function toUTCDate(s: string): Date {
  return new Date(s + "Z");
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
