# Calorie Track AI Bot - System Architecture

## Overview

The Calorie Track AI Bot is a comprehensive Telegram-based application that uses computer vision to analyze food photos and provide detailed nutritional information. The system consists of multiple components working together to deliver a seamless user experience.

## High-Level Architecture

```mermaid
graph TB
    subgraph "User Layer"
        U[Telegram Users]
        WA[Telegram WebApp]
    end

    subgraph "Frontend Layer"
        FE[React Frontend]
        UI[Modern UI Components]
    end

    subgraph "API Gateway"
        API[FastAPI Backend]
        AUTH[Authentication]
        CORS[CORS Middleware]
    end

    subgraph "AI Processing Layer"
        CV[Computer Vision]
        ML[ML Models]
        QUEUE[Background Queue]
    end

    subgraph "Data Layer"
        DB[(PostgreSQL)]
        REDIS[(Redis Cache)]
        S3[(Tigris Storage)]
    end

    subgraph "Infrastructure"
        FLY[Fly.io Deployment]
        CDN[CDN]
        MONITOR[Monitoring]
    end

    U --> WA
    WA --> FE
    FE --> API
    API --> AUTH
    API --> CORS
    API --> CV
    CV --> ML
    CV --> QUEUE
    API --> DB
    API --> REDIS
    API --> S3
    FLY --> API
    FLY --> FE
    CDN --> FE
    MONITOR --> API
    MONITOR --> FE
```

## Component Architecture

### Frontend Architecture

```mermaid
graph TD
    subgraph "React Frontend"
        APP[App.tsx]
        ROUTER[React Router]
        CONTEXT[Telegram Context]

        subgraph "Pages"
            TODAY[Today Page]
            MEAL[Meal Detail]
            STATS[Stats Page]
            GOALS[Goals Page]
        end

        subgraph "Components"
            ERROR[Error Boundary]
            LOADING[Loading Component]
            SHARE[Share Component]
        end

        subgraph "Services"
            API_SVC[API Service]
            CONFIG[Configuration]
            I18N[Internationalization]
        end

        subgraph "Styling"
            CSS[Telegram WebApp CSS]
            THEMES[Theme System]
            SAFE[Safe Areas]
        end
    end

    APP --> ROUTER
    APP --> CONTEXT
    ROUTER --> TODAY
    ROUTER --> MEAL
    ROUTER --> STATS
    ROUTER --> GOALS
    APP --> ERROR
    APP --> LOADING
    APP --> SHARE
    API_SVC --> CONFIG
    CONFIG --> I18N
    CSS --> THEMES
    THEMES --> SAFE
```

### Backend Architecture

```mermaid
graph TD
    subgraph "FastAPI Backend"
        MAIN[main.py]
        LIFESPAN[Lifespan Manager]

        subgraph "API Routes"
            HEALTH[Health Check]
            AUTH_ROUTE[Auth Routes]
            PHOTOS_ROUTE[Photos Routes]
            ESTIMATES_ROUTE[Estimates Routes]
            MEALS_ROUTE[Meals Routes]
            SUMMARY_ROUTE[Summary Routes]
            GOALS_ROUTE[Goals Routes]
            BOT_ROUTE[Bot Routes]
        end

        subgraph "Services"
            CONFIG_SVC[Config Service]
            DB_SVC[Database Service]
            STORAGE_SVC[Storage Service]
            TELEGRAM_SVC[Telegram Service]
            ESTIMATOR_SVC[Estimator Service]
            QUEUE_SVC[Queue Service]
        end

        subgraph "Workers"
            ESTIMATE_WORKER[Estimate Worker]
        end
    end

    MAIN --> LIFESPAN
    MAIN --> HEALTH
    MAIN --> AUTH_ROUTE
    MAIN --> PHOTOS_ROUTE
    MAIN --> ESTIMATES_ROUTE
    MAIN --> MEALS_ROUTE
    MAIN --> SUMMARY_ROUTE
    MAIN --> GOALS_ROUTE
    MAIN --> BOT_ROUTE

    AUTH_ROUTE --> CONFIG_SVC
    PHOTOS_ROUTE --> STORAGE_SVC
    ESTIMATES_ROUTE --> ESTIMATOR_SVC
    MEALS_ROUTE --> DB_SVC
    SUMMARY_ROUTE --> DB_SVC
    GOALS_ROUTE --> DB_SVC
    BOT_ROUTE --> TELEGRAM_SVC

    ESTIMATOR_SVC --> QUEUE_SVC
    QUEUE_SVC --> ESTIMATE_WORKER
```

