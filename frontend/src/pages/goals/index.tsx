import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  useGetGoalApiV1GoalsGet,
  useUpdateGoalApiV1GoalsPatch,
  useCreateGoalApiV1GoalsPost,
} from "@/api/queries/goals/goals";
import { useGetDailySummaryApiV1DailySummaryDateGet } from "@/api/queries/daily-summary/daily-summary";
import { Modal } from "@/components/ui/Modal";
import { Skeleton } from "@/components/ui/Skeleton";
import type { GoalResponse, DailySummary } from "@/api/model";

function formatDate(d: Date): string {
  return d.toISOString().split("T")[0];
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

export default function GoalsPage() {
  const { t } = useTranslation();
  const [editing, setEditing] = useState(false);
  const [goalInput, setGoalInput] = useState("");
  const [error, setError] = useState("");

  const { data: goalRaw, isLoading: loadingGoal } = useGetGoalApiV1GoalsGet();
  const { data: summaryRaw } = useGetDailySummaryApiV1DailySummaryDateGet(
    formatDate(new Date()),
  );
  const updateGoal = useUpdateGoalApiV1GoalsPatch();
  const createGoal = useCreateGoalApiV1GoalsPost();

  const goal = unwrap<GoalResponse>(goalRaw);
  const summary = unwrap<DailySummary>(summaryRaw);

  const handleEdit = useCallback(() => {
    setGoalInput(goal?.daily_kcal_target?.toString() ?? "2000");
    setError("");
    setEditing(true);
  }, [goal]);

  const handleSave = useCallback(() => {
    const value = parseInt(goalInput, 10);
    if (isNaN(value) || value < 500 || value > 10000) {
      setError(t("goals.validation.range"));
      return;
    }
    const mutation = goal ? updateGoal : createGoal;
    mutation.mutate(
      { data: { daily_kcal_target: value } },
      { onSuccess: () => setEditing(false) },
    );
  }, [goalInput, goal, updateGoal, createGoal, t]);

  const consumed = summary?.kcal_total ?? 0;
  const target = goal?.daily_kcal_target ?? 0;
  const remaining = target - consumed;
  const progress = target > 0 ? Math.min((consumed / target) * 100, 100) : 0;

  return (
    <div className="flex flex-col gap-4 p-4">
      <h1 className="text-lg font-semibold text-tg-text">{t("goals.title")}</h1>

      {loadingGoal ? (
        <Skeleton className="h-32 w-full" />
      ) : (
        <>
          {/* Goal display */}
          <div className="rounded-xl bg-tg-secondary-bg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-tg-hint">
                  {t("goals.dailyCalorieGoal")}
                </p>
                <p className="text-3xl font-bold text-tg-text">{target} kcal</p>
              </div>
              <button
                type="button"
                aria-label={t("goals.editGoal")}
                onClick={handleEdit}
                className="rounded-lg bg-tg-button px-4 py-2 text-sm font-medium text-tg-button-text"
              >
                {t("goals.editGoal")}
              </button>
            </div>
          </div>

          {/* Progress */}
          {target > 0 && (
            <div className="rounded-xl bg-tg-secondary-bg p-4">
              <p className="mb-2 text-sm font-medium text-tg-text">
                {t("goals.todayProgress")}
              </p>
              <div className="h-3 overflow-hidden rounded-full bg-tg-bg">
                <div
                  className="h-full rounded-full bg-tg-button transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="mt-2 flex justify-between text-xs text-tg-hint">
                <span>{consumed} kcal</span>
                <span>
                  {remaining > 0
                    ? `${remaining} ${t("goals.remaining")}`
                    : remaining === 0
                      ? t("goals.goalAchieved")
                      : `${Math.abs(remaining)} ${t("goals.overGoal")}`}
                </span>
              </div>
            </div>
          )}

          {/* Tips */}
          <div className="rounded-xl bg-tg-secondary-bg p-4">
            <p className="mb-2 text-sm font-medium text-tg-text">
              {t("goals.tips")}
            </p>
            <div className="flex flex-col gap-1 text-xs text-tg-hint">
              <p>{t("goals.tip1")}</p>
              <p>{t("goals.tip2")}</p>
              <p>{t("goals.tip3")}</p>
            </div>
          </div>
        </>
      )}

      {/* Edit modal */}
      <Modal
        open={editing}
        onClose={() => setEditing(false)}
        title={t("goals.setDailyGoal")}
      >
        <div className="flex flex-col gap-4">
          <label className="flex flex-col gap-1">
            <span className="text-sm text-tg-hint">
              {t("goals.dailyTarget")}
            </span>
            <input
              type="number"
              min={500}
              max={10000}
              value={goalInput}
              onChange={(e) => {
                setGoalInput(e.target.value);
                setError("");
              }}
              className="rounded-lg border border-tg-hint/30 bg-tg-secondary-bg px-3 py-2 text-tg-text"
            />
          </label>
          {error && <p className="text-sm text-red-500">{error}</p>}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setEditing(false)}
              className="flex-1 rounded-lg border border-tg-hint/30 py-2 text-sm text-tg-text"
            >
              {t("goals.cancel")}
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={updateGoal.isPending || createGoal.isPending}
              className="flex-1 rounded-lg bg-tg-button py-2 text-sm font-medium text-tg-button-text disabled:opacity-50"
            >
              {updateGoal.isPending || createGoal.isPending
                ? t("goals.saving")
                : t("goals.save")}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
