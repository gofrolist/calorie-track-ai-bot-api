import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useGetDailyStatisticsApiV1StatisticsDailyGet } from "@/api/queries/statistics/statistics";
import { useGetMacroStatisticsApiV1StatisticsMacrosGet } from "@/api/queries/statistics/statistics";
import { StatsCharts } from "@/components/stats/StatsCharts";
import { PeriodSelector } from "@/components/stats/PeriodSelector";
import type { Period } from "@/components/stats/PeriodSelector";
import { Skeleton } from "@/components/ui/Skeleton";
import { unwrap } from "@/api/unwrap";
import { getDateRange } from "@/utils/date";
import type {
  DailyStatisticsResponse,
  MacroStatisticsResponse,
} from "@/api/model";

export default function StatsPage() {
  const { t } = useTranslation();
  const [period, setPeriod] = useState<Period>(7);
  // Recomputed every render so a page left open past midnight picks up the
  // new "today"; query keys are hashed by value, so this does not refetch.
  const dateRange = getDateRange(period);

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