## Data Flow Architecture

### Photo Upload and Processing Flow

```mermaid
sequenceDiagram
    participant U as User
    participant WA as Telegram WebApp
    participant FE as Frontend
    participant API as Backend API
    participant S3 as Tigris Storage
    participant Q as Queue
    participant W as Worker
    participant ML as ML Model
    participant DB as Database

    U->>WA: Upload photo
    WA->>FE: Photo file
    FE->>API: POST /api/v1/photos
    API->>S3: Generate presigned URL
    S3-->>API: Upload URL
    API-->>FE: Photo ID + Upload URL
    FE->>S3: Upload photo file
    FE->>API: POST /api/v1/photos/{id}/estimate
    API->>Q: Queue estimation job
    Q->>W: Process estimation
    W->>ML: Analyze photo
    ML-->>W: Calorie estimate
    W->>DB: Store estimate
    W-->>Q: Job complete
    FE->>API: GET /api/v1/estimates/{id}
    API-->>FE: Estimate results
    FE-->>WA: Display results
    WA-->>U: Show calories & macros
```

### Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant WA as Telegram WebApp
    participant FE as Frontend
    participant API as Backend API
    participant DB as Database

    U->>WA: Open mini-app
    WA->>FE: Init data
    FE->>API: POST /api/v1/auth/telegram/init
    API->>API: Validate Telegram data
    API->>DB: Create/update user
    DB-->>API: User data
    API-->>FE: Session token + user
    FE->>FE: Store session
    FE-->>WA: Authenticated state
    WA-->>U: Show app interface
```

## Deployment Architecture

### Development Environment

```mermaid
graph LR
    subgraph "Local Development"
        DEV_FE[Frontend Dev Server<br/>localhost:3000]
        DEV_API[Backend API<br/>localhost:8000]
        DEV_DB[Local PostgreSQL]
        DEV_REDIS[Local Redis]
        DEV_S3[Mock Storage]
    end

    DEV_FE --> DEV_API
    DEV_API --> DEV_DB
    DEV_API --> DEV_REDIS
    DEV_API --> DEV_S3
```

### Production Environment

```mermaid
graph TB
    subgraph "Fly.io Production"
        subgraph "Frontend App"
            FE_PROD[Frontend Container]
            FE_CDN[CDN Distribution]
        end

        subgraph "Backend App"
            API_PROD[Backend Container]
            WORKER_PROD[Worker Container]
        end

        subgraph "External Services"
            SUPABASE[(Supabase PostgreSQL)]
            REDIS_PROD[(Redis Cloud)]
            TIGRIS[(Tigris Storage)]
        end

        subgraph "Monitoring"
            LOGS[Structured Logging]
            METRICS[Performance Metrics]
            ALERTS[Alerting]
        end
    end

    FE_PROD --> FE_CDN
    FE_PROD --> API_PROD
    API_PROD --> WORKER_PROD
    API_PROD --> SUPABASE
    API_PROD --> REDIS_PROD
    API_PROD --> TIGRIS
    WORKER_PROD --> SUPABASE
    WORKER_PROD --> REDIS_PROD
    API_PROD --> LOGS
    WORKER_PROD --> LOGS
    LOGS --> METRICS
    METRICS --> ALERTS
```

## Environment Configuration

### Development vs Production

```mermaid
graph LR
    subgraph "Development Environment"
        DEV_FE[Frontend Dev Server<br/>localhost:3000]
        DEV_API[Backend API<br/>localhost:8000]
        DEV_DB[Local PostgreSQL]
        DEV_REDIS[Local Redis]
        DEV_S3[Mock Storage]
    end

    subgraph "Production Environment"
        PROD_FE[Frontend Container<br/>Fly.io]
        PROD_API[Backend Container<br/>Fly.io]
        PROD_DB[Supabase PostgreSQL]
        PROD_REDIS[Redis Cloud]
        PROD_S3[Tigris Storage]
    end

    DEV_FE --> DEV_API
    DEV_API --> DEV_DB
    DEV_API --> DEV_REDIS
    DEV_API --> DEV_S3

    PROD_FE --> PROD_API
    PROD_API --> PROD_DB
    PROD_API --> PROD_REDIS
    PROD_API --> PROD_S3
