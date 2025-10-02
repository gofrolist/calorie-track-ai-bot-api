/**
 * Meals Page (formerly Today)
 * Feature: 003-update-logic-for
 * Task: T051
 *
 * Calendar-based meal history with:
 * - Date picker for 1-year history
 * - Expandable meal cards
 * - Multi-photo carousel
 * - Meal editing and deletion
 */

import React, { useState, useContext, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import {
  goalsApi,
  type Goal,
  type DailySummary
} from '../services/api';
import { TelegramWebAppContext } from '../app';
import Share from '../components/share';
import { Skeleton } from '../components/Loading';
import { MealCard } from '../components/MealCard';
import { CalendarPicker } from '../components/CalendarPicker';
import { MealEditor } from '../components/MealEditor';
import { Navigation } from '../components/Navigation';
import { useMeals, useMealsCalendar, type Meal } from '../hooks/useMeals';

export const Meals: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const telegramContext = useContext(TelegramWebAppContext);

  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [showCalendar, setShowCalendar] = useState(false);
  const [expandedMealId, setExpandedMealId] = useState<string | null>(null);
  const [editingMeal, setEditingMeal] = useState<Meal | null>(null);
  const [goal, setGoal] = useState<Goal | null>(null);

  // Fetch meals for selected date
  const { meals, loading, error, updateMeal, deleteMeal, refetch } = useMeals(selectedDate);

  // Fetch calendar data for last month - memoize dates to prevent infinite loop
  const calendarDates = useMemo(() => {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setMonth(startDate.getMonth() - 1);
    return { startDate, endDate };
  }, []);
  const { calendarData } = useMealsCalendar(calendarDates.startDate, calendarDates.endDate);

  // Fetch goal on mount
  React.useEffect(() => {
    const fetchGoal = async () => {
      try {
        const fetchedGoal = await goalsApi.getGoal();
        setGoal(fetchedGoal);
      } catch (err) {
        console.error('Failed to fetch goal:', err);
      }
    };
    fetchGoal();
  }, []);

  const formatCalories = (calories: number): string => {
    return calories.toLocaleString();
  };

  const formatMacro = (grams: number | undefined): string => {
    return grams ? `${Math.round(grams)}g` : '0g';
  };

  const handleToggleExpand = (mealId: string) => {
    setExpandedMealId(expandedMealId === mealId ? null : mealId);
  };

  const handleEdit = (meal: Meal) => {
    setEditingMeal(meal);
  };

  const handleDelete = async (mealId: string) => {
    if (window.confirm(t('meals.confirmDelete') || 'Are you sure you want to delete this meal?')) {
      try {
        await deleteMeal(mealId);
        setExpandedMealId(null);
      } catch (err) {
        console.error('Failed to delete meal:', err);
        if (window.Telegram?.WebApp?.showAlert) {
          window.Telegram.WebApp.showAlert('Failed to delete meal');
        }
      }
    }
  };

  const handleSaveEdit = async (updates: any) => {
    if (!editingMeal) return;
    try {
      await updateMeal(editingMeal.id, updates);
      setEditingMeal(null);
    } catch (err) {
      console.error('Failed to update meal:', err);
      throw err;
    }
  };

  const handleDateChange = (date: Date) => {
    setSelectedDate(date);
    setShowCalendar(false);
    setExpandedMealId(null);
  };

  // Calculate daily summary from meals
  const dailySummary: DailySummary = React.useMemo(() => {
    const totalCalories = meals.reduce((sum, meal) => sum + meal.calories, 0);
    const totalProtein = meals.reduce((sum, meal) => sum + meal.macronutrients.protein, 0);
    const totalFats = meals.reduce((sum, meal) => sum + meal.macronutrients.fats, 0);
    const totalCarbs = meals.reduce((sum, meal) => sum + meal.macronutrients.carbs, 0);

    return {
      user_id: telegramContext.user?.id || '',
      date: selectedDate.toISOString().split('T')[0],
      kcal_total: totalCalories,
      macros_totals: {
        protein_g: totalProtein,
        fat_g: totalFats,
        carbs_g: totalCarbs,
      },
    };
  }, [meals, telegramContext.user?.id, selectedDate]);

  const getProgressPercentage = (): number => {
    if (!goal) return 0;
    return Math.round((dailySummary.kcal_total / goal.daily_kcal_target) * 100);
  };

  const getRemainingCalories = (): number => {
    if (!goal) return 0;
    return Math.max(0, goal.daily_kcal_target - dailySummary.kcal_total);
  };

  // Get dates with meals for calendar
  const datesWithMeals = React.useMemo(() => {
    return calendarData.map(day => new Date(day.meal_date));
  }, [calendarData]);

  const isToday = selectedDate.toDateString() === new Date().toDateString();

  if (loading && meals.length === 0) {
    return (
      <div className="main-content" style={{ padding: 16 }}>
        <header style={{ marginBottom: 24 }}>
          <h1>{t('meals.title') || 'Meals'}</h1>
        </header>

        {/* Loading Summary */}
        <div className="tg-card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <Skeleton width="40%" height="24px" />
            <Skeleton width="60px" height="32px" style={{ borderRadius: '8px' }} />
          </div>
          <Skeleton width="100%" height="80px" />
        </div>

        {/* Loading Meals */}
          <div>
            {[1, 2, 3].map((i) => (
            <div key={i} className="tg-card" style={{ marginBottom: 12 }}>
              <Skeleton width="100%" height="80px" />
              </div>
            ))}
        </div>

        <Navigation />
      </div>
    );
  }

  if (error) {
    return (
      <div className="main-content" style={{ padding: 16 }}>
        <h1>{t('meals.title') || 'Meals'}</h1>
        <div className="error">{error}</div>
        <button
          className="tg-button"
          onClick={() => refetch(selectedDate)}
          style={{ marginTop: 16 }}
        >
          {t('common.retry')}
        </button>
      </div>
    );
  }

  return (
    <div className="main-content" style={{ padding: 16 }}>
      <div style={{ maxWidth: 900, margin: '0 auto' }}>
        <header style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h1>{t('meals.title') || 'Meals'}</h1>
          <button
            className="tg-button-secondary calendar-icon"
            onClick={() => setShowCalendar(!showCalendar)}
            style={{ fontSize: '1.2em', padding: '8px 16px' }}
          >
            📅
          </button>
        </div>
        <div className="date-header" style={{ color: 'var(--tg-hint-color)', fontSize: '0.9em', marginTop: 8 }}>
          {selectedDate.toLocaleDateString(telegramContext.user?.language || 'en', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
          {!isToday && (
            <button
              className="tg-button-secondary"
              onClick={() => handleDateChange(new Date())}
              style={{ marginLeft: 12, fontSize: '0.9em', padding: '4px 12px' }}
            >
              {t('meals.backToToday') || 'Back to Today'}
            </button>
          )}
        </div>
      </header>

      {/* Calendar Picker */}
      {showCalendar && (
        <div className="calendar-picker" style={{ marginBottom: 24 }}>
          <CalendarPicker
            selectedDate={selectedDate}
            onDateChange={handleDateChange}
            datesWithMeals={datesWithMeals}
          />
        </div>
      )}

      {/* Daily Summary Card */}
      <div className="tg-card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ margin: 0 }}>{t('meals.summary.title') || 'Daily Summary'}</h2>
          <Share
            shareData={{
              calories: dailySummary?.kcal_total,
              meals: meals.length,
              goal: goal?.daily_kcal_target,
              date: selectedDate.toLocaleDateString()
            }}
            style={{ fontSize: '12px', padding: '6px 12px' }}
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: '1.5em', fontWeight: 'bold' }}>
              {formatCalories(dailySummary?.kcal_total || 0)} kcal
            </div>
            {goal && (
              <div style={{ color: 'var(--tg-hint-color)', fontSize: '0.9em' }}>
                {t('meals.summary.goal', { target: formatCalories(goal.daily_kcal_target) }) ||
                  `Goal: ${formatCalories(goal.daily_kcal_target)} kcal`}
              </div>
            )}
          </div>

          {goal && (
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '1.2em', fontWeight: 'bold' }}>
                {getProgressPercentage()}%
              </div>
              <div style={{ color: 'var(--tg-hint-color)', fontSize: '0.9em' }}>
                {getRemainingCalories()} kcal {t('meals.summary.remaining') || 'left'}
              </div>
            </div>
          )}
        </div>

        {goal && (
          <div className="progress-bar">
            <div
              className="progress-bar-fill"
              style={{ width: `${Math.min(getProgressPercentage(), 100)}%` }}
            />
          </div>
        )}

        {/* Macros */}
        {dailySummary?.macros_totals && (
          <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: 16, fontSize: '0.9em' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontWeight: 'bold' }}>{formatMacro(dailySummary.macros_totals.protein_g)}</div>
              <div style={{ color: 'var(--tg-hint-color)' }}>{t('meals.macros.protein') || 'Protein'}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontWeight: 'bold' }}>{formatMacro(dailySummary.macros_totals.fat_g)}</div>
              <div style={{ color: 'var(--tg-hint-color)' }}>{t('meals.macros.fat') || 'Fat'}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontWeight: 'bold' }}>{formatMacro(dailySummary.macros_totals.carbs_g)}</div>
              <div style={{ color: 'var(--tg-hint-color)' }}>{t('meals.macros.carbs') || 'Carbs'}</div>
            </div>
          </div>
        )}
      </div>

      {/* Meals List */}
      <div style={{ marginBottom: 80 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ margin: 0 }}>
            {t('meals.list.title') || 'Meals'} ({meals.length})
          </h2>
        </div>

        {meals.length === 0 ? (
          <div className="tg-card" style={{ textAlign: 'center', padding: 32 }}>
            <div style={{ fontSize: '2em', marginBottom: 16 }}>🍽️</div>
            <div style={{ color: 'var(--tg-hint-color)' }}>
              {t('meals.list.empty') || 'No meals logged for this date'}
            </div>
            {isToday && (
              <div style={{ marginTop: 16, fontSize: '0.9em', color: 'var(--tg-hint-color)' }}>
                {t('meals.list.sendPhotoHint') || 'Send a photo to the bot to log a meal'}
              </div>
            )}
          </div>
        ) : (
          <div>
            {meals.map((meal) => (
              <MealCard
                key={meal.id}
                meal={meal}
                isExpanded={expandedMealId === meal.id}
                onToggleExpand={() => handleToggleExpand(meal.id)}
                onEdit={() => handleEdit(meal)}
                onDelete={() => handleDelete(meal.id)}
                className="meal-card-item"
              />
            ))}
          </div>
        )}
      </div>

      {/* Meal Editor Modal */}
      {editingMeal && (
        <MealEditor
          meal={editingMeal}
          isOpen={true}
          onClose={() => setEditingMeal(null)}
          onSave={handleSaveEdit}
        />
      )}

      </div>

      <Navigation />
    </div>
  );
};

export default Meals;
