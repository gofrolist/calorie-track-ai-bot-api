import React, { useState, useEffect, useContext } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import {
  goalsApi,
  dailySummaryApi,
  apiUtils,
  type Goal,
  type DailySummary
} from '../services/api';
import { TelegramWebAppContext } from '../app';

interface GoalFormData {
  daily_kcal_target: number;
}

interface ValidationErrors {
  daily_kcal_target?: string;
}

export const Goals: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const telegramContext = useContext(TelegramWebAppContext);

  const [goal, setGoal] = useState<Goal | null>(null);
  const [dailySummary, setDailySummary] = useState<DailySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [goalForm, setGoalForm] = useState<GoalFormData>({ daily_kcal_target: 2000 });
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    const fetchGoalsData = async () => {
      try {
        setLoading(true);
        setError(null);

        const today = apiUtils.getTodayDate();

        // Fetch goal and daily summary in parallel
        const [goalResult, summaryResult] = await Promise.allSettled([
          goalsApi.getGoal(),
          dailySummaryApi.getDailySummary(today),
        ]);

        if (goalResult.status === 'fulfilled') {
          const goalData = goalResult.value;
          setGoal(goalData);
          if (goalData) {
            setGoalForm({ daily_kcal_target: goalData.daily_kcal_target });
          }
        } else {
          console.error('Failed to fetch goal:', goalResult.reason);
        }

        if (summaryResult.status === 'fulfilled') {
          setDailySummary(summaryResult.value);
        } else {
          console.error('Failed to fetch daily summary:', summaryResult.reason);
          // Create empty summary if API fails
          setDailySummary({
            user_id: telegramContext.user?.id || '',
            date: today,
            kcal_total: 0,
            macros_totals: { protein_g: 0, fat_g: 0, carbs_g: 0 },
          });
        }

      } catch (err) {
        setError('Failed to load goals. Please try again.');
        console.error('Error fetching goals:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchGoalsData();
  }, [telegramContext.user?.id]);

  const formatCalories = (calories: number): string => {
    return calories.toLocaleString();
  };

  const getProgressPercentage = (): number => {
    if (!goal || !dailySummary) return 0;
    return Math.round((dailySummary.kcal_total / goal.daily_kcal_target) * 100);
  };

  const getRemainingCalories = (): number => {
    if (!goal || !dailySummary) return 0;
    const remaining = goal.daily_kcal_target - dailySummary.kcal_total;
    return remaining;
  };

  const validateForm = (): boolean => {
    const errors: ValidationErrors = {};

    if (goalForm.daily_kcal_target < 500 || goalForm.daily_kcal_target > 10000) {
      errors.daily_kcal_target = 'Daily calorie goal must be between 500 and 10,000';
    }

    if (isNaN(goalForm.daily_kcal_target)) {
      errors.daily_kcal_target = 'Please enter a valid number';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleEdit = () => {
    setIsEditing(true);
    setValidationErrors({});
    setSaveMessage(null);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setValidationErrors({});
    setSaveMessage(null);

    // Reset form to original value
    if (goal) {
      setGoalForm({ daily_kcal_target: goal.daily_kcal_target });
    }
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      setSaveLoading(true);
      setSaveMessage(null);

      let updatedGoal: Goal;
      if (goal) {
        // Update existing goal
        updatedGoal = await goalsApi.updateGoal(goalForm.daily_kcal_target);
      } else {
        // Create new goal
        updatedGoal = await goalsApi.createGoal(goalForm.daily_kcal_target);
      }

      setGoal(updatedGoal);
      setIsEditing(false);
      setSaveMessage('Goal updated successfully');

      // Clear message after 3 seconds
      setTimeout(() => setSaveMessage(null), 3000);

    } catch (err) {
      console.error('Failed to save goal:', err);
      setSaveMessage('Failed to save goal. Please try again.');
    } finally {
      setSaveLoading(false);
    }
  };

  const handleRetry = () => {
    window.location.reload();
  };

  const handleInputChange = (value: string) => {
    const numValue = parseInt(value) || 0;
    setGoalForm({ daily_kcal_target: numValue });

    // Clear validation error
    if (validationErrors.daily_kcal_target) {
      setValidationErrors({});
    }
  };

  if (loading) {
    return (
      <div className="main-content" style={{ padding: 16 }}>
        <div className="loading">Loading goals...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="main-content" style={{ padding: 16 }}>
        <h1>Goals</h1>
        <div className="error">{error}</div>
        <button className="tg-button" onClick={handleRetry} style={{ marginTop: 16 }}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="main-content" style={{ padding: 16 }}>
      <header style={{ marginBottom: 24 }}>
        <h1>Goals</h1>
      </header>

      {/* Save Message */}
      {saveMessage && (
        <div className={`${saveMessage.includes('successfully') ? 'success' : 'error'}`}>
          {saveMessage}
        </div>
      )}

      {/* Goal Setting Card */}
      <div className="tg-card" style={{ marginBottom: 24 }}>
        <h2 style={{ marginTop: 0, marginBottom: 16 }}>Daily Calorie Goal</h2>

        {goal || isEditing ? (
          <div>
            {isEditing ? (
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', marginBottom: 8, fontWeight: 'bold' }}>
                  Daily Calorie Goal
                </label>
                <input
                  type="number"
                  aria-label="Daily Calorie Goal"
                  value={goalForm.daily_kcal_target}
                  onChange={(e) => handleInputChange(e.target.value)}
                  placeholder="e.g., 2000"
                  style={{
                    width: '100%',
                    padding: 12,
                    border: `1px solid ${validationErrors.daily_kcal_target ? '#ff3b30' : 'var(--tg-hint-color)'}`,
                    borderRadius: 8,
                    fontSize: '1em',
                    backgroundColor: 'var(--tg-bg-color)',
                    color: 'var(--tg-text-color)',
                  }}
                />
                {validationErrors.daily_kcal_target && (
                  <div style={{ color: '#ff3b30', fontSize: '0.9em', marginTop: 4 }}>
                    {validationErrors.daily_kcal_target}
                  </div>
                )}
              </div>
            ) : (
              <div style={{ textAlign: 'center', marginBottom: 16 }}>
                <div style={{ fontSize: '2em', fontWeight: 'bold', marginBottom: 8 }}>
                  {formatCalories(goal?.daily_kcal_target || 0)} kcal
                </div>
                <div style={{ color: 'var(--tg-hint-color)' }}>
                  Daily target
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
              {isEditing ? (
                <>
                  <button
                    className="tg-button"
                    onClick={handleSave}
                    disabled={saveLoading}
                    style={{ opacity: saveLoading ? 0.6 : 1 }}
                  >
                    {saveLoading ? 'Saving...' : 'Save'}
                  </button>
                  <button
                    className="tg-button-secondary"
                    onClick={handleCancel}
                    disabled={saveLoading}
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <button className="tg-button" onClick={handleEdit}>
                  Edit Goal
                </button>
              )}
            </div>
          </div>
        ) : (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2em', marginBottom: 16 }}>🎯</div>
            <div style={{ marginBottom: 16, color: 'var(--tg-hint-color)' }}>
              No goals set yet.
            </div>
            <button className="tg-button" onClick={() => setIsEditing(true)}>
              Set Daily Goal
            </button>
          </div>
        )}
      </div>

      {/* Today's Progress */}
      {goal && dailySummary && (
        <div className="tg-card" style={{ marginBottom: 24 }}>
          <h3 style={{ marginTop: 0, marginBottom: 16 }}>Today's Progress</h3>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: '1.5em', fontWeight: 'bold' }}>
                {formatCalories(dailySummary.kcal_total)} / {formatCalories(goal.daily_kcal_target)} kcal
              </div>
              <div style={{ color: 'var(--tg-hint-color)', fontSize: '0.9em' }}>
                {getRemainingCalories() > 0
                  ? `${formatCalories(getRemainingCalories())} kcal remaining`
                  : `${formatCalories(Math.abs(getRemainingCalories()))} kcal over goal`
                }
              </div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '1.2em', fontWeight: 'bold' }}>
                {getProgressPercentage()}%
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div
            className="progress-bar"
            role="progressbar"
            aria-valuenow={getProgressPercentage()}
            aria-valuemax={100}
          >
            <div
              className="progress-bar-fill"
              style={{ width: `${Math.min(getProgressPercentage(), 100)}%` }}
            />
          </div>

          {/* Progress Status */}
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            {(() => {
              const percentage = getProgressPercentage();
              if (percentage >= 100) {
                return (
                  <div style={{
                    padding: 12,
                    borderRadius: 8,
                    backgroundColor: '#34c759',
                    color: 'white',
                    fontWeight: 'bold'
                  }}>
                    🎉 Goal achieved!
                  </div>
                );
              } else if (percentage >= 80) {
                return (
                  <div style={{
                    padding: 12,
                    borderRadius: 8,
                    backgroundColor: '#ff9500',
                    color: 'white',
                    fontWeight: 'bold'
                  }}>
                    💪 Almost there!
                  </div>
                );
              } else {
                return (
                  <div style={{
                    padding: 12,
                    borderRadius: 8,
                    backgroundColor: 'var(--tg-secondary-bg-color)',
                    color: 'var(--tg-text-color)',
                    fontWeight: 'bold'
                  }}>
                    📈 Keep going!
                  </div>
                );
              }
            })()}
          </div>
        </div>
      )}

      {/* Tips Card */}
      <div className="tg-card" style={{ marginBottom: 24 }}>
        <h3 style={{ marginTop: 0, marginBottom: 12 }}>💡 Tips</h3>
        <div style={{ fontSize: '0.9em', color: 'var(--tg-hint-color)', lineHeight: 1.5 }}>
          <p style={{ margin: '0 0 8px 0' }}>
            • Set a realistic daily calorie goal based on your activity level
          </p>
          <p style={{ margin: '0 0 8px 0' }}>
            • Track your meals consistently to see progress over time
          </p>
          <p style={{ margin: '0 0 8px 0' }}>
            • Check your weekly stats to understand your patterns
          </p>
          <p style={{ margin: '0' }}>
            • Adjust your goal as needed based on your results
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="navigation">
        <div className="navigation-item" onClick={() => navigate('/')}>
          <div>📊</div>
          <div>Today</div>
        </div>
        <div className="navigation-item" onClick={() => navigate('/stats')}>
          <div>📈</div>
          <div>Stats</div>
        </div>
        <div className="navigation-item active">
          <div>🎯</div>
          <div>Goals</div>
        </div>
      </nav>
    </div>
  );
};
