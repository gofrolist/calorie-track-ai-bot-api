import { describe, it, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@/test/utils";
import { Navigation } from "../Navigation";

describe("Navigation", () => {
  it("renders three nav items", () => {
    renderWithProviders(<Navigation />);
    expect(screen.getByRole("navigation")).toBeInTheDocument();
    expect(screen.getAllByRole("button")).toHaveLength(3);
  });

  it("renders Meals, Stats, Goals labels", () => {
    renderWithProviders(<Navigation />);
    expect(screen.getByText("Meals")).toBeInTheDocument();
    expect(screen.getByText("Stats")).toBeInTheDocument();
    expect(screen.getByText("Goals")).toBeInTheDocument();
  });

  it("highlights active route", () => {
    renderWithProviders(<Navigation />, { initialRoute: "/stats" });
    const statsButton = screen.getByText("Stats").closest("button");
    expect(statsButton).toHaveAttribute("aria-current", "page");
  });
});