```

## Integration Points

### Frontend-Backend Integration

```mermaid
graph LR
    subgraph "Frontend"
        CONFIG[Configuration]
        API_CLIENT[API Client]
        AUTH_MGR[Auth Manager]
        ERROR_HANDLER[Error Handler]
    end

    subgraph "Backend"
        CORS[CORS Middleware]
        AUTH_MIDDLEWARE[Auth Middleware]
        API_ROUTES[API Routes]
        ERROR_MIDDLEWARE[Error Middleware]
    end

    CONFIG --> API_CLIENT
    API_CLIENT --> AUTH_MGR
    API_CLIENT --> ERROR_HANDLER
    API_CLIENT --> CORS
    CORS --> AUTH_MIDDLEWARE
    AUTH_MIDDLEWARE --> API_ROUTES
    API_ROUTES --> ERROR_MIDDLEWARE
```

## Technology Stack

### Frontend Technologies
- **React 18**: Modern React with hooks and concurrent features
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server
- **React Router**: Client-side routing
- **Axios**: HTTP client with interceptors
- **CSS Custom Properties**: Dynamic theming
- **Telegram WebApp API**: Native Telegram integration

### Backend Technologies
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Primary database
- **Redis**: Caching and session storage
- **Celery**: Background task processing
- **Tigris**: S3-compatible object storage
- **OpenAI API**: AI model integration
- **Telegram Bot API**: Bot functionality

### Infrastructure Technologies
- **Fly.io**: Container deployment platform
- **Docker**: Containerization
- **GitHub Actions**: CI/CD pipeline
- **Supabase**: Database hosting
- **Structured Logging**: Observability
- **Health Checks**: Monitoring

## Security Architecture

```mermaid
graph TD
    subgraph "Security Layers"
        TELEGRAM_AUTH[Telegram Authentication]
        SESSION_MGMT[Session Management]
        CORS_POLICY[CORS Policy]
        RATE_LIMIT[Rate Limiting]
        INPUT_VALIDATION[Input Validation]
        ENCRYPTION[Data Encryption]
    end

    TELEGRAM_AUTH --> SESSION_MGMT
    SESSION_MGMT --> CORS_POLICY
    CORS_POLICY --> RATE_LIMIT
    RATE_LIMIT --> INPUT_VALIDATION
    INPUT_VALIDATION --> ENCRYPTION
```

## Performance Architecture

### Caching Strategy

```mermaid
graph LR
    subgraph "Caching Layers"
        BROWSER[Browser Cache]
        CDN[CDN Cache]
        REDIS_CACHE[Redis Cache]
        DB_CACHE[Database Cache]
    end

    BROWSER --> CDN
    CDN --> REDIS_CACHE
    REDIS_CACHE --> DB_CACHE
```

### Optimization Strategies
- **Frontend**: Code splitting, lazy loading, image optimization
- **Backend**: Database indexing, query optimization, connection pooling
- **Infrastructure**: CDN distribution, container optimization
- **Monitoring**: Performance metrics, resource usage tracking

## Monitoring and Observability

```mermaid
graph TD
    subgraph "Observability Stack"
        LOGS[Structured Logs]
        METRICS[Performance Metrics]
        TRACES[Distributed Tracing]
        ALERTS[Alerting System]
        DASHBOARDS[Monitoring Dashboards]
    end

    LOGS --> METRICS
    METRICS --> TRACES
    TRACES --> ALERTS
    ALERTS --> DASHBOARDS
```

## Development Workflow

```mermaid
graph LR
    subgraph "Development Process"
        SPEC[Specification]
        PLAN[Planning]
        IMPL[Implementation]
        TEST[Testing]
        DEPLOY[Deployment]
        MONITOR[Monitoring]
    end

    SPEC --> PLAN
    PLAN --> IMPL
    IMPL --> TEST
    TEST --> DEPLOY
    DEPLOY --> MONITOR
    MONITOR --> SPEC
```

This architecture documentation provides a comprehensive view of the Calorie Track AI Bot system, showing how all components interact and work together to deliver a robust, scalable, and maintainable application.
