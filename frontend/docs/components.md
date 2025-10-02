# Frontend Components Documentation

This document describes the React components used in the Calorie Track AI Bot frontend application.

## Core Components

### MealCard
**Location**: `src/components/MealCard.tsx`

A reusable component for displaying individual meal information with photos and macronutrients.

**Props**:
- `meal`: MealWithPhotos object containing meal data
- `onEdit`: Function called when edit button is clicked
- `onDelete`: Function called when delete button is clicked
- `isExpanded`: Boolean to control expanded/collapsed state
- `onToggleExpand`: Function to toggle expansion state

**Features**:
- Displays meal description, calories, and macronutrients
- Shows photo carousel with thumbnail and full-size images
- Expandable/collapsible design for mobile optimization
- Edit and delete action buttons
- Responsive design for different screen sizes

### PhotoCarousel
**Location**: `src/components/PhotoCarousel.tsx`

A carousel component for displaying multiple meal photos with navigation controls.

**Props**:
- `photos`: Array of PhotoInfo objects
- `initialSlide`: Index of the initial slide to display
- `onSlideChange`: Callback function when slide changes

**Features**:
- Swiper.js integration for smooth touch/swipe navigation
- Thumbnail navigation dots
- Full-screen image display
- Keyboard navigation support
- Responsive design

### CalendarPicker
**Location**: `src/components/CalendarPicker.tsx`

A date picker component for selecting meal dates and date ranges.

**Props**:
- `selectedDate`: Currently selected date
- `onDateSelect`: Function called when a date is selected
- `onRangeSelect`: Function called when a date range is selected
- `mode`: 'single' or 'range' selection mode

**Features**:
- react-day-picker integration
- Single date and date range selection
- Month/year navigation
- Custom styling for Telegram Mini App theme
- Accessibility support

### MealEditor
**Location**: `src/components/MealEditor.tsx`

A modal component for editing meal details including description and macronutrients.

**Props**:
- `meal`: MealWithPhotos object to edit
- `isOpen`: Boolean to control modal visibility
- `onClose`: Function called when modal is closed
- `onSave`: Function called when changes are saved

**Features**:
- Form validation for macronutrient values
- Real-time calorie calculation
- Optimistic UI updates
- Error handling and validation messages

## Page Components

### Meals
**Location**: `src/pages/Meals.tsx`

The main page component for displaying and managing meals.

**Features**:
- Meal list with filtering and pagination
- Calendar integration for date-based filtering
- Meal creation, editing, and deletion
- Responsive layout for mobile and desktop
- Integration with backend API

**State Management**:
- Uses `useMeals` hook for data fetching
- Uses `useMealsCalendar` hook for calendar data
- Local state for UI interactions (modals, filters)

## Utility Components

### SafeAreaWrapper
**Location**: `src/components/SafeAreaWrapper.tsx`

A wrapper component that handles safe area insets for mobile devices.

**Props**:
- `children`: React children to wrap
- `className`: Additional CSS classes

**Features**:
- CSS environment variable support for safe areas
- Fallback for devices without safe area support
- Customizable padding and margins

### Loading
**Location**: `src/components/Loading.tsx`

A loading indicator component for async operations.

**Props**:
- `size`: 'small', 'medium', or 'large'
- `text`: Optional loading text

**Features**:
- Spinner animation
- Customizable size and text
- Accessible loading states

### ErrorBoundary
**Location**: `src/components/ErrorBoundary.tsx`

An error boundary component for catching and handling React errors.

**Props**:
- `children`: React children to wrap
- `fallback`: Custom fallback component

**Features**:
- Catches JavaScript errors in component tree
- Displays fallback UI
- Error reporting and logging

## Hooks

### useMeals
**Location**: `src/hooks/useMeals.ts`

A custom hook for managing meal data and operations.

**Returns**:
- `meals`: Array of meals
- `loading`: Loading state
- `error`: Error state
- `createMeal`: Function to create a new meal
- `updateMeal`: Function to update an existing meal
- `deleteMeal`: Function to delete a meal
- `refetch`: Function to refetch data

**Features**:
- Optimistic updates for better UX
- Error handling and retry logic
- Caching and state management

### useMealsCalendar
**Location**: `src/hooks/useMeals.ts`

A custom hook for managing calendar meal data.

**Returns**:
- `calendarData`: Calendar summary data
- `loading`: Loading state
- `error`: Error state
- `refetch`: Function to refetch data

**Features**:
- Date range-based data fetching
- Caching for performance
- Error handling

## Styling

### CSS Modules
Components use CSS modules for scoped styling:
- `SafeAreaWrapper.module.css`
- Component-specific styles in respective files

### Theme Integration
Components integrate with Telegram Mini App theming:
- Light/dark mode support
- Custom color schemes
- Responsive design patterns

## Testing

### Component Tests
Each component has corresponding test files:
- `MealCard.test.tsx`
- `PhotoCarousel.test.tsx`
- `CalendarPicker.test.tsx`
- `MealEditor.test.tsx`

### E2E Tests
End-to-end tests cover user workflows:
- `meal-editing-flow.spec.ts`
- `meal-deletion-flow.spec.ts`
- `calendar-filtering.spec.ts`

## Performance Considerations

### Image Optimization
- Lazy loading for photos
- Thumbnail vs full-size image selection
- Presigned URL caching

### State Management
- Optimistic updates for better perceived performance
- Efficient re-rendering with React.memo
- Proper dependency arrays in useEffect

### Bundle Optimization
- Code splitting for large components
- Dynamic imports for heavy libraries
- Tree shaking for unused code
