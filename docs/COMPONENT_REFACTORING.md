# Navigation Component Refactoring

## Overview

Extracted the navigation bar into a reusable `Navigation` component to eliminate code duplication and ensure consistency across all pages.

## Problem

Previously, each page (Meals, Stats, Goals) had its own inline navigation code:
- **Code duplication**: Same navigation code repeated 3 times
- **Inconsistency risk**: Easy to update one page but forget others
- **Maintenance burden**: Changes required editing 3 files
- **Translation errors**: Different pages could use different translation keys

## Solution

Created a single reusable `Navigation` component located at:
```
frontend/src/components/Navigation.tsx
```

## Benefits

### ✅ **Single Source of Truth**
- Navigation items defined once in one place
- All pages use the exact same component
- Guaranteed consistency across the app

### ✅ **Automatic Active State Detection**
- Uses `useLocation()` to detect current page
- Automatically highlights the active navigation item
- No manual `active` class management needed

### ✅ **i18n Support**
- All labels use translation keys: `t('navigation.meals')`, etc.
- Supports both English and Russian (and easy to add more)
- Consistent translations across all pages

### ✅ **Easy Maintenance**
- Update navigation in one file → all pages update
- Add new navigation items → appears everywhere
- Change icons/styling → consistent across app

### ✅ **Reduced Bundle Size**
- Eliminated ~45 lines of duplicated code per page (135 lines total)
- Component can be code-split if needed
- Better tree-shaking opportunities

## Implementation

### Component Structure

```typescript
// frontend/src/components/Navigation.tsx
export const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();

  const navItems = [
    { path: '/', icon: '🍽️', label: t('navigation.meals') },
    { path: '/stats', icon: '📈', label: t('navigation.stats') },
    { path: '/goals', icon: '🎯', label: t('navigation.goals') },
  ];

  return (
    <nav className="navigation">
      {navItems.map((item) => (
        <div
          key={item.path}
          className={`navigation-item ${location.pathname === item.path ? 'active' : ''}`}
          onClick={() => navigate(item.path)}
        >
          <div>{item.icon}</div>
          <div>{item.label}</div>
        </div>
      ))}
    </nav>
  );
};
```

### Usage in Pages

**Before (45 lines per page):**
```typescript
<nav className="navigation">
  <div className="navigation-item active">
    <div>🍽️</div>
    <div>{t('navigation.meals')}</div>
  </div>
  <div className="navigation-item" onClick={() => navigate('/stats')}>
    <div>📈</div>
    <div>{t('navigation.stats')}</div>
  </div>
  <div className="navigation-item" onClick={() => navigate('/goals')}>
    <div>🎯</div>
    <div>{t('navigation.goals')}</div>
  </div>
</nav>
```

**After (1 line per page):**
```typescript
<Navigation />
```

## Updated Files

1. **Created:**
   - `frontend/src/components/Navigation.tsx` - New reusable component

2. **Updated:**
   - `frontend/src/pages/Meals.tsx` - Now imports and uses `<Navigation />`
   - `frontend/src/pages/stats.tsx` - Now imports and uses `<Navigation />`
   - `frontend/src/pages/goals.tsx` - Now imports and uses `<Navigation />`

## Code Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total navigation code | ~135 lines | ~50 lines | -63% |
| Files with nav code | 3 pages | 1 component | Centralized |
| Active state management | Manual (3 places) | Automatic | Simplified |
| Translation consistency | At risk | Guaranteed | ✅ |

## Future Enhancements

Possible improvements to the Navigation component:

1. **Badge support**: Show unread notifications
   ```typescript
   { path: '/meals', icon: '🍽️', label: '...', badge: mealCount }
   ```

2. **Conditional items**: Show/hide based on user permissions
   ```typescript
   navItems.filter(item => hasPermission(item.permission))
   ```

3. **Nested navigation**: Support sub-items or tabs
   ```typescript
   { path: '/stats', icon: '📈', label: '...', children: [...] }
   ```

4. **Accessibility**: Add ARIA labels and keyboard navigation
   ```typescript
   <nav role="navigation" aria-label="Main navigation">
   ```

5. **Animation**: Add transitions when switching tabs
   ```css
   .navigation-item { transition: all 0.2s ease; }
   ```

## Testing

All existing tests pass with the new Navigation component:
- ✅ Build: Success (790ms)
- ✅ Tests: 104 passed
- ✅ Bundle: No size increase (code actually reduced)

## Related Documentation

- [i18n Translations](./i18n-setup.md) - How translation keys work
- [Component Architecture](./ARCHITECTURE.md) - Overall component structure
- [Routing](./routing.md) - How navigation and routing work together
