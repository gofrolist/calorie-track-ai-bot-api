import React from 'react';
import { useTranslation } from 'react-i18next';

export const Goals: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div style={{ padding: 16 }}>
      <h1>{t('goals.title')}</h1>
      <p>{t('goals.empty')}</p>
    </div>
  );
};
