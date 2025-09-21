import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './app';
import './i18n';
import './telegram-webapp.css';

// Initialize Telegram WebApp SDK
const initTelegramApp = async () => {
  try {
    // Configure the WebApp appearance
    if (window.Telegram?.WebApp) {
      const webApp = window.Telegram.WebApp;

      // Expand the WebApp to full height
      webApp.expand();

      // Enable closing confirmation
      webApp.enableClosingConfirmation();

      // Set header color to match theme
      webApp.setHeaderColor('#ffffff');

      // Set background color
      webApp.setBackgroundColor('#f8f9fa');

      // Ready signal to Telegram
      webApp.ready();
    }
  } catch (error) {
    console.warn('Failed to initialize Telegram WebApp SDK:', error);
    // Continue without Telegram features for development/testing
  }
};

// Initialize Telegram before rendering the app
initTelegramApp().then(() => {
  const root = createRoot(document.getElementById('root')!);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
});
