import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      today: {
        title: 'Today',
        empty: 'No meals yet. Send a photo to the bot to start.',
      },
    },
  },
  ru: {
    translation: {
      today: {
        title: 'Сегодня',
        empty: 'Пока нет приёмов пищи. Отправьте фото боту, чтобы начать.',
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
