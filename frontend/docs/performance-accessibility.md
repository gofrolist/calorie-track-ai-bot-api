# Performance & Accessibility Guidelines

## Lighthouse Performance Targets

### Mobile Performance Goals
- **First Contentful Paint (FCP)**: < 1.8s
- **Largest Contentful Paint (LCP)**: < 2.5s
- **First Input Delay (FID)**: < 100ms
- **Cumulative Layout Shift (CLS)**: < 0.1
- **Speed Index**: < 3.4s
- **Time to Interactive (TTI)**: < 3.8s

### Accessibility Goals
- **Accessibility Score**: 100/100
- **Color Contrast**: AA compliance (4.5:1 for normal text, 3:1 for large text)
- **Keyboard Navigation**: Full support
- **Screen Reader**: Compatible with major screen readers
- **Focus Management**: Visible and logical focus order

## Performance Optimizations Implemented

### 1. Code Splitting & Lazy Loading
```typescript
// Route-based code splitting
const Today = lazy(() => import('./pages/today'));
const Stats = lazy(() => import('./pages/stats'));
const Goals = lazy(() => import('./pages/goals'));
const MealDetail = lazy(() => import('./pages/meal-detail'));
```

### 2. Image Optimization
- Use WebP format when supported
- Implement responsive images with srcset
- Lazy load images below the fold
- Optimize image sizes for mobile devices

### 3. Bundle Optimization
- Tree shaking to eliminate unused code
- Minification and compression
- Vendor chunk splitting
- Dynamic imports for heavy dependencies

### 4. Caching Strategy
- Service worker for offline functionality
- HTTP caching headers
- Local storage for user preferences
- Memory caching for API responses

### 5. Network Optimization
- API request batching
- Parallel data fetching
- Request deduplication
- Optimistic updates

## Accessibility Features Implemented

### 1. Semantic HTML
```html
<!-- Proper heading hierarchy -->
<h1>Page Title</h1>
<h2>Section Title</h2>
<h3>Subsection Title</h3>

<!-- Semantic elements -->
<main role="main">
<nav role="navigation">
<section aria-labelledby="section-heading">
```

### 2. ARIA Labels and Roles
```typescript
// Progress bars
<div
  className="progress-bar"
  role="progressbar"
  aria-valuenow={percentage}
  aria-valuemin={0}
  aria-valuemax={100}
  aria-label={`Progress: ${percentage}%`}
>

// Form inputs
<input
  type="number"
  aria-label="Daily Calorie Goal"
  aria-describedby="goal-help"
  aria-invalid={hasError}
/>
```

### 3. Keyboard Navigation
- Tab order follows logical flow
- Skip links for main content
- Keyboard shortcuts for common actions
- Focus indicators visible and consistent

### 4. Color and Contrast
- High contrast mode support
- Color is not the only indicator of information
- Sufficient contrast ratios (4.5:1 minimum)
- Dark mode compatibility

### 5. Screen Reader Support
- Descriptive alt text for images
- Live regions for dynamic content updates
- Proper form labels and descriptions
- Announcements for state changes

## Performance Testing Checklist

### Pre-deployment Tests
- [ ] Lighthouse audit (mobile) > 90
- [ ] Core Web Vitals pass
- [ ] Bundle size analysis
- [ ] Network waterfall analysis
- [ ] Memory leak detection

### Accessibility Testing
- [ ] Lighthouse accessibility audit = 100
- [ ] Keyboard-only navigation test
- [ ] Screen reader testing (NVDA, JAWS, VoiceOver)
- [ ] Color contrast validation
- [ ] Focus management verification

## Monitoring and Metrics

### Performance Monitoring
```typescript
// Web Vitals tracking
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

getCLS(console.log);
getFID(console.log);
getFCP(console.log);
getLCP(console.log);
getTTFB(console.log);
```

### Error Tracking
- JavaScript error monitoring
- API error tracking
- Performance regression detection
- User experience metrics

## Mobile-Specific Optimizations

### 1. Touch Interactions
- Minimum 44px touch targets
- Touch feedback for interactions
- Swipe gestures where appropriate
- Prevent accidental double-taps

### 2. Viewport Optimization
- Proper viewport meta tag
- Responsive design for all screen sizes
- Safe area handling for notched devices
- Orientation change handling

### 3. Network Considerations
- Offline functionality
- Progressive loading
- Data usage optimization
- 3G network simulation testing

## Implementation Examples

### Optimized Component Loading
```typescript
const LazyComponent = lazy(() => import('./HeavyComponent'));

const App = () => (
  <Suspense fallback={<LoadingSkeleton />}>
    <LazyComponent />
  </Suspense>
);
```

### Efficient Data Fetching
```typescript
// Parallel data fetching
const [todayData, goalData] = await Promise.allSettled([
  dailySummaryApi.getTodayData(today),
  goalsApi.getGoal(),
]);

// Request deduplication
const cache = new Map();
const fetchWithCache = async (key, fetcher) => {
  if (cache.has(key)) return cache.get(key);
  const result = await fetcher();
  cache.set(key, result);
  return result;
};
```

### Accessibility Helper Functions
```typescript
// Announce changes to screen readers
const announceToScreenReader = (message: string) => {
  const announcement = document.createElement('div');
  announcement.setAttribute('aria-live', 'polite');
  announcement.setAttribute('aria-atomic', 'true');
  announcement.className = 'sr-only';
  announcement.textContent = message;
  document.body.appendChild(announcement);
  setTimeout(() => document.body.removeChild(announcement), 1000);
};

// Focus management
const trapFocus = (element: HTMLElement) => {
  const focusableElements = element.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  // Focus trap implementation
};
```

## Continuous Improvement

### Regular Audits
- Weekly Lighthouse audits
- Monthly accessibility reviews
- Quarterly performance regression tests
- User feedback integration

### Performance Budgets
- JavaScript bundle: < 250KB gzipped
- CSS bundle: < 50KB gzipped
- Images: < 100KB per image
- Fonts: < 100KB total

### Monitoring Dashboard
- Real-time performance metrics
- Error rate tracking
- User experience scores
- Accessibility compliance status

## Resources

### Tools
- [Lighthouse](https://developers.google.com/web/tools/lighthouse)
- [Web Vitals](https://web.dev/vitals/)
- [axe-core](https://github.com/deque/axe-core)
- [Pa11y](https://pa11y.org/)

### Guidelines
- [WCAG 2.1 AA](https://www.w3.org/WAI/WCAG21/quickref/)
- [Web Performance Best Practices](https://web.dev/fast/)
- [Mobile Web Best Practices](https://developers.google.com/web/fundamentals/design-and-ux/responsive)

### Testing
- [Chrome DevTools](https://developers.google.com/web/tools/chrome-devtools)
- [WebPageTest](https://www.webpagetest.org/)
- [Accessibility Insights](https://accessibilityinsights.io/)
