import React from 'react';
import { createRoot } from 'react-dom/client';
import { init } from '@telegram-apps/sdk';
import App from './app';
import './i18n';

init();

const root = createRoot(document.getElementById('root')!);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
