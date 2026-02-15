import { describe, it, expect, beforeAll, afterEach, afterAll } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import { handlers } from "@/test/handlers";
import { renderWithProviders } from "@/test/utils";
import FeedbackPage from "../index";

const API_BASE = "http://localhost:8000";

const feedbackHandlers = [
  ...handlers,
  http.post(`${API_BASE}/api/v1/feedback`, () =>
    HttpResponse.json({
      id: "f1",
      status: "received",
      created_at: "2026-02-15",
      message: "ok",
    }),
  ),
];

const server = setupServer(...feedbackHandlers);
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("FeedbackPage", () => {
  it("renders feedback form", () => {
    renderWithProviders(<FeedbackPage />);
    expect(
      screen.getByRole("heading", { name: /feedback/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /send/i })).toBeInTheDocument();
  });

  it("disables submit when empty", () => {
    renderWithProviders(<FeedbackPage />);
    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
  });

  it("enables submit when text entered", async () => {
    renderWithProviders(<FeedbackPage />);
    await userEvent.type(screen.getByRole("textbox"), "Great app!");
    expect(screen.getByRole("button", { name: /send/i })).toBeEnabled();
  });
});
