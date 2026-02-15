import { describe, it, expect } from "vitest";

describe("test infrastructure", () => {
  it("vitest runs", () => {
    expect(1 + 1).toBe(2);
  });

  it("telegram mock is available", () => {
    expect(window.Telegram?.WebApp?.initDataUnsafe?.user?.id).toBe(123456);
  });
});
