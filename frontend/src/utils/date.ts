export function formatDate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/**
 * Date range covering the last `days` days including today, for the
 * statistics API, which treats `end_date` as exclusive.
 */
export function getDateRange(days: number, now: Date = new Date()) {
  const end = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
  const start = new Date(
    end.getFullYear(),
    end.getMonth(),
    end.getDate() - days,
  );
  return {
    start_date: formatDate(start),
    end_date: formatDate(end),
  };
}
