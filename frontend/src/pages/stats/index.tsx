import { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useGetDailyStatisticsApiV1StatisticsDailyGet } from "@/api/queries/statistics/statistics";
import { useGetMacroStatisticsApiV1StatisticsMacrosGet } from "@/api/queries/statistics/statistics";
import { StatsCharts } from "@/components/stats/StatsCharts";
import { PeriodSelector } from "@/components/stats/PeriodSelector";
import type { Period } from "@/components/stats/PeriodSelector";
import { Skeleton } from "@/components/ui/Skeleton";
import type {
  DailyStatisticsResponse,
  MacroStatisticsResponse,
} from "@/api/model";

function getDateRange(days: number) {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - days);
  return {
    start_date: start.toISOString().split("T")[0],
    end_date: end.toISOString().split("T")[0],
  };
}

/**
 * Extract the actual response body from an Orval hook result.
 * Orval types wrap the body in { data, status, headers } but at runtime
 * customFetch returns the raw JSON body directly.
 */
function unwrap<T>(response: unknown): T | undefined {
  if (!response) return undefined;
  const r = response as Record<string, unknown>;
  if ("data" in r && "status" in r) {
    return r.data as T;
  }
  return response as T;
}

export default function StatsPage() {
  const { t } = useTranslation();
  const [period, setPeriod] = useState<Period>(7);
  const dateRange = useMemo(() => getDateRange(period), [period]);

  const { data: dailyRaw, isLoading: loadingDaily } =
    useGetDailyStatisticsApiV1StatisticsDailyGet(dateRange);
  const { data: macroRaw, isLoading: loadingMacro } =
    useGetMacroStatisticsApiV1StatisticsMacrosGet(dateRange);

  const dailyStats = unwrap<DailyStatisticsResponse>(dailyRaw);
  const macroStats = unwrap<MacroStatisticsResponse>(macroRaw);

  const isLoading = loadingDaily || loadingMacro;

  return (
    <div className="flex flex-col gap-4 p-4">
      <h1 className="text-lg font-semibold text-tg-text">
        {t("statistics.title")}
      </h1>
      <PeriodSelector selected={period} onChange={setPeriod} />

      {isLoading ? (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      ) : dailyStats ? (
        <StatsCharts dailyStats={dailyStats} macroStats={macroStats ?? null} />
      ) : null}
    </div>
  );
}
