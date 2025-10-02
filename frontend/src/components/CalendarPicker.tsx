/**
 * CalendarPicker Component
 * Feature: 003-update-logic-for
 * Task: T047
 *
 * Date picker for selecting meal history dates
 * - Shows dates with meal indicators
 * - Disables future dates and dates >1 year old
 * - Mobile-optimized with touch-friendly targets
 */

import React from 'react';
import { DayPicker } from 'react-day-picker';
import 'react-day-picker/dist/style.css';

interface CalendarPickerProps {
  selectedDate: Date;
  onDateChange: (date: Date) => void;
  datesWithMeals?: Date[];
  className?: string;
}

export const CalendarPicker: React.FC<CalendarPickerProps> = ({
  selectedDate,
  onDateChange,
  datesWithMeals = [],
  className = '',
}) => {
  const today = new Date();
  const oneYearAgo = new Date();
  oneYearAgo.setFullYear(today.getFullYear() - 1);

  // Create modifiers for dates with meals
  const modifiers = {
    hasData: datesWithMeals,
  };

  const modifiersStyles = {
    hasData: {
      fontWeight: 'bold',
      textDecoration: 'underline',
    },
  };

  const handleDayClick = (day: Date | undefined) => {
    if (day) {
      onDateChange(day);
    }
  };

  return (
    <div className={`calendar-picker-component ${className}`}>
      <h3>Select Date</h3>
      <DayPicker
        mode="single"
        selected={selectedDate}
        onSelect={handleDayClick}
        disabled={(date) =>
          date > today || date < oneYearAgo
        }
        modifiers={modifiers}
        modifiersStyles={modifiersStyles}
        className="mobile-optimized-calendar"
        showOutsideDays={false}
        aria-label="Select date for meal history"
      />
      <style>{`
        .mobile-optimized-calendar {
          max-width: 100%;
          font-size: 14px;
        }
        .mobile-optimized-calendar button {
          min-width: 44px;
          min-height: 44px;
        }
        .rdp-day_selected {
          background-color: var(--tg-theme-button-color, #007aff);
          color: var(--tg-theme-button-text-color, white);
        }
        .rdp-day_disabled {
          opacity: 0.3;
          cursor: not-allowed;
        }

        .calendar-day {
          position: relative;
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .day-button {
          min-width: 44px;
          min-height: 44px;
          border: none;
          background: transparent;
          cursor: pointer;
          border-radius: 8px;
          font-size: 14px;
        }

        .day-button.selected {
          background-color: var(--tg-theme-button-color, #007aff);
          color: var(--tg-theme-button-text-color, white);
        }

        .day-button.disabled {
          opacity: 0.3;
          cursor: not-allowed;
        }

        .meal-indicator {
          position: absolute;
          bottom: 2px;
          font-size: 12px;
          color: var(--tg-theme-button-color, #007aff);
        }
      `}</style>
    </div>
  );
};

export default CalendarPicker;
