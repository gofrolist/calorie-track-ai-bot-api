# Calorie Track AI - Telegram Mini App

A modern, mobile-first Telegram Mini App for calorie tracking with AI-powered food recognition. Built with React, TypeScript, and Vite, featuring real-time meal tracking, goal setting, and comprehensive statistics.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- npm or yarn
- Backend API running (see main project README)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd calorie-track-ai-bot-api/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:5173`

## 📱 Features

### Core Functionality
- **Today View**: Real-time meal tracking with daily summaries
- **Meal Details**: Edit and correct AI-estimated calories and macros
- **Statistics**: Weekly and monthly progress charts
- **Goals**: Set and track daily calorie targets
- **Share**: Share progress via Telegram Stories
- **Internationalization**: English and Russian support

### User Experience
- **Mobile-First**: Optimized for Telegram's mobile interface
- **Dark Mode**: Automatic theme detection from Telegram
- **Accessibility**: Full keyboard navigation and screen reader support
- **Performance**: Fast loading with skeleton screens and error boundaries
- **Offline Support**: Graceful handling of network issues

## 🛠️ Development

### Available Scripts
```bash
# Development
npm run dev              # Start development server with hot reload
npm run dev:host         # Start dev server accessible from network

# Building
npm run build            # Build for production
npm run build:analyze    # Build with bundle analysis
npm run preview          # Preview production build locally

# Testing
npm run test             # Run unit tests
npm run test:watch       # Run tests in watch mode
npm run test:e2e         # Run end-to-end tests
npm run test:e2e:ui      # Run E2E tests with UI

# Code Quality
npm run lint             # Run ESLint
npm run lint:fix         # Fix ESLint issues
npm run type-check       # Run TypeScript type checking
npm run format           # Format code with Prettier

# Utilities
npm run clean            # Clean build artifacts
npm run generate:types   # Generate TypeScript types from OpenAPI
```

### Project Structure
```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ErrorBoundary.tsx
│   │   ├── Loading.tsx
│   │   └── share.tsx
│   ├── pages/              # Route components
│   │   ├── today.tsx
│   │   ├── meal-detail.tsx
│   │   ├── stats.tsx
│   │   └── goals.tsx
│   ├── services/           # API and external services
│   │   └── api.ts
│   ├── i18n/              # Internationalization
│   │   └── index.ts
│   ├── tests/             # Test files
│   │   ├── contracts/
│   │   └── i18n.test.ts
│   ├── app.tsx            # Main app component
│   ├── main.tsx           # App entry point
│   └── config.ts          # Configuration
├── tests/
│   └── e2e/               # End-to-end tests
├── docs/                  # Documentation
├── public/                # Static assets
└── dist/                  # Build output
```

### Configuration

#### Environment Variables
```bash
# .env.local
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Calorie Track AI
VITE_APP_VERSION=1.0.0
```

#### Telegram WebApp Integration
The app automatically detects and integrates with Telegram's WebApp API:
- Theme detection (light/dark mode)
- User data from initData
- Haptic feedback
- Share functionality

## 🧪 Testing

### Unit Tests
```bash
npm run test
```
Tests cover:
- Component rendering and behavior
- API service functions
- Internationalization
- Utility functions

### End-to-End Tests
```bash
npm run test:e2e
```
E2E tests cover:
- User workflows (onboarding, meal tracking, goal setting)
- Navigation between pages
- Error handling scenarios
- Accessibility features

### Test Data
Mock data is available in `tests/fixtures/` for consistent testing.

## 🎨 Styling

### CSS Architecture
- **CSS Variables**: Telegram theme integration
- **Mobile-First**: Responsive design patterns
- **Component-Scoped**: Modular styling approach
- **Dark Mode**: Automatic theme switching

### Theme Integration
```css
:root {
  --tg-bg-color: var(--tg-theme-bg-color, #ffffff);
  --tg-text-color: var(--tg-theme-text-color, #000000);
  --tg-button-color: var(--tg-theme-button-color, #007aff);
  --tg-button-text-color: var(--tg-theme-button-text-color, #ffffff);
}
```

## 🌐 Internationalization

### Supported Languages
- English (en)
- Russian (ru)

### Adding Translations
```typescript
// src/i18n/index.ts
const resources = {
  en: {
    translation: {
      // English translations
    }
  },
  ru: {
    translation: {
      // Russian translations
    }
  }
};
```

### Usage
```typescript
import { useTranslation } from 'react-i18next';

const MyComponent = () => {
  const { t } = useTranslation();
  return <h1>{t('common.title')}</h1>;
};
```

## 🚀 Deployment

### Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

### Manual Deployment
```bash
# Build the app
npm run build

# Upload dist/ folder to your hosting provider
# Ensure proper cache headers for static assets
```

### Environment Configuration
Set these environment variables in your deployment platform:

```bash
VITE_API_BASE_URL=https://your-api-domain.com
VITE_APP_NAME=Calorie Track AI
```

### Performance Optimization
- **Code Splitting**: Automatic route-based splitting
- **Tree Shaking**: Unused code elimination
- **Compression**: Gzip/Brotli compression
- **Caching**: Aggressive caching for static assets
- **CDN**: Global content delivery

## 📊 Performance

### Lighthouse Scores (Target)
- **Performance**: 90+
- **Accessibility**: 100
- **Best Practices**: 90+
- **SEO**: 90+

### Core Web Vitals
- **FCP**: < 1.8s
- **LCP**: < 2.5s
- **FID**: < 100ms
- **CLS**: < 0.1

### Bundle Size
- **JavaScript**: < 250KB gzipped
- **CSS**: < 50KB gzipped
- **Images**: Optimized WebP format

## 🔧 Troubleshooting

### Common Issues

#### Telegram WebApp Not Loading
```bash
# Check if running in Telegram environment
console.log(window.Telegram?.WebApp);
```

#### API Connection Issues
```bash
# Verify API URL configuration
echo $VITE_API_BASE_URL
```

#### Build Failures
```bash
# Clear cache and reinstall
npm run clean
rm -rf node_modules package-lock.json
npm install
```

### Debug Mode
```bash
# Enable debug logging
VITE_DEBUG=true npm run dev
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run quality checks
5. Submit a pull request

### Code Standards
- TypeScript strict mode
- ESLint + Prettier configuration
- Conventional commits
- Test coverage > 80%

### Pull Request Checklist
- [ ] Tests pass
- [ ] No linting errors
- [ ] TypeScript compilation succeeds
- [ ] Performance impact assessed
- [ ] Accessibility verified

## 📚 Documentation

- [Performance & Accessibility Guide](docs/performance-accessibility.md)
- [E2E Testing Guide](docs/e2e-testing-guide.md)
- [API Documentation](../backend/specs/openapi.yaml)

## 📄 License

This project is part of the Calorie Track AI Bot system. See the main project README for license information.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing GitHub issues
3. Create a new issue with detailed information

---

Built with ❤️ for healthy living and accurate calorie tracking.
