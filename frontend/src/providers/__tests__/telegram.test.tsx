import { describe, it, expect } from "vitest";
import { renderHook } from "@testing-library/react";
import { TelegramProvider, useTelegram } from "../telegram";

function wrapper({ children }: { children: React.ReactNode }) {
  return <TelegramProvider>{children}</TelegramProvider>;
}

describe("TelegramProvider", () => {
  it("provides user from Telegram WebApp", () => {
    const { result } = renderHook(() => useTelegram(), { wrapper });
    expect(result.current.user?.id).toBe(123456);
  });

  it("provides theme from Telegram colorScheme", () => {
    const { result } = renderHook(() => useTelegram(), { wrapper });
    expect(result.current.theme).toBe("light");
  });

  it("provides language from Telegram user data", () => {
    const { result } = renderHook(() => useTelegram(), { wrapper });
    expect(result.current.language).toBe("en");
  });
});
