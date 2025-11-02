/**
 * Navigation Component
 *
 * Reusable bottom navigation bar for all pages
 * - Consistent across Meals, Stats, and Goals pages
 * - Single source of truth for navigation items
 * - i18n support for labels
 * - Hamburger menu for additional options (Feature 005)
 */

import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const [menuOpen, setMenuOpen] = useState(false);

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

  const menuItems = [
    {
      path: '/feedback',
      icon: '💬',
      label: t('feedback.title'),
    },
  ];

  const handleMenuItemClick = (path: string) => {
    navigate(path);
    setMenuOpen(false);
  };

  return (
    <>
      {/* Hamburger menu overlay */}
      {menuOpen && (
        <div
          className="menu-overlay"
          onClick={() => setMenuOpen(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 999,
            transition: 'opacity 0.3s',
          }}
        />
      )}

      {/* Hamburger menu drawer */}
      {menuOpen && (
        <div
          className="menu-drawer"
          role="dialog"
          aria-label={t('navigation.menu')}
          style={{
            position: 'fixed',
            top: 0,
            right: 0,
            bottom: 0,
            width: '280px',
            maxWidth: '80%',
            backgroundColor: 'var(--tg-theme-bg-color, white)',
            boxShadow: '-2px 0 8px rgba(0, 0, 0, 0.1)',
            zIndex: 1000,
            padding: '24px 16px',
            overflowY: 'auto',
            animation: 'slideIn 0.3s ease-out',
          }}
        >
          <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '20px', fontWeight: '600', margin: 0 }}>
              {t('navigation.menu')}
            </h3>
            <button
              onClick={() => setMenuOpen(false)}
              aria-label={t('navigation.close')}
              style={{
                minWidth: '44px', // CHK001: Minimum touch target
                minHeight: '44px',
                fontSize: '24px',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '8px',
              }}
            >
              ✕
            </button>
          </div>

          {menuItems.map((item) => (
            <div
              key={item.path}
              className="menu-item"
              onClick={() => handleMenuItemClick(item.path)}
              role="menuitem"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  handleMenuItemClick(item.path);
                }
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '16px',
                padding: '16px',
                minHeight: '56px', // CHK001: Touch-friendly height
                fontSize: '16px',
                borderRadius: '8px',
                cursor: 'pointer',
                backgroundColor: location.pathname === item.path ? 'rgba(0, 136, 204, 0.1)' : 'transparent',
                transition: 'background-color 0.2s',
              }}
            >
              <span style={{ fontSize: '24px' }}>{item.icon}</span>
              <span>{item.label}</span>
            </div>
          ))}
        </div>
      )}

      {/* Bottom navigation with hamburger button */}
      <nav className="navigation" style={{ display: 'flex', position: 'relative' }}>
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

        {/* Hamburger menu button */}
        <div
          className="navigation-item"
          onClick={() => setMenuOpen(true)}
          role="button"
          aria-label={t('navigation.menu')}
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              setMenuOpen(true);
            }
          }}
        >
          <div style={{ fontSize: '24px' }}>☰</div>
          <div>{t('navigation.more')}</div>
        </div>
      </nav>

      <style>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
          }
          to {
            transform: translateX(0);
          }
        }
      `}</style>
    </>
  );
};

export default Navigation;
