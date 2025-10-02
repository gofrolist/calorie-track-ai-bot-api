# Infinite Loop Prevention & Detection

## Overview

This document describes the strategies implemented to prevent and detect infinite re-render loops in the React frontend application.

## Problem

React applications can experience infinite loops when:
1. **useEffect dependencies cause circular updates**: Effect triggers state update → re-render → effect runs again
2. **New objects created on every render**: Date objects, arrays, objects passed to hooks create new references
3. **Callback dependencies missing**: useCallback without proper deps recreates functions unnecessarily
4. **Cascading state updates**: One state update triggers another in a cycle

## Prevention Strategies

### 1. ESLint Configuration (`eslint.config.js`)

```javascript
rules: {
  ...reactHooks.configs.recommended.rules,
  'react-hooks/exhaustive-deps': 'warn', // Explicitly warn about missing deps
  // ... other rules
}
```

**What it catches:**
- Missing dependencies in useEffect
- Missing dependencies in useCallback/useMemo
- Unnecessary dependencies

**Limitations:**
- Won't catch infinite loops caused by recreating object references
- Only warns, doesn't enforce

### 2. Memoization Patterns

#### ✅ **Good: Memoize Date Objects**
```typescript
// In Meals.tsx
const calendarDates = useMemo(() => {
  const endDate = new Date();
  const startDate = new Date();
  startDate.setMonth(startDate.getMonth() - 1);
  return { startDate, endDate };
}, []); // Empty deps - only create once

const { calendarData } = useMealsCalendar(
  calendarDates.startDate,
  calendarDates.endDate
);
```

#### ❌ **Bad: Creating Dates on Every Render**
```typescript
// DON'T DO THIS - creates new Date objects on every render
const calendarStartDate = new Date();
calendarStartDate.setMonth(calendarStartDate.getMonth() - 1);
const { calendarData } = useMealsCalendar(calendarStartDate, new Date());
```

### 3. useEffect Dependency Management

#### ✅ **Good: Direct Dependencies**
```typescript
// In useMeals.ts
const fetchCalendar = useCallback(async () => {
  const startStr = startDate.toISOString().split('T')[0];
  const endStr = endDate.toISOString().split('T')[0];
  const response = await getMealsCalendar(startStr, endStr);
  setCalendarData(response.dates);
}, [startDate, endDate]);

useEffect(() => {
  fetchCalendar();
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [startDate, endDate]); // Depend on actual values, not callback
```

#### ❌ **Bad: Callback as Dependency**
```typescript
// DON'T DO THIS - fetchCalendar recreates when deps change
useEffect(() => {
  fetchCalendar();
}, [fetchCalendar]); // This creates infinite loop!
```

## Detection Strategies

### 1. E2E Tests (`infinite-loop-detection.desktop.spec.ts`)

**Test Coverage:**
- Monitors all API requests during page load
- Detects duplicate calls to same endpoint
- Tests all major pages (Meals, Stats, Goals)
- Tests user interactions (calendar, editing)
- Monitors component re-render counts

**Example Test:**
```typescript
test('should not have infinite loop on Meals page', async ({ page }) => {
  const result = await detectInfiniteLoop(page, {
    navigationUrl: 'http://localhost:3000/',
    maxAllowedCalls: 3, // Alert if same API called >3 times
    monitorDuration: 4000, // Monitor for 4 seconds
  });

  expect(result.infiniteLoopDetected).toBe(false);
});
```

**What it detects:**
- API endpoints called excessively (>3 times in 4 seconds)
- Infinite loops in any page load scenario
- Loops triggered by user interactions

**Exclusions:**
- `/api/v1/logs` - Expected to be called multiple times during init
- `/api/v1/config` - Expected for multi-stage configuration

### 2. Network Monitoring in E2E Tests

```typescript
const apiCalls = new Map<string, number>();

page.on('request', (request) => {
  const url = request.url();
  if (/\/api\/v1\//.test(url)) {
    const normalizedUrl = url.split('?')[0];
    const count = apiCalls.get(normalizedUrl) || 0;
    apiCalls.set(normalizedUrl, count + 1);
  }
});

// ... perform actions ...

for (const [url, count] of apiCalls.entries()) {
  expect(count).toBeLessThanOrEqual(maxAllowed);
}
```

