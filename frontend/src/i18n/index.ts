import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      today: {
        title: 'Today',
        empty: 'No meals yet. Send a photo to the bot to start.',
        total: 'Total: {{calories}} kcal',
        loading: 'Loading...',
        error: 'Failed to load meals',
        mealTypes: {
          breakfast: 'Breakfast',
          lunch: 'Lunch',
          dinner: 'Dinner',
          snack: 'Snack',
        },
      },
      mealDetail: {
        title: 'Meal Detail',
        id: 'ID',
      },
      stats: {
        title: 'Statistics',
        empty: 'No statistics yet.',
      },
      goals: {
        title: 'Goals',
        empty: 'No goals set yet.',
      },
    },
  },
  ru: {
    translation: {
      today: {
        title: 'Сегодня',
        empty: 'Пока нет приёмов пищи. Отправьте фото боту, чтобы начать.',
        total: 'Всего: {{calories}} ккал',
        loading: 'Загрузка...',
        error: 'Не удалось загрузить приёмы пищи',
        mealTypes: {
          breakfast: 'Завтрак',
          lunch: 'Обед',
          dinner: 'Ужин',
          snack: 'Перекус',
        },
      },
      mealDetail: {
        title: 'Приём пищи',
        id: 'Идентификатор',
      },
      stats: {
        title: 'Статистика',
        empty: 'Пока нет статистики.',
      },
      goals: {
        title: 'Цели',
        empty: 'Цели не заданы.',
      },
    },
  },
};

i18n.use(initReactI18next).init({
  resources,
  lng: 'en',
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
});

export default i18n;
