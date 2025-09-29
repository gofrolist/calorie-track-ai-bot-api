import React, { useState, useEffect, useContext } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import {
  mealsApi,
  dailySummaryApi,
  goalsApi,
  apiUtils,
  type Meal,
  type DailySummary,
  type Goal
} from '../services/api';
import { TelegramWebAppContext } from '../app';
import Share from '../components/share';
import { Loading, Skeleton } from '../components/Loading';

export const Today: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const telegramContext = useContext(TelegramWebAppContext);

  const [meals, setMeals] = useState<Meal[]>([]);
  const [dailySummary, setDailySummary] = useState<DailySummary | null>(null);
  const [goal, setGoal] = useState<Goal | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTodayData = async () => {
      try {
        setLoading(true);
        setError(null);

        const today = apiUtils.getTodayDate();

        // Fetch today data (meals + summary) and goal in parallel - optimized!
        const [todayResult, goalResult] = await Promise.allSettled([
          dailySummaryApi.getTodayData(today),
          goalsApi.getGoal(),
        ]);

        // Handle today data (meals + daily summary)
        if (todayResult.status === 'fulfilled') {
          const { meals: fetchedMeals, daily_summary } = todayResult.value;
          // Ensure meals is always an array
          setMeals(Array.isArray(fetchedMeals) ? fetchedMeals : []);
          setDailySummary(daily_summary);
        } else {
          console.error('Failed to fetch today data:', todayResult.reason);
          // Fallback to separate API calls if optimized endpoint fails
          const [mealsResult, summaryResult] = await Promise.allSettled([
            mealsApi.getMealsByDate(today),
            dailySummaryApi.getDailySummary(today),
          ]);

          if (mealsResult.status === 'fulfilled') {
            // Ensure meals is always an array
            setMeals(Array.isArray(mealsResult.value) ? mealsResult.value : []);
          } else {
            console.error('Failed to fetch meals:', mealsResult.reason);
            // Set empty array as fallback
            setMeals([]);
          }

          if (summaryResult.status === 'fulfilled') {
            setDailySummary(summaryResult.value);
          } else {
            console.error('Failed to fetch daily summary:', summaryResult.reason);
            // Create empty summary if both fail
            setDailySummary({
              user_id: telegramContext.user?.id || '',
              date: today,
              kcal_total: 0,
              macros_totals: {
                protein_g: 0,
                fat_g: 0,
                carbs_g: 0,
              },
            });
          }
        }

        // Handle goal
        if (goalResult.status === 'fulfilled') {
          setGoal(goalResult.value);
        } else {
          console.error('Failed to fetch goal:', goalResult.reason);
        }

      } catch (err) {
        setError('Failed to load today\'s data');
        console.error('Error fetching today data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTodayData();
  }, [telegramContext.user?.id, Array.isArray(meals) ? meals.length : 0]); // Re-fetch when user changes or meals are updated

  const formatCalories = (calories: number): string => {
    return calories.toLocaleString();
  };

  const formatMacro = (grams: number | undefined): string => {
    return grams ? `${Math.round(grams)}g` : '0g';
  };

  const getMealTypeLabel = (mealType: string): string => {
    return t(`today.mealTypes.${mealType}`);
  };

  const getMealTypeIcon = (mealType: string): string => {
    const icons = {
      breakfast: '🌅',
      lunch: '☀️',
      dinner: '🌙',
      snack: '🍎',
    };
    return icons[mealType as keyof typeof icons] || '🍽️';
  };

  const getProgressPercentage = (): number => {
    if (!goal || !dailySummary) return 0;
    return Math.round((dailySummary.kcal_total / goal.daily_kcal_target) * 100);
  };

  const getRemainingCalories = (): number => {
    if (!goal || !dailySummary) return 0;
    return Math.max(0, goal.daily_kcal_target - dailySummary.kcal_total);
  };

  const handleMealClick = (mealId: string) => {
    navigate(`/meal/${mealId}`);
  };

  const handleAddMeal = () => {
    // TODO: Add meal functionality (photo upload or manual entry)
    if (window.Telegram?.WebApp?.showAlert) {
      window.Telegram.WebApp.showAlert('Add meal functionality coming soon!');
    } else {
      alert('Add meal functionality coming soon!');
    }
  };

  if (loading) {
    return (
      <div className="main-content" style={{ padding: 16 }}>
        <header style={{ marginBottom: 24 }}>
          <h1>{t('today.title')}</h1>
          <div style={{ color: 'var(--tg-hint-color)', fontSize: '0.9em' }}>
            {new Date().toLocaleDateString(telegramContext.user?.language || 'en', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </div>
        </header>

        {/* Loading Summary Card */}
        <div className="tg-card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <Skeleton width="40%" height="24px" />
            <Skeleton width="60px" height="32px" style={{ borderRadius: '8px' }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div>
              <Skeleton width="120px" height="32px" style={{ marginBottom: '8px' }} />
              <Skeleton width="100px" height="16px" />
            </div>
            <div>
              <Skeleton width="60px" height="24px" style={{ marginBottom: '8px' }} />
              <Skeleton width="80px" height="16px" />
            </div>
          </div>
          <Skeleton width="100%" height="8px" style={{ borderRadius: '4px', marginBottom: '16px' }} />
          <div style={{ display: 'flex', justifyContent: 'space-around' }}>
            <Skeleton width="50px" height="32px" />
            <Skeleton width="50px" height="32px" />
            <Skeleton width="50px" height="32px" />
          </div>
        </div>

        {/* Loading Meals */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <Skeleton width="80px" height="24px" />
            <Skeleton width="80px" height="32px" style={{ borderRadius: '8px' }} />
          </div>
          <div>
            {[1, 2, 3].map((i) => (
              <div key={i} className="tg-card" style={{ marginBottom: 12, padding: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <Skeleton width="40px" height="40px" style={{ borderRadius: '8px' }} />
                    <div>
                      <Skeleton width="80px" height="16px" style={{ marginBottom: '4px' }} />
                      <Skeleton width="120px" height="14px" />
                    </div>
                  </div>
                  <div>
                    <Skeleton width="60px" height="18px" style={{ marginBottom: '4px' }} />
                    <Skeleton width="100px" height="12px" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Loading Navigation */}
        <nav className="navigation">
          <div className="navigation-item active">
            <div>📊</div>
            <div>{t('navigation.today')}</div>
          </div>
          <div className="navigation-item">
            <div>📈</div>
            <div>{t('navigation.stats')}</div>
          </div>
          <div className="navigation-item">
            <div>🎯</div>
            <div>{t('navigation.goals')}</div>
          </div>
        </nav>
      </div>
    );
  }

  if (error) {
    return (
      <div className="main-content" style={{ padding: 16 }}>
        <h1>{t('today.title')}</h1>
        <div className="error">{t('today.error')}</div>
        <button
          className="tg-button"
          onClick={() => window.location.reload()}
          style={{ marginTop: 16 }}
        >
          {t('common.retry')}
        </button>
      </div>
    );
  }

  return (
    <div className="main-content" style={{ padding: 16 }}>
      <header style={{ marginBottom: 24 }}>
        <h1>{t('today.title')}</h1>
        <div style={{ color: 'var(--tg-hint-color)', fontSize: '0.9em' }}>
          {new Date().toLocaleDateString(telegramContext.user?.language || 'en', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </div>
      </header>

      {/* Daily Summary Card */}
      <div className="tg-card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ margin: 0 }}>{t('today.summary.title')}</h2>
          <Share
            shareData={{
              calories: dailySummary?.kcal_total,
              meals: Array.isArray(meals) ? meals.length : 0,
              goal: goal?.daily_kcal_target,
              date: new Date().toLocaleDateString()
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
                {t('today.summary.goal', { target: formatCalories(goal.daily_kcal_target) })}
              </div>
            )}
          </div>

          {goal && (
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '1.2em', fontWeight: 'bold' }}>
                {getProgressPercentage()}%
              </div>
              <div style={{ color: 'var(--tg-hint-color)', fontSize: '0.9em' }}>
                {getRemainingCalories()} kcal {t('today.summary.remaining')}
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
              <div style={{ color: 'var(--tg-hint-color)' }}>{t('today.macros.protein')}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontWeight: 'bold' }}>{formatMacro(dailySummary.macros_totals.fat_g)}</div>
              <div style={{ color: 'var(--tg-hint-color)' }}>{t('today.macros.fat')}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontWeight: 'bold' }}>{formatMacro(dailySummary.macros_totals.carbs_g)}</div>
              <div style={{ color: 'var(--tg-hint-color)' }}>{t('today.macros.carbs')}</div>
            </div>
          </div>
        )}
      </div>

      {/* Meals List */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ margin: 0 }}>{t('today.meals.title')}</h2>
          <button className="tg-button" onClick={handleAddMeal}>
            {t('today.meals.add')}
          </button>
        </div>

        {!Array.isArray(meals) || meals.length === 0 ? (
          <div className="tg-card" style={{ textAlign: 'center', padding: 32 }}>
            <div style={{ fontSize: '2em', marginBottom: 16 }}>🍽️</div>
            <div style={{ color: 'var(--tg-hint-color)' }}>{t('today.meals.empty')}</div>
          </div>
        ) : (
          <div>
            {meals.map((meal) => (
              <div
                key={meal.id}
                data-testid="meal-item"
                className="tg-card"
                style={{
                  marginBottom: 12,
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                }}
                onClick={() => handleMealClick(meal.id)}
                onMouseDown={(e) => {
                  e.currentTarget.style.transform = 'scale(0.98)';
                }}
                onMouseUp={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    {meal.photo_url ? (
                      <div
                        style={{
                          width: 40,
                          height: 40,
                          borderRadius: 8,
                          backgroundImage: `url(${meal.photo_url})`,
                          backgroundSize: 'cover',
                          backgroundPosition: 'center',
                          flexShrink: 0
                        }}
                      />
                    ) : (
                      <div style={{ fontSize: '1.5em' }}>
                        {getMealTypeIcon(meal.meal_type)}
                      </div>
                    )}
                    <div>
                      <div style={{ fontWeight: 'bold', marginBottom: 4 }}>
                        {getMealTypeLabel(meal.meal_type)}
                      </div>
                      <div style={{ fontSize: '0.9em', color: 'var(--tg-hint-color)' }}>
                        {meal.corrected && (
                          <span style={{ marginRight: 8 }}>📝 {t('today.meals.corrected')}</span>
                        )}
                        {new Date(meal.created_at).toLocaleTimeString(telegramContext.user?.language || 'en', {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </div>
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 'bold', fontSize: '1.1em' }}>
                      {formatCalories(meal.kcal_total)} kcal
                    </div>
                    {meal.macros && (
                      <div style={{ fontSize: '0.8em', color: 'var(--tg-hint-color)' }}>
                        P: {formatMacro(meal.macros.protein_g)} •
                        F: {formatMacro(meal.macros.fat_g)} •
                        C: {formatMacro(meal.macros.carbs_g)}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="navigation">
        <div className="navigation-item active">
          <div>📊</div>
          <div>{t('navigation.today')}</div>
        </div>
        <div className="navigation-item" onClick={() => navigate('/stats')}>
          <div>📈</div>
          <div>{t('navigation.stats')}</div>
        </div>
        <div className="navigation-item" onClick={() => navigate('/goals')}>
          <div>🎯</div>
          <div>{t('navigation.goals')}</div>
        </div>
      </nav>
    </div>
  );
};
