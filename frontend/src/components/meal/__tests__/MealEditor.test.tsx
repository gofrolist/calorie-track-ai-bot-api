import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@/test/utils";
import { MealEditor } from "../MealEditor";

const defaultMeal = {
  description: "Chicken",
  calories: 450,
  protein: 35,
  carbs: 40,
  fats: 12,
};

describe("MealEditor", () => {
  it("renders form fields pre-filled with data", () => {
    renderWithProviders(
      <MealEditor meal={defaultMeal} onSave={vi.fn()} onCancel={vi.fn()} />,
    );
    expect(screen.getByLabelText(/description/i)).toHaveValue("Chicken");
    expect(screen.getByLabelText(/protein/i)).toHaveValue(35);
    expect(screen.getByLabelText(/carbs/i)).toHaveValue(40);
    expect(screen.getByLabelText(/fat/i)).toHaveValue(12);
  });

  it("calls onSave with updated data", async () => {
    const onSave = vi.fn();
    renderWithProviders(
      <MealEditor meal={defaultMeal} onSave={onSave} onCancel={vi.fn()} />,
    );
    const descInput = screen.getByLabelText(/description/i);
    await userEvent.clear(descInput);
    await userEvent.type(descInput, "Updated meal");
    await userEvent.click(screen.getByRole("button", { name: /save/i }));
    expect(onSave).toHaveBeenCalledWith(
      expect.objectContaining({ description: "Updated meal" }),
    );
  });

  it("calls onCancel when cancelled", async () => {
    const onCancel = vi.fn();
    renderWithProviders(
      <MealEditor meal={defaultMeal} onSave={vi.fn()} onCancel={onCancel} />,
    );
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalled();
  });
});
