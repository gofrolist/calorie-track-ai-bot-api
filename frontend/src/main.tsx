import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./app.css";
import "./i18n";
import { App } from "./app";

// Initialize Telegram WebApp
const webapp = window.Telegram?.WebApp;
if (webapp) {
  webapp.ready();
  webapp.expand();
  webapp.enableClosingConfirmation();
  if (webapp.setHeaderColor) webapp.setHeaderColor("bg_color");
  if (webapp.setBackgroundColor) webapp.setBackgroundColor("bg_color");
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
