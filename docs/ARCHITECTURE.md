# Calorie Track AI Bot - System Architecture

## Overview

The Calorie Track AI Bot is a comprehensive Telegram Mini App that uses AI-powered computer vision to analyze food photos and provide detailed nutritional information. The system features a modern, mobile-first design with automatic theme detection, multi-language support, and enterprise-grade observability. The architecture prioritizes scalability, performance, and developer experience.

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        U[Telegram Users]
        TG[Telegram Mini App]
        WEB[Web Interface]
    end

    subgraph "Frontend Layer (Vercel)"
        FE[React App]
        THEME[Theme Detection]
        LANG[Language Detection]
        SAFE[Safe Area Handling]
        CONFIG[Configuration Service]
    end

    subgraph "Backend Layer (Fly.io)"
        API[FastAPI API]
        WORKER[Background Worker]
        MIDDLEWARE[Middleware Stack]
        MONITOR[Performance Monitor]
    end

    subgraph "Database Layer (Neon PostgreSQL)"
        DB[PostgreSQL Database]
        AUTH_DB[Auth Service]
        MIGRATIONS[Migration System]
    end

    subgraph "External Services"
        REDIS[Upstash Redis]
        S3[Tigris Storage]
        OPENAI[OpenAI API]
        BOT_API[Telegram Bot API]
    end

    subgraph "AI Processing"
        CV[Computer Vision]
        ESTIMATOR[Nutrition Estimator]
        QUEUE[Job Queue]
    end

    subgraph "Observability"
        LOGS[Structured Logging]
        METRICS[Performance Metrics]
        HEALTH[Health Checks]
        ALERTS[Error Tracking]
    end

    %% User interactions
    U --> TG
    U --> WEB
    TG --> FE
    WEB --> FE

    %% Frontend services
    FE --> THEME
    FE --> LANG
    FE --> SAFE
    FE --> CONFIG

    %% Frontend to backend
    FE --> API

    %% Backend services
    API --> MIDDLEWARE
    API --> MONITOR
    API --> WORKER

    %% Database connections
    API --> DB
    API --> AUTH_DB
    WORKER --> DB
    MIGRATIONS --> DB

    %% External service connections
    API --> REDIS
    API --> S3
    API --> BOT_API
    WORKER --> REDIS
    WORKER --> OPENAI

    %% AI processing
    API --> CV
    CV --> ESTIMATOR
    ESTIMATOR --> QUEUE
    QUEUE --> WORKER

    %% Observability
    API --> LOGS
    WORKER --> LOGS
    API --> METRICS
    WORKER --> METRICS
    API --> HEALTH
    LOGS --> ALERTS

    %% Styling
    classDef client fill:#e3f2fd
    classDef frontend fill:#e1f5fe
    classDef backend fill:#f3e5f5
    classDef database fill:#e8f5e8
    classDef external fill:#fff8e1
    classDef ai fill:#fce4ec
    classDef observability fill:#f1f8e9

    class U,TG,WEB client
    class FE,THEME,LANG,SAFE,CONFIG frontend
    class API,WORKER,MIDDLEWARE,MONITOR backend
    class DB,AUTH_DB,MIGRATIONS database
    class REDIS,S3,OPENAI,BOT_API external
    class CV,ESTIMATOR,QUEUE ai
    class LOGS,METRICS,HEALTH,ALERTS observability
