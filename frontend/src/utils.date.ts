// TODO: Tests :D

/** Returns start of year (00:00:00) for given date (eg March 15, 2026 returns Jan 1, 2026 00:00:00) */
export function startOfYear(d: Date): Date {
  return new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
}

/** Returns end of year (23:59:59) for given date (eg March 15, 2026 returns Dec 31, 2026 23:59:59) */
export function endOfYear(d: Date): Date {
  return new Date(Date.UTC(d.getUTCFullYear(), 11, 31, 23, 59, 59, 999));
}

/** Returns start of month (00:00:00) for given date (eg March 15, returns March 1, 00:00:00) */
export function startOfMonth(d: Date): Date {
  return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1));
}

/** Returns end of month (23:59:59) for given date (eg March 15, returns March 31, 23:59:59) */
export function endOfMonth(d: Date): Date {
  return new Date(
    Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 1, 0, 23, 59, 59, 999),
  );
}

/** Returns monday 00:00:00 for given date. Eg March 15 2026 returns March 9 2026 00:00:00. */
export function startOfWeek(d: Date): Date {
  const day = d.getUTCDay();
  const diff = (day + 6) % 7; // convert Sunday=0 to Sunday=7
  const result = new Date(d);
  result.setUTCDate(d.getUTCDate() - diff);
  result.setUTCHours(0, 0, 0, 0);
  return result;
}

/** Returns sunday 23:59:59 for given date Eg March 16 2026 returns March 22 2026 23:59:59. */
export function endOfWeek(d: Date): Date {
  const day = d.getUTCDay();
  const diff = (7 - day) % 7; // convert Sunday=0 to Sunday=7
  const result = new Date(d);
  result.setUTCDate(d.getUTCDate() + diff);
  result.setUTCHours(23, 59, 59, 999);
  return result;
}

export function currentYear(): number {
  return new Date().getUTCFullYear();
}

export function currentMonth(): number {
  return new Date().getUTCMonth();
}
