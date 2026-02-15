import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/utils";
import { PeriodSelector } from "../PeriodSelector";

describe("PeriodSelector", () => {
  it("renders period options", () => {
    renderWithProviders(<PeriodSelector selected={7} onChange={vi.fn()} />);
    expect(screen.getByText(/7/)).toBeInTheDocument();
    expect(screen.getByText(/30/)).toBeInTheDocument();
    expect(screen.getByText(/90/)).toBeInTheDocument();
  });

  it("calls onChange when option clicked", async () => {
    const onChange = vi.fn();
    renderWithProviders(<PeriodSelector selected={7} onChange={onChange} />);
    await userEvent.click(screen.getByText(/30/));
    expect(onChange).toHaveBeenCalledWith(30);
  });

  it("highlights selected period", () => {
    renderWithProviders(<PeriodSelector selected={30} onChange={vi.fn()} />);
    const selected = screen.getByText(/30/).closest("button");
    expect(selected).toHaveAttribute("aria-pressed", "true");
  });
});
