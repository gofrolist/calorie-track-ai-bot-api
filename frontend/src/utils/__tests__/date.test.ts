import { describe, it, expect } from "vitest";
import { getDateRange } from "../date";

describe("getDateRange", () => {
  // The statistics API treats end_date as exclusive.
  it("includes today by ending the range tomorrow", () => {
    const now = new Date(2026, 9, 11, 15, 30);
    expect(getDateRange(7, now)).toEqual({
      start_date: "2026-10-05",
      end_date: "2026-10-12",
    });
  });

  it("covers exactly the requested number of days", () => {
    const now = new Date(2026, 9, 11);
    const { start_date, end_date } = getDateRange(30, now);
    const days =
      (new Date(end_date).getTime() - new Date(start_date).getTime()) /
      86_400_000;
    expect(days).toBe(30);
  });

  it("handles month and year boundaries", () => {
    expect(getDateRange(7, new Date(2026, 11, 31))).toEqual({
      start_date: "2026-12-25",
      end_date: "2027-01-01",
    });
  });
});
