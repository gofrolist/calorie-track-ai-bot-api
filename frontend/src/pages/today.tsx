import React from 'react';
import { useTranslation } from 'react-i18next';

export const Today: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div style={{ padding: 16 }}>
      <h1>{t('today.title')}</h1>
      <p>{t('today.empty')}</p>
    </div>
  );
};
