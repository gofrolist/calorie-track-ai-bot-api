/**
 * Stats Page - Nutrition Statistics and Visualization
 * Feature: 005-mini-app-improvements (Complete Rework)
 *
 * Interactive charts showing calorie trends, macronutrient breakdowns,
 * and goal achievement tracking with Recharts library
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Navigation } from '../components/Navigation';
import { StatsCharts } from '../components/StatsCharts';

export const Stats: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="main-content">
      {/* Page Header */}
      <header style={{
        padding: '16px',
        borderBottom: '1px solid var(--tg-hint-color, #ddd)',
      }}>
        <h1 style={{
          fontSize: '24px',
          fontWeight: '600',
          margin: 0,
          color: 'var(--tg-text-color, #000)',
        }}>
          {t('statistics.title')}
        </h1>
      </header>

      {/* Statistics Charts */}
      <StatsCharts className="stats-charts-container" />

      {/* Bottom Navigation */}
      <Navigation />
    </div>
  );
};

export default Stats;