### 3. Component Re-Render Detection

```typescript
test('should not have excessive re-renders when component mounts', async ({ page }) => {
  await page.addInitScript(() => {
    (window as any).__renderCount__ = 0;
    // Inject render counter
  });

  // React in dev mode renders twice (StrictMode)
  // In production, expect <= 2 renders
  const renderCount = await page.evaluate(() => (window as any).__renderCount__);
  expect(renderCount).toBeLessThanOrEqual(10);
});
```

## Common Patterns & Solutions

### Pattern 1: Date Objects in Hook Dependencies

**Problem:**
```typescript
const { data } = useCustomHook(new Date(), new Date());
```

**Solution:**
```typescript
const dates = useMemo(() => ({
  start: new Date(),
  end: new Date()
}), []);
const { data } = useCustomHook(dates.start, dates.end);
```

### Pattern 2: useEffect with Callback Dependency

**Problem:**
```typescript
const fetchData = useCallback(() => {
  // ... fetch logic
}, [dependency]);

useEffect(() => {
  fetchData();
}, [fetchData]); // ❌ Infinite loop!
```

**Solution:**
```typescript
const fetchData = useCallback(() => {
  // ... fetch logic
}, [dependency]);

useEffect(() => {
  fetchData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [dependency]); // ✅ Direct dependency
```

### Pattern 3: State Updates in Effects

**Problem:**
```typescript
useEffect(() => {
  setState(computeValue(state)); // ❌ Reads and writes same state
}, [state]);
```

**Solution:**
```typescript
useEffect(() => {
  setState(prev => computeValue(prev)); // ✅ Use functional update
}, []); // Or proper dependencies
```

## Testing Checklist

When implementing new features:

- [ ] Run ESLint to check for hook dependency warnings
- [ ] Test page load doesn't cause excessive API calls
- [ ] Test user interactions don't trigger loops
- [ ] Check Network tab in DevTools for repeated requests
- [ ] Run infinite loop detection E2E tests
- [ ] Verify no excessive re-renders in React DevTools Profiler

## Automated Detection

### In CI/CD:

1. **ESLint**: Catches missing dependencies
   ```bash
   npm run lint
   ```

2. **E2E Tests**: Detects runtime loops
   ```bash
   npm run test:e2e infinite-loop-detection
   ```

3. **Manual Testing**: Check browser console
   - Look for repeated API Request Debug logs
   - Monitor Network tab for duplicate requests
   - Use React DevTools Profiler to count renders

## Known Safe Patterns

These patterns are safe and won't cause infinite loops:

```typescript
// 1. Empty dependency array (run once on mount)
useEffect(() => {
  initializeApp();
}, []);

// 2. Primitive dependencies (strings, numbers, booleans)
useEffect(() => {
  fetchData(userId);
}, [userId]);

// 3. Memoized objects
const options = useMemo(() => ({ foo: 'bar' }), []);
useEffect(() => {
  doSomething(options);
}, [options]);

// 4. Stable callback references
const handleClick = useCallback(() => {
  doSomething();
}, []); // No dependencies = stable reference
```

## Debugging Infinite Loops

### Step 1: Identify the Loop
- Open browser DevTools → Console
- Look for repeated log messages
- Check Network tab for duplicate requests

### Step 2: Find the Source
- Use React DevTools Profiler
- Check which component is re-rendering
- Look at the "Why did this render?" information

### Step 3: Fix the Root Cause
- Check useEffect dependencies
- Look for objects/arrays created in render
- Verify useCallback/useMemo usage
- Ensure state updates don't trigger themselves

### Step 4: Verify the Fix
```bash
# Run lint
npm run lint

# Run infinite loop detection tests
npm run test:e2e infinite-loop-detection

# Manual browser test
npm run dev
# Open DevTools → Console & Network tab
```

## References

- [React Hooks Documentation](https://react.dev/reference/react)
- [ESLint Plugin React Hooks](https://www.npmjs.com/package/eslint-plugin-react-hooks)
- [React DevTools Profiler](https://react.dev/learn/react-developer-tools)