```

## Inline Mode Pipeline

Inline photo analysis introduces an additional fast-path inside the existing architecture. The diagram below highlights the components that participate in the inline acknowledgement (≤3 s) and result delivery (≤10 s) SLAs while maintaining the 24 hour retention boundary for transient artifacts.

```mermaid
sequenceDiagram
    participant TG as Telegram Bot API
    participant API as FastAPI /api/v1/bot
    participant RQ as Upstash Redis Queue
    participant WK as Inline Worker
    participant OA as OpenAI Vision
    participant ST as Tigris Storage
    participant SA as Neon PostgreSQL Analytics

    TG->>API: Inline update (query / reply / tagged photo)
    API->>API: Validate + hash identifiers<br/>record request metadata
    API->>TG: Placeholder acknowledgement (≤3 s)
    API->>RQ: Enqueue InlineInteractionJob
    RQ->>WK: Pop job
    WK->>TG: Download photo file
    WK->>ST: Upload transient copy (expires ≤24 h)
    WK->>OA: Request calorie/macronutrient analysis
    OA-->>WK: Analysis payload
    WK->>TG: Edit inline message / threaded reply
    WK->>SA: Upsert InlineAnalyticsDaily aggregates
    WK->>API: Emit structured logs + metrics (trigger_type, latency, permission status)
```

**Throughput target**: the inline queue is dimensioned for 60 jobs per minute with bursts up to 5 RPS across active groups, matching the plan’s scaling assumptions. The worker pool scales horizontally once Redis pending counts exceed thresholds logged via the telemetry hooks.

**Privacy boundary**: chat and user identifiers are salted + hashed before leaving the webhook, and only aggregate analytics (success/failure counts, latency, accuracy within tolerance, permission block counts) reach PostgreSQL. Transient photos uploaded to Tigris are purged within 24 hours by the existing cleanup routine.

## Component Architecture

### Frontend Architecture

```mermaid
graph TD
    subgraph "React Frontend Application"
        APP[App.tsx<br/>Main Application]
        ROUTER[React Router]
        CONTEXT[Telegram WebApp Context]

        subgraph "Core Pages"
            TODAY[Today Page<br/>Main Dashboard]
            MEAL[Meal Detail<br/>Nutrition View]
            STATS[Stats Page<br/>Analytics]
            GOALS[Goals Page<br/>Target Setting]
        end

        subgraph "UI Components"
            ERROR[Error Boundary<br/>Error Handling]
            LOADING[Loading Component<br/>State Management]
            SHARE[Share Component<br/>Social Features]
            SAFE_AREA[Safe Area Wrapper<br/>Mobile Layout]
        end

        subgraph "Detection Services"
            THEME_DETECT[Theme Detector<br/>Auto Light/Dark]
            LANG_DETECT[Language Detector<br/>Auto EN/RU]
            SAFE_DETECT[Safe Area Detection<br/>Mobile Insets]
        end

        subgraph "Configuration Services"
            CONFIG_SVC[Configuration Service<br/>Runtime Config]
            API_CLIENT[API Client<br/>HTTP Layer]
            AUTH_MGR[Authentication<br/>Telegram Auth]
        end

        subgraph "State Management"
            CONTEXT_API[React Context]
            LOCAL_STATE[Component State]
            SESSION_MGR[Session Manager]
        end

        subgraph "Styling & UX"
            CSS_MODULES[CSS Modules<br/>Scoped Styles]
            THEME_SYS[Theme System<br/>Dynamic Theming]
            I18N[Internationalization<br/>Multi-language]
            RESPONSIVE[Responsive Design<br/>Mobile-first]
        end
    end

    %% Main app flow
    APP --> ROUTER
    APP --> CONTEXT
    APP --> ERROR

    %% Router connections
    ROUTER --> TODAY
    ROUTER --> MEAL
    ROUTER --> STATS
    ROUTER --> GOALS

    %% Component integration
    APP --> SAFE_AREA
    SAFE_AREA --> LOADING
    SAFE_AREA --> SHARE

    %% Detection services
    APP --> THEME_DETECT
    APP --> LANG_DETECT
    APP --> SAFE_DETECT

    %% Configuration services
    APP --> CONFIG_SVC
    CONFIG_SVC --> API_CLIENT
    API_CLIENT --> AUTH_MGR

    %% State management
    CONTEXT --> CONTEXT_API
    CONTEXT_API --> LOCAL_STATE
    AUTH_MGR --> SESSION_MGR

    %% Styling connections
    THEME_DETECT --> THEME_SYS
    LANG_DETECT --> I18N
    SAFE_DETECT --> RESPONSIVE
    CSS_MODULES --> THEME_SYS

    %% Styling
    classDef core fill:#e1f5fe
    classDef components fill:#f3e5f5
    classDef services fill:#e8f5e8
    classDef state fill:#fff3e0
    classDef styling fill:#fce4ec

    class APP,ROUTER,CONTEXT,TODAY,MEAL,STATS,GOALS core
    class ERROR,LOADING,SHARE,SAFE_AREA components
    class THEME_DETECT,LANG_DETECT,SAFE_DETECT,CONFIG_SVC,API_CLIENT,AUTH_MGR services
    class CONTEXT_API,LOCAL_STATE,SESSION_MGR state
    class CSS_MODULES,THEME_SYS,I18N,RESPONSIVE styling
