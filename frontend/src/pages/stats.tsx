import React, { useState, useEffect, useContext } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import {
  dailySummaryApi,
  goalsApi,
  apiUtils,
  type DailySummary,
  type Goal
} from '../services/api';
import { TelegramWebAppContext } from '../app';

interface SimpleChart {
  data: Array<{ date: string; value: number; label?: string }>;
  maxValue: number;
  type: 'bar' | 'line';
}

type StatsView = 'week' | 'month';

export const Stats: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const telegramContext = useContext(TelegramWebAppContext);

  const [currentView, setCurrentView] = useState<StatsView>('week');
  const [weeklyData, setWeeklyData] = useState<DailySummary[]>([]);
  const [monthlyData, setMonthlyData] = useState<DailySummary[]>([]);
  const [goal, setGoal] = useState<Goal | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatsData = async () => {
      try {
        setLoading(true);
        setError(null);

        const today = new Date();

        // Calculate week start (Monday)
        const weekStart = new Date(today);
        const dayOfWeek = weekStart.getDay();
        const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
        weekStart.setDate(weekStart.getDate() - daysToMonday);

        // Calculate month start
        const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);

        // Fetch data in parallel
        const [weeklyResult, monthlyResult, goalResult] = await Promise.allSettled([
          dailySummaryApi.getWeeklySummary(apiUtils.formatDate(weekStart)),
          dailySummaryApi.getMonthlySummary(today.getFullYear(), today.getMonth() + 1),
          goalsApi.getGoal(),
        ]);

        if (weeklyResult.status === 'fulfilled') {
          setWeeklyData(weeklyResult.value);
        } else {
          console.error('Failed to fetch weekly data:', weeklyResult.reason);
        }

        if (monthlyResult.status === 'fulfilled') {
          setMonthlyData(monthlyResult.value);
        } else {
          console.error('Failed to fetch monthly data:', monthlyResult.reason);
        }

        if (goalResult.status === 'fulfilled') {
          setGoal(goalResult.value);
        } else {
          console.error('Failed to fetch goal:', goalResult.reason);
        }

      } catch (err) {
        setError('Failed to load stats data');
        console.error('Error fetching stats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStatsData();
  }, []);

  const formatCalories = (calories: number): string => {
    return calories.toLocaleString();
  };

  const formatMacro = (grams: number | undefined): string => {
    return grams ? `${Math.round(grams)}g` : '0g';
  };

  const getWeeklyChartData = (): SimpleChart => {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const today = new Date();
    const weekStart = new Date(today);
    const dayOfWeek = weekStart.getDay();
    const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    weekStart.setDate(weekStart.getDate() - daysToMonday);

    const chartData = days.map((day, index) => {
      const date = new Date(weekStart);
      date.setDate(weekStart.getDate() + index);
      const dateStr = apiUtils.formatDate(date);

      const dayData = weeklyData.find(d => d.date === dateStr);
      return {
        date: dateStr,
        value: dayData?.kcal_total || 0,
        label: day,
      };
    });

    const maxValue = Math.max(...chartData.map(d => d.value), goal?.daily_kcal_target || 2000);

    return {
      data: chartData,
      maxValue,
      type: 'bar',
    };
  };

  const getMonthlyChartData = (): SimpleChart => {
    const chartData = monthlyData.map(day => ({
      date: day.date,
      value: day.kcal_total,
      label: new Date(day.date).getDate().toString(),
    }));

    const maxValue = Math.max(...chartData.map(d => d.value), goal?.daily_kcal_target || 2000);

    return {
      data: chartData,
      maxValue,
      type: 'line',
    };
  };

  const renderSimpleChart = (chart: SimpleChart) => {
    if (chart.data.length === 0) {
      return (
        <div style={{
          height: 200,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--tg-hint-color)'
        }}>
          No data available
        </div>
      );
    }

    const chartHeight = 160;
    const chartWidth = chart.data.length * 40;

    return (
      <div style={{
        overflowX: 'auto',
        padding: '16px 0',
        background: 'var(--tg-secondary-bg-color)',
        borderRadius: 8,
        margin: '16px 0'
      }}>
        <div style={{
          position: 'relative',
          height: chartHeight + 40,
          minWidth: chartWidth,
          padding: '0 20px'
        }}>
          {/* Goal line */}
          {goal && (
            <div style={{
              position: 'absolute',
              left: 20,
              right: 20,
              top: chartHeight - (goal.daily_kcal_target / chart.maxValue) * chartHeight,
              height: 1,
              backgroundColor: 'var(--tg-link-color)',
              opacity: 0.6,
            }}>
              <div style={{
                position: 'absolute',
                right: 0,
                top: -10,
                fontSize: '0.8em',
                color: 'var(--tg-link-color)',
                background: 'var(--tg-bg-color)',
                padding: '2px 4px',
                borderRadius: 4,
              }}>
                Goal: {formatCalories(goal.daily_kcal_target)}
              </div>
            </div>
          )}

          {/* Data bars/points */}
          {chart.data.map((point, index) => {
            const height = (point.value / chart.maxValue) * chartHeight;
            const left = index * 40;

            if (chart.type === 'bar') {
              return (
                <div key={point.date}>
                  <div
                    style={{
                      position: 'absolute',
                      left: left + 8,
                      bottom: 20,
                      width: 24,
                      height,
                      backgroundColor: point.value >= (goal?.daily_kcal_target || 0) ?
                        'var(--tg-button-color)' : 'var(--tg-hint-color)',
                      borderRadius: '4px 4px 0 0',
                    }}
                  />
                  <div style={{
                    position: 'absolute',
                    left: left,
                    bottom: 0,
                    width: 40,
                    fontSize: '0.8em',
                    textAlign: 'center',
                    color: 'var(--tg-hint-color)',
                  }}>
                    {point.label}
                  </div>
                  {point.value > 0 && (
                    <div style={{
                      position: 'absolute',
                      left: left,
                      bottom: height + 22,
                      width: 40,
                      fontSize: '0.7em',
                      textAlign: 'center',
                      color: 'var(--tg-text-color)',
                    }}>
                      {formatCalories(point.value)}
                    </div>
                  )}
                </div>
              );
            } else {
              // Line chart points
              const nextPoint = chart.data[index + 1];
              return (
                <div key={point.date}>
                  <div
                    style={{
                      position: 'absolute',
                      left: left + 16,
                      bottom: 20 + height - 3,
                      width: 6,
                      height: 6,
                      backgroundColor: 'var(--tg-button-color)',
                      borderRadius: '50%',
                    }}
                  />
                  {nextPoint && (
                    <div
                      style={{
                        position: 'absolute',
                        left: left + 19,
                        bottom: 20 + height,
                        width: Math.sqrt(Math.pow(40, 2) + Math.pow((nextPoint.value - point.value) / chart.maxValue * chartHeight, 2)),
                        height: 1,
                        backgroundColor: 'var(--tg-button-color)',
                        transformOrigin: '0 0',
                        transform: `rotate(${Math.atan2((nextPoint.value - point.value) / chart.maxValue * chartHeight, 40) * 180 / Math.PI}deg)`,
                      }}
                    />
                  )}
                  <div style={{
                    position: 'absolute',
                    left: left,
                    bottom: 0,
                    width: 40,
                    fontSize: '0.7em',
                    textAlign: 'center',
                    color: 'var(--tg-hint-color)',
                  }}>
                    {point.label}
                  </div>
                </div>
              );
            }
          })}
        </div>
      </div>
    );
  };

  const getStatsData = () => {
    const data = currentView === 'week' ? weeklyData : monthlyData;

    if (data.length === 0) {
      return {
        totalCalories: 0,
        averageCalories: 0,
        totalProtein: 0,
        totalFat: 0,
        totalCarbs: 0,
        daysWithData: 0,
      };
    }

    const totalCalories = data.reduce((sum, day) => sum + day.kcal_total, 0);
    const totalProtein = data.reduce((sum, day) => sum + (day.macros_totals?.protein_g || 0), 0);
    const totalFat = data.reduce((sum, day) => sum + (day.macros_totals?.fat_g || 0), 0);
    const totalCarbs = data.reduce((sum, day) => sum + (day.macros_totals?.carbs_g || 0), 0);
    const daysWithData = data.filter(day => day.kcal_total > 0).length;

    return {
      totalCalories,
      averageCalories: daysWithData > 0 ? Math.round(totalCalories / daysWithData) : 0,
      totalProtein,
      totalFat,
      totalCarbs,
      daysWithData,
    };
  };

  if (loading) {
    return (
      <div className="main-content" style={{ padding: 16 }}>
        <div className="loading">Loading stats...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="main-content" style={{ padding: 16 }}>
        <h1>Week/Month Stats</h1>
        <div className="error">{error}</div>
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

  const stats = getStatsData();
  const chartData = currentView === 'week' ? getWeeklyChartData() : getMonthlyChartData();

  return (
    <div className="main-content" style={{ padding: 16 }}>
      <header style={{ marginBottom: 24 }}>
        <h1>Week/Month Stats</h1>
      </header>

      {/* View Toggle */}
      <div className="tg-card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            className={currentView === 'week' ? 'tg-button' : 'tg-button-secondary'}
            onClick={() => setCurrentView('week')}
            style={{ flex: 1 }}
          >
            This Week
          </button>
          <button
            className={currentView === 'month' ? 'tg-button' : 'tg-button-secondary'}
            onClick={() => setCurrentView('month')}
            style={{ flex: 1 }}
          >
            This Month
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="tg-card" style={{ marginBottom: 24 }}>
        <h2 style={{ marginTop: 0, marginBottom: 16 }}>
          {currentView === 'week' ? 'Weekly' : 'Monthly'} Summary
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '1.5em', fontWeight: 'bold', marginBottom: 4 }}>
              {formatCalories(stats.totalCalories)}
            </div>
            <div style={{ color: 'var(--tg-hint-color)', fontSize: '0.9em' }}>
              Total Calories
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '1.5em', fontWeight: 'bold', marginBottom: 4 }}>
              {formatCalories(stats.averageCalories)}
            </div>
            <div style={{ color: 'var(--tg-hint-color)', fontSize: '0.9em' }}>
              Daily Average
            </div>
          </div>
        </div>

        {/* Macros breakdown */}
        <div style={{ display: 'flex', justifyContent: 'space-around', fontSize: '0.9em' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontWeight: 'bold' }}>{formatMacro(stats.totalProtein)}</div>
            <div style={{ color: 'var(--tg-hint-color)' }}>Protein</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontWeight: 'bold' }}>{formatMacro(stats.totalFat)}</div>
            <div style={{ color: 'var(--tg-hint-color)' }}>Fat</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontWeight: 'bold' }}>{formatMacro(stats.totalCarbs)}</div>
            <div style={{ color: 'var(--tg-hint-color)' }}>Carbs</div>
          </div>
        </div>

        <div style={{
          marginTop: 16,
          padding: 12,
          backgroundColor: 'var(--tg-bg-color)',
          borderRadius: 8,
          fontSize: '0.9em',
          color: 'var(--tg-hint-color)'
        }}>
          {stats.daysWithData} days with logged meals
        </div>
      </div>

      {/* Chart */}
      <div className="tg-card" style={{ marginBottom: 24 }}>
        <h3 style={{ marginTop: 0, marginBottom: 8 }}>
          Daily Calories ({currentView === 'week' ? 'This Week' : 'This Month'})
        </h3>
        {renderSimpleChart(chartData)}
      </div>

      {/* Goal Progress (if goal is set) */}
      {goal && stats.daysWithData > 0 && (
        <div className="tg-card" style={{ marginBottom: 24 }}>
          <h3 style={{ marginTop: 0, marginBottom: 16 }}>Goal Progress</h3>

          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span>Daily Target:</span>
              <span style={{ fontWeight: 'bold' }}>{formatCalories(goal.daily_kcal_target)} kcal</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <span>Your Average:</span>
              <span style={{ fontWeight: 'bold' }}>{formatCalories(stats.averageCalories)} kcal</span>
            </div>

            {(() => {
              const targetMet = stats.averageCalories >= goal.daily_kcal_target;
              return (
                <div style={{
                  padding: 12,
                  borderRadius: 8,
                  backgroundColor: targetMet ? '#34c759' : '#ff9500',
                  color: 'white',
                  textAlign: 'center',
                  fontWeight: 'bold'
                }}>
                  {targetMet ? '🎉 Target Met!' : '📈 Keep Going!'}
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="navigation">
        <div className="navigation-item" onClick={() => navigate('/')}>
          <div>📊</div>
          <div>Today</div>
        </div>
        <div className="navigation-item active">
          <div>📈</div>
          <div>Stats</div>
        </div>
        <div className="navigation-item" onClick={() => navigate('/goals')}>
          <div>🎯</div>
          <div>Goals</div>
        </div>
      </nav>
    </div>
  );
};
