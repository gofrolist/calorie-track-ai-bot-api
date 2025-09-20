import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../services/api';

interface Meal {
  id: string;
  meal_date: string;
  meal_type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  kcal_total: number;
  source: string;
  estimate_id?: string;
  created_at: string;
}

interface MealsResponse {
  meals: Meal[];
  total_calories: number;
}

export const Today: React.FC = () => {
  const { t } = useTranslation();
  const [meals, setMeals] = useState<Meal[]>([]);
  const [totalCalories, setTotalCalories] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMeals = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await api.get<MealsResponse>('/api/v1/meals');
        setMeals(response.data.meals);
        setTotalCalories(response.data.total_calories);
      } catch (err) {
        setError('Failed to load meals');
        console.error('Error fetching meals:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchMeals();
  }, []);

  const formatCalories = (calories: number): string => {
    return calories.toLocaleString();
  };

  const getMealTypeLabel = (mealType: string): string => {
    return t(`today.mealTypes.${mealType}`);
  };

  if (loading) {
    return (
      <div style={{ padding: 16 }}>
        <h1>{t('today.title')}</h1>
        <p>{t('today.loading')}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 16 }}>
        <h1>{t('today.title')}</h1>
        <p>{t('today.error')}</p>
      </div>
    );
  }

  return (
    <div style={{ padding: 16 }}>
      <h1>{t('today.title')}</h1>

      <p>{t('today.total', { calories: formatCalories(totalCalories) })}</p>

      {meals.length === 0 ? (
        <p>{t('today.empty')}</p>
      ) : (
        <div>
          {meals.map((meal) => (
            <div
              key={meal.id}
              data-testid="meal-item"
              style={{
                marginBottom: 12,
                padding: 12,
                border: '1px solid #ccc',
                borderRadius: 8,
                cursor: 'pointer'
              }}
              onClick={() => {
                // TODO: Navigate to meal detail page
                console.log('Navigate to meal:', meal.id);
              }}
            >
              <div style={{ fontWeight: 'bold' }}>
                {getMealTypeLabel(meal.meal_type)}
              </div>
              <div>
                {formatCalories(meal.kcal_total)} kcal
              </div>
              <div style={{ fontSize: '0.8em', color: '#666' }}>
                {meal.source === 'estimate' ? 'From AI estimate' : 'Manual entry'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