```

### Backend Architecture

```mermaid
graph TD
    subgraph "FastAPI Backend Application"
        MAIN[main.py<br/>Application Entry]
        LIFESPAN[Lifespan Manager<br/>Startup/Shutdown]

        subgraph "Middleware Stack"
            CORS_MW[CORS Middleware<br/>Cross-Origin]
            TRUSTED_MW[Trusted Host Middleware<br/>Security]
            CORRELATION_MW[Correlation ID Middleware<br/>Tracing]
            LOGGING_MW[Request Logging Middleware<br/>Observability]
        end

        subgraph "API Routes v1"
            HEALTH[Health & Connectivity<br/>/health/*]
            CONFIG_ROUTE[Configuration<br/>/api/v1/config/*]
            LOGS_ROUTE[Logging<br/>/api/v1/logs/*]
            DEV_ROUTE[Development<br/>/api/v1/dev/*]
            AUTH_ROUTE[Authentication<br/>/api/v1/auth/*]
            PHOTOS_ROUTE[Photo Management<br/>/api/v1/photos/*]
            ESTIMATES_ROUTE[AI Estimates<br/>/api/v1/estimates/*]
            MEALS_ROUTE[Meal Tracking<br/>/api/v1/meals/*]
            SUMMARY_ROUTE[Daily Summary<br/>/api/v1/daily-summary/*]
            GOALS_ROUTE[User Goals<br/>/api/v1/goals/*]
            BOT_ROUTE[Telegram Bot<br/>/api/v1/bot/*]
        end

        subgraph "Core Services"
            CONFIG_SVC[Configuration Service<br/>Settings & Features]
            DB_SVC[Database Service<br/>Neon PostgreSQL]
            STORAGE_SVC[Storage Service<br/>Tigris S3]
            TELEGRAM_SVC[Telegram Service<br/>Bot API]
            ESTIMATOR_SVC[AI Estimator Service<br/>OpenAI Integration]
            QUEUE_SVC[Queue Service<br/>Redis Tasks]
            MONITORING_SVC[Monitoring Service<br/>Performance Metrics]
        end

        subgraph "Background Workers"
            ESTIMATE_WORKER[Estimate Worker<br/>AI Processing]
        end
    end

    %% Main application flow
    MAIN --> LIFESPAN
    MAIN --> CORS_MW
    MAIN --> TRUSTED_MW
    MAIN --> CORRELATION_MW
    MAIN --> LOGGING_MW

    %% Middleware to routes
    CORS_MW --> HEALTH
    CORS_MW --> CONFIG_ROUTE
    CORS_MW --> LOGS_ROUTE
    CORS_MW --> DEV_ROUTE
    CORS_MW --> AUTH_ROUTE
    CORS_MW --> PHOTOS_ROUTE
    CORS_MW --> ESTIMATES_ROUTE
    CORS_MW --> MEALS_ROUTE
    CORS_MW --> SUMMARY_ROUTE
    CORS_MW --> GOALS_ROUTE
    CORS_MW --> BOT_ROUTE

    %% Route to service connections
    CONFIG_ROUTE --> CONFIG_SVC
    LOGS_ROUTE --> MONITORING_SVC
    DEV_ROUTE --> CONFIG_SVC
    AUTH_ROUTE --> TELEGRAM_SVC
    PHOTOS_ROUTE --> STORAGE_SVC
    ESTIMATES_ROUTE --> ESTIMATOR_SVC
    MEALS_ROUTE --> DB_SVC
    SUMMARY_ROUTE --> DB_SVC
    GOALS_ROUTE --> DB_SVC
    BOT_ROUTE --> TELEGRAM_SVC

    %% Service interconnections
    CONFIG_ROUTE --> DB_SVC
    ESTIMATOR_SVC --> QUEUE_SVC
    QUEUE_SVC --> ESTIMATE_WORKER
    ESTIMATE_WORKER --> DB_SVC
    ESTIMATE_WORKER --> ESTIMATOR_SVC

    %% Monitoring connections
    LOGGING_MW --> MONITORING_SVC
    CORRELATION_MW --> MONITORING_SVC

    %% Styling
    classDef main fill:#e1f5fe
    classDef middleware fill:#f3e5f5
    classDef routes fill:#e8f5e8
    classDef services fill:#fff3e0
    classDef workers fill:#fce4ec

    class MAIN,LIFESPAN main
    class CORS_MW,TRUSTED_MW,CORRELATION_MW,LOGGING_MW middleware
    class HEALTH,CONFIG_ROUTE,LOGS_ROUTE,DEV_ROUTE,AUTH_ROUTE,PHOTOS_ROUTE,ESTIMATES_ROUTE,MEALS_ROUTE,SUMMARY_ROUTE,GOALS_ROUTE,BOT_ROUTE routes
    class CONFIG_SVC,DB_SVC,STORAGE_SVC,TELEGRAM_SVC,ESTIMATOR_SVC,QUEUE_SVC,MONITORING_SVC services
    class ESTIMATE_WORKER workers
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
            NEON[(Neon PostgreSQL)]
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
    API_PROD --> NEON
    API_PROD --> REDIS_PROD
    API_PROD --> TIGRIS
    WORKER_PROD --> NEON
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
        PROD_DB[Neon PostgreSQL]
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
- **TypeScript**: Type-safe development with strict mode
- **Vite**: Fast build tool and dev server
- **React Router**: Client-side routing
- **Axios**: HTTP client with interceptors and correlation IDs
- **CSS Modules**: Scoped styling with dynamic theming
- **Telegram WebApp API**: Native Telegram Mini App integration
- **Zod**: Runtime type validation for configuration
- **i18next**: Internationalization (English/Russian)

### Backend Technologies
- **FastAPI**: Modern Python web framework with OpenAPI 3.1.1
- **Python 3.12**: Latest Python with type hints
- **Neon PostgreSQL**: Serverless PostgreSQL database (via psycopg3)
- **Upstash Redis**: Serverless Redis for caching and queues
- **Tigris**: S3-compatible object storage
- **OpenAI API**: GPT-5-mini for nutrition analysis
- **Telegram Bot API**: Bot functionality and webhooks
- **Structlog**: Structured logging with correlation IDs
- **Pydantic v2**: Data validation and serialization
- **psutil**: System monitoring and performance metrics

### Infrastructure Technologies
- **Fly.io**: Container deployment platform for backend
- **Vercel**: Edge deployment for frontend
- **Docker**: Containerization with multi-stage builds
- **Neon**: Serverless PostgreSQL with branching
- **GitHub Actions**: CI/CD pipeline
- **Performance Monitoring**: Real-time metrics collection
- **Health Checks**: Comprehensive connectivity monitoring
- **Correlation IDs**: Distributed tracing

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
