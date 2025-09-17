import React from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export const MealDetail: React.FC = () => {
  const { id } = useParams();
  const { t } = useTranslation();
  return (
    <div style={{ padding: 16 }}>
      <h1>{t('mealDetail.title')}</h1>
      <p>
        {t('mealDetail.id')}: {id}
      </p>
    </div>
  );
};
