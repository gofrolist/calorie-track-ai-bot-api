/**
 * StatsCharts Component
 * Feature: 005-mini-app-improvements
 *
 * Comprehensive statistics visualization using Recharts
 * Implements UI/UX best practices for mobile-first design
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  getDailyStatistics,
  getMacroStatistics,
  calculateDateRange,
  formatDateForDisplay,
  type DailyStatisticsResponse,
  type MacroStatisticsResponse,
  type DateRangePreset,
} from '../services/statistics';

interface StatsChartsProps {
  className?: string;
}

export function StatsCharts({ className }: StatsChartsProps) {
  const { t, i18n } = useTranslation();

  const [selectedRange, setSelectedRange] = useState<DateRangePreset>('7days');
  const [dailyStats, setDailyStats] = useState<DailyStatisticsResponse | null>(null);
  const [macroStats, setMacroStats] = useState<MacroStatisticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load statistics data
  useEffect(() => {
    loadStatistics();
  }, [selectedRange]);

  const loadStatistics = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const { start_date, end_date } = calculateDateRange(selectedRange);

      // Load both daily and macro statistics in parallel
      const [daily, macro] = await Promise.all([
        getDailyStatistics(start_date, end_date),
        getMacroStatistics(start_date, end_date),
      ]);

      setDailyStats(daily);
      setMacroStats(macro);
    } catch (err) {
      console.error('Failed to load statistics:', err);
      setError(t('statistics.error'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleRangeChange = (range: DateRangePreset) => {
    setSelectedRange(range);
  };

  if (isLoading) {
    return (
      <div
        className={className}
        data-testid="stats-charts"
        role="region"
        aria-label={t('statistics.title')}
        aria-busy="true"
        style={{ padding: '16px', backgroundColor: '#ffffff', minHeight: '200px' }}
      >
        {/* Skeleton Screen - matches actual chart layout */}
        <div role="status" aria-live="polite" aria-label={t('statistics.loading')}>
          {/* Date Range Selector Skeleton */}
          <div style={{ marginBottom: '24px', display: 'flex', gap: '8px', justifyContent: 'center' }}>
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="skeleton-pulse"
                style={{
                  width: '80px',
                  height: '44px',
                  backgroundColor: '#e0e0e0',
                  borderRadius: '8px',
                  animation: 'pulse 1.5s ease-in-out infinite',
                }}
              />
            ))}
          </div>

          {/* Line Chart Skeleton */}
          <div style={{ marginBottom: '32px' }}>
            <div className="skeleton-pulse" style={{ width: '200px', height: '24px', backgroundColor: '#e0e0e0', borderRadius: '4px', marginBottom: '16px' }} />
            <div style={{ height: '250px', backgroundColor: '#f5f5f5', borderRadius: '8px', position: 'relative', overflow: 'hidden' }}>
              {/* Chart lines skeleton */}
              <svg width="100%" height="100%" style={{ position: 'absolute' }}>
                <path
                  d="M 10 200 Q 100 150 200 180 T 390 160"
                  stroke="#e0e0e0"
                  strokeWidth="2"
                  fill="none"
                  className="skeleton-pulse"
                />
              </svg>
            </div>
          </div>

          {/* Pie Chart Skeleton */}
          <div style={{ marginBottom: '32px' }}>
            <div className="skeleton-pulse" style={{ width: '200px', height: '24px', backgroundColor: '#e0e0e0', borderRadius: '4px', marginBottom: '16px' }} />
            <div style={{ display: 'flex', justifyContent: 'center', height: '200px' }}>
              <div
                className="skeleton-pulse"
                style={{
                  width: '160px',
                  height: '160px',
                  backgroundColor: '#e0e0e0',
                  borderRadius: '50%',
                }}
              />
            </div>
          </div>

          {/* Bar Chart Skeleton */}
          <div style={{ marginBottom: '32px' }}>
            <div className="skeleton-pulse" style={{ width: '200px', height: '24px', backgroundColor: '#e0e0e0', borderRadius: '4px', marginBottom: '16px' }} />
            <div style={{ height: '200px', backgroundColor: '#f5f5f5', borderRadius: '8px', padding: '20px', display: 'flex', alignItems: 'flex-end', gap: '8px' }}>
              {[1, 2, 3, 4, 5, 6, 7].map((i) => (
                <div
                  key={i}
                  className="skeleton-pulse"
                  style={{
                    flex: 1,
                    height: `${Math.random() * 80 + 20}%`,
                    backgroundColor: '#e0e0e0',
                    borderRadius: '4px',
                  }}
                />
              ))}
            </div>
          </div>

          {/* Summary Statistics Skeleton */}
          <div style={{ padding: '16px', backgroundColor: '#f5f5f5', borderRadius: '8px', marginTop: '24px' }}>
            <div className="skeleton-pulse" style={{ width: '150px', height: '20px', backgroundColor: '#e0e0e0', borderRadius: '4px', marginBottom: '12px' }} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              {[1, 2].map((i) => (
                <div key={i}>
                  <div className="skeleton-pulse" style={{ width: '100px', height: '14px', backgroundColor: '#e0e0e0', borderRadius: '4px', marginBottom: '8px' }} />
                  <div className="skeleton-pulse" style={{ width: '80px', height: '24px', backgroundColor: '#e0e0e0', borderRadius: '4px' }} />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* CSS Animation for pulse effect */}
        <style>{`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
          .skeleton-pulse {
            animation: pulse 1.5s ease-in-out infinite;
          }
        `}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className={className}
        data-testid="stats-charts"
        role="region"
        aria-label={t('statistics.title')}
        style={{ padding: '16px', backgroundColor: '#ffffff', minHeight: '200px' }}
      >
        <div style={{ textAlign: 'center', padding: '32px 0' }}>
          <p
            role="alert"
            aria-live="assertive"
            style={{ color: '#d32f2f', marginBottom: '16px' }}
          >
            {error}
          </p>
          <button
            onClick={loadStatistics}
            aria-label={t('common.retry')}
            style={{
              padding: '12px 24px',
              minHeight: '44px',
              fontSize: '16px',
              backgroundColor: 'var(--tg-button-color, #0066cc)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
            }}
          >
            {t('common.retry')}
          </button>
        </div>
      </div>
    );
  }

  if (!dailyStats || dailyStats.data.length === 0) {
    return (
      <div
        className={className}
        data-testid="stats-charts"
        role="region"
        aria-label={t('statistics.title')}
        style={{ padding: '16px', backgroundColor: '#ffffff', minHeight: '200px' }}
      >
        <div style={{ textAlign: 'center', padding: '48px 16px' }}>
          <div role="img" aria-label="Chart icon" style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
          <h3 style={{ fontSize: '20px', marginBottom: '8px' }}>{t('statistics.emptyState.title')}</h3>
          <p style={{ color: 'var(--tg-hint-color, #6b6b6b)', marginBottom: '24px' }}>{t('statistics.emptyState.message')}</p>
          <button
            onClick={() => window.location.href = '/'}
            aria-label={t('statistics.emptyState.action')}
            style={{
              padding: '12px 24px',
              minHeight: '44px',
              fontSize: '16px',
              backgroundColor: 'var(--tg-button-color, #0066cc)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
            }}
          >
            {t('statistics.emptyState.action')}
          </button>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const chartData = dailyStats.data.map(dp => ({
    date: formatDateForDisplay(dp.date, i18n.language),
    fullDate: dp.date,
    calories: dp.total_calories,
    protein: dp.total_protein,
    fat: dp.total_fat,
    carbs: dp.total_carbs,
    meals: dp.meal_count,
    goal: dp.goal_calories,
    achievement: dp.goal_achievement,
  }));

  // Macro pie chart data
  const macroData = macroStats ? [
    { name: t('statistics.chart.protein'), value: macroStats.protein_percent, grams: macroStats.protein_grams, color: '#4CAF50' },
    { name: t('statistics.chart.fat'), value: macroStats.fat_percent, grams: macroStats.fat_grams, color: '#FF9800' },
    { name: t('statistics.chart.carbs'), value: macroStats.carbs_percent, grams: macroStats.carbs_grams, color: '#2196F3' },
  ] : [];

  return (
    <div
      className={className}
      data-testid="stats-charts"
      role="region"
      aria-label={t('statistics.title')}
      aria-describedby="stats-summary"
      style={{
        padding: '16px',
        paddingBottom: '80px',
        backgroundColor: '#ffffff',
        minHeight: '200px'
      }}
    >
      {/* Date Range Selector */}
      <div style={{ marginBottom: '24px' }}>
        <div
          style={{
            display: 'flex',
            gap: '8px',
            flexWrap: 'wrap',
            justifyContent: 'center',
          }}
          role="radiogroup"
          aria-label={t('statistics.period.title')}
        >
          {(['7days', '30days', '90days'] as DateRangePreset[]).map((range) => (
            <button
              key={range}
              type="button"
              role="radio"
              aria-checked={selectedRange === range}
              data-testid={`date-range-${range.replace('days', '')}`}
              onClick={() => handleRangeChange(range)}
              style={{
                flex: '1 1 auto',
                minWidth: '80px',
                minHeight: '44px', // CHK001: Touch target
                padding: '10px 16px',
                fontSize: '16px',
                fontWeight: selectedRange === range ? '600' : '400',
                backgroundColor: selectedRange === range ? 'var(--tg-button-color, #0066cc)' : '#f0f0f0',
                color: selectedRange === range ? 'white' : 'var(--tg-text-color, #333)',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              {t(`statistics.period.${range}`)}
            </button>
          ))}
        </div>
      </div>

      {/* Primary Visualization: Time-Series Calorie Trend (CHK020) */}
      <div style={{ marginBottom: '32px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
          {t('statistics.caloriesOverTime')}
        </h3>
        <div role="img" aria-label={t('statistics.caloriesOverTime')} style={{ width: '100%', backgroundColor: 'var(--tg-bg-color, #fff)' }}>
          <ResponsiveContainer width="100%" height={250}>
          <LineChart
            data={chartData}
            margin={{ top: 5, right: 5, left: 5, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12 }}
              stroke="#666"
            />
            <YAxis
              tick={{ fontSize: 12 }}
              stroke="#666"
              label={{ value: t('statistics.chart.calories'), angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid #ddd',
                borderRadius: '8px',
                padding: '12px',
              }}
              formatter={(value: number, name: string) => [
                `${Math.round(value)} ${name === 'calories' ? 'kcal' : ''}`,
                name === 'calories' ? t('statistics.chart.calories') : name
              ]}
              labelFormatter={(label: string, payload: any) => {
                if (payload && payload.length > 0) {
                  return payload[0].payload.fullDate;
                }
                return label;
              }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            {chartData.some(d => d.goal) && (
              <Line
                type="monotone"
                dataKey="goal"
                stroke="#FF9800"
                strokeDasharray="5 5"
                name={t('statistics.chart.goal')}
                dot={false}
              />
            )}
            <Line
              type="monotone"
              dataKey="calories"
              stroke="var(--tg-button-color, #0066cc)"
              strokeWidth={2}
              name={t('statistics.chart.calories')}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
        </div>
      </div>

      {/* Supporting Visualization: Macronutrient Breakdown (CHK021) */}
      {macroStats && macroStats.total_calories > 0 && (
        <div style={{ marginBottom: '32px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
            {t('statistics.macroBreakdown')}
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div role="img" aria-label={t('statistics.macroBreakdown')} style={{ width: '100%', backgroundColor: 'var(--tg-bg-color, #fff)' }}>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={macroData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry: any) => `${entry.name}: ${(entry.value as number).toFixed(1)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {macroData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number, name: string, props: any) => [
                    `${value.toFixed(1)}% (${Math.round(props.payload.grams)}g)`,
                    name
                  ]}
                />
              </PieChart>
            </ResponsiveContainer>
            </div>

            {/* Macro details */}
            <div style={{ width: '100%', marginTop: '16px' }}>
              {macroData.map((macro) => (
                <div
                  key={macro.name}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    padding: '8px 16px',
                    borderRadius: '4px',
                    backgroundColor: '#f5f5f5',
                    marginBottom: '8px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div
                      style={{
                        width: '12px',
                        height: '12px',
                        backgroundColor: macro.color,
                        borderRadius: '2px',
                      }}
                    />
                    <span style={{ fontWeight: '500' }}>{macro.name}</span>
                  </div>
                  <span>{macro.value.toFixed(1)}% ({Math.round(macro.grams)}g)</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Supporting Visualization: Goal Achievement (CHK021) */}
      {dailyStats.data.some(d => d.goal_achievement) && (
        <div style={{ marginBottom: '32px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
            {t('statistics.goalTracking')}
          </h3>
          <div role="img" aria-label={t('statistics.goalTracking')} style={{ width: '100%', backgroundColor: 'var(--tg-bg-color, #fff)' }}>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart
              data={chartData.filter(d => d.achievement !== null)}
              margin={{ top: 5, right: 5, left: 5, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                stroke="#666"
              />
              <YAxis
                tick={{ fontSize: 12 }}
                stroke="#666"
                label={{ value: '%', angle: 0, position: 'insideTopLeft', style: { fontSize: 12 } }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #ddd',
                  borderRadius: '8px',
                  padding: '12px',
                }}
                formatter={(value: number) => [`${Math.round(value)}%`, t('statistics.goalTracking')]}
              />
              <Bar
                dataKey="achievement"
                fill="#4CAF50"
                name={t('statistics.goalTracking')}
                radius={[4, 4, 0, 0]}
              >
                {chartData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.achievement && entry.achievement > 100 ? '#FF9800' : '#4CAF50'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          </div>

          {/* Achievement summary */}
          <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ color: 'var(--tg-text-color, #000)' }}>{t('statistics.summary.avgAchievement')}:</span>
              <span style={{ fontWeight: '600', color: 'var(--tg-text-color, #000)' }}>
                {dailyStats.summary.average_goal_achievement?.toFixed(1) || 'N/A'}%
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--tg-text-color, #000)' }}>{t('statistics.summary.daysOverGoal')}:</span>
              <span style={{ fontWeight: '600', color: 'var(--tg-text-color, #000)' }}>
                {chartData.filter(d => d.achievement && d.achievement > 100).length}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Summary Statistics */}
      <div id="stats-summary" style={{ marginTop: '24px', padding: '16px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
        <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px' }}>
          {t('statistics.summary.title')}
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--tg-hint-color, #6b6b6b)', marginBottom: '4px' }}>
              {t('statistics.summary.totalMeals')}
            </div>
            <div style={{ fontSize: '20px', fontWeight: '600', color: 'var(--tg-text-color, #000)' }}>
              {dailyStats.summary.total_meals}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--tg-hint-color, #6b6b6b)', marginBottom: '4px' }}>
              {t('statistics.summary.avgDaily')}
            </div>
            <div style={{ fontSize: '20px', fontWeight: '600', color: 'var(--tg-text-color, #000)' }}>
              {Math.round(dailyStats.summary.average_daily_calories)} kcal
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default StatsCharts;
