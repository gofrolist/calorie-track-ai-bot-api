import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './app';
import './i18n';

// TODO: Initialize Telegram WebApp SDK when needed

const root = createRoot(document.getElementById('root')!);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
