import { DayPicker } from "react-day-picker";
import type { MealCalendarDay } from "@/api/model";

interface CalendarPickerProps {
  selected: Date;
  onSelect: (date: Date) => void;
  calendarData?: MealCalendarDay[];
}

export function CalendarPicker({
  selected,
  onSelect,
  calendarData,
}: CalendarPickerProps) {
  const modifiers = calendarData?.reduce<Record<string, Date[]>>((acc, day) => {
    const date = new Date(day.meal_date);
    if (day.meal_count > 0) {
      acc.hasMeals = [...(acc.hasMeals ?? []), date];
    }
    return acc;
  }, {});

  return (
    <div className="flex justify-center">
      <DayPicker
        mode="single"
        selected={selected}
        onSelect={(date) => date && onSelect(date)}
        modifiers={modifiers}
        modifiersClassNames={{ hasMeals: "font-bold text-tg-button" }}
        className="text-tg-text"
      />
    </div>
  );
}
