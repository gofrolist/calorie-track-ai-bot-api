/**
 * Navigation Component
 *
 * Reusable bottom navigation bar for all pages
 * - Consistent across Meals, Stats, and Goals pages
 * - i18n support for labels
 */

import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();

  const navItems = [
    {
      path: '/',
      icon: '🍽️',
      label: t('navigation.meals'),
    },
    {
      path: '/stats',
      icon: '📈',
      label: t('navigation.stats'),
    },
    {
      path: '/goals',
      icon: '🎯',
      label: t('navigation.goals'),
    },
  ];

  return (
    <nav className="navigation">
      {navItems.map((item) => (
        <div
          key={item.path}
          className={`navigation-item ${location.pathname === item.path ? 'active' : ''}`}
          onClick={() => navigate(item.path)}
        >
          <div>{item.icon}</div>
          <div>{item.label}</div>
        </div>
      ))}
    </nav>
  );
};

export default Navigation;
