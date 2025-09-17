import React from 'react';
import { useTranslation } from 'react-i18next';

export const Stats: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div style={{ padding: 16 }}>
      <h1>{t('stats.title')}</h1>
      <p>{t('stats.empty')}</p>
    </div>
  );
};
