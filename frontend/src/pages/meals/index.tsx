import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import {
  useGetMealsApiV1MealsGet,
  useUpdateMealApiV1MealsMealIdPatch,
  useDeleteMealApiV1MealsMealIdDelete,
} from "@/api/queries/meals/meals";
import { useGetDailySummaryApiV1DailySummaryDateGet } from "@/api/queries/daily-summary/daily-summary";
import { useGetGoalApiV1GoalsGet } from "@/api/queries/goals/goals";
import { MealCard } from "@/components/meal/MealCard";
import { MealEditor } from "@/components/meal/MealEditor";
import type { MealFormData } from "@/components/meal/MealEditor";
import { Modal } from "@/components/ui/Modal";
import { Skeleton } from "@/components/ui/Skeleton";
import type { MealWithPhotos } from "@/api/model";
import type { MealsListResponse } from "@/api/model";
import type { DailySummary } from "@/api/model";
import type { GoalResponse } from "@/api/model";

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

export default function MealsPage() {
  const { t } = useTranslation();
  const [selectedDate] = useState(formatDate(new Date()));
  const [editingMeal, setEditingMeal] = useState<MealWithPhotos | null>(null);

  const { data: mealsRaw, isLoading } = useGetMealsApiV1MealsGet({
    date: selectedDate,
  });
  const { data: summaryRaw } =
    useGetDailySummaryApiV1DailySummaryDateGet(selectedDate);
  const { data: goalRaw } = useGetGoalApiV1GoalsGet();
  const updateMeal = useUpdateMealApiV1MealsMealIdPatch();
  const deleteMeal = useDeleteMealApiV1MealsMealIdDelete();

  const mealsData = unwrap<MealsListResponse>(mealsRaw);
  const summary = unwrap<DailySummary>(summaryRaw);
  const goal = unwrap<GoalResponse>(goalRaw);

  const handleEdit = useCallback(
    (id: string) => {
      const meal = mealsData?.meals.find((m) => m.id === id);
      if (meal) setEditingMeal(meal);
    },
    [mealsData],
  );

  const handleDelete = useCallback(
    (id: string) => {
      if (window.confirm(t("meals.confirmDelete"))) {
        deleteMeal.mutate({ mealId: id });
      }
    },
    [deleteMeal, t],
  );

  const handleSave = useCallback(
    (data: MealFormData) => {
      if (!editingMeal) return;
      updateMeal.mutate(
        {
          mealId: editingMeal.id,
          data: {
            description: data.description,
            protein_grams: data.protein,
            carbs_grams: data.carbs,
            fats_grams: data.fats,
          },
        },
        { onSuccess: () => setEditingMeal(null) },
      );
    },
    [editingMeal, updateMeal],
  );

  return (
    <div className="flex flex-col gap-4 p-4">
      <h1 className="text-lg font-semibold text-tg-text">{t("meals.title")}</h1>

      {/* Daily summary */}
      {summary && (
        <div className="flex items-center justify-between rounded-xl bg-tg-secondary-bg p-4">
          <div>
            <p className="text-2xl font-bold text-tg-text">
              {summary.kcal_total} kcal
            </p>
            {goal && (
              <p className="text-sm text-tg-hint">
                {t("meals.summary.goal", {
                  target: goal.daily_kcal_target,
                })}
              </p>
            )}
          </div>
          <div className="flex gap-4 text-xs text-tg-hint">
            <span>
              {t("today.macros.protein")}: {summary.macros_totals.protein_g}g
            </span>
            <span>
              {t("today.macros.fat")}: {summary.macros_totals.fat_g}g
            </span>
            <span>
              {t("today.macros.carbs")}: {summary.macros_totals.carbs_g}g
            </span>
          </div>
        </div>
      )}

      {/* Meal list */}
      {isLoading ? (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : mealsData?.meals.length ? (
        <div className="flex flex-col gap-3">
          {mealsData.meals.map((meal) => (
            <MealCard
              key={meal.id}
              meal={meal}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      ) : (
        <p className="py-8 text-center text-sm text-tg-hint">
          {t("meals.list.empty")}
        </p>
      )}

      {/* Edit modal */}
      <Modal
        open={!!editingMeal}
        onClose={() => setEditingMeal(null)}
        title={t("mealDetail.edit")}
      >
        {editingMeal && (
          <MealEditor
            meal={{
              description: editingMeal.description ?? "",
              calories: editingMeal.calories,
              protein: editingMeal.macronutrients.protein,
              carbs: editingMeal.macronutrients.carbs,
              fats: editingMeal.macronutrients.fats,
            }}
            onSave={handleSave}
            onCancel={() => setEditingMeal(null)}
            saving={updateMeal.isPending}
          />
        )}
      </Modal>
    </div>
  );
}
