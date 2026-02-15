import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/utils";
import { StatsCharts } from "../StatsCharts";
import type {
  DailyStatisticsResponse,
  MacroStatisticsResponse,
} from "@/api/model";

const mockDailyStats: DailyStatisticsResponse = {
  data: [
    {
      date: "2026-02-13",
      total_calories: 1800,
      total_protein: 120,
      total_fat: 60,
      total_carbs: 200,
      meal_count: 3,
      goal_calories: 2000,
      goal_achievement: 0.9,
    },
    {
      date: "2026-02-14",
      total_calories: 2100,
      total_protein: 130,
      total_fat: 70,
      total_carbs: 220,
      meal_count: 4,
      goal_calories: 2000,
      goal_achievement: 1.05,
    },
  ],
  period: {
    start_date: "2026-02-13",
    end_date: "2026-02-14",
    total_days: 2,
  },
  summary: {
    total_meals: 7,
    average_daily_calories: 1950,
    average_goal_achievement: 0.975,
  },
};

const mockMacroStats: MacroStatisticsResponse = {
  protein_percent: 30,
  fat_percent: 25,
  carbs_percent: 45,
  protein_grams: 125,
  fat_grams: 65,
  carbs_grams: 210,
  total_calories: 1950,
  period: {
    start_date: "2026-02-13",
    end_date: "2026-02-14",
    total_days: 2,
  },
};

describe("StatsCharts", () => {
  it("renders summary stats", () => {
    renderWithProviders(
      <StatsCharts dailyStats={mockDailyStats} macroStats={mockMacroStats} />,
    );
    expect(screen.getByText(/1950/)).toBeInTheDocument();
    expect(screen.getByText(/7/)).toBeInTheDocument();
  });

  it("renders empty state when no data", () => {
    const emptyDaily: DailyStatisticsResponse = {
      data: [],
      period: {
        start_date: "2026-02-13",
        end_date: "2026-02-14",
        total_days: 2,
      },
      summary: {
        total_meals: 0,
        average_daily_calories: 0,
        average_goal_achievement: null,
      },
    };
    renderWithProviders(
      <StatsCharts dailyStats={emptyDaily} macroStats={null} />,
    );
    expect(screen.getByText(/no data/i)).toBeInTheDocument();
  });
});
