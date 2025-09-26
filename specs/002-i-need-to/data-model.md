# Data Model: Backend-Frontend Integration & Modern UI/UX Enhancement

## Core Entities

### UI Configuration Entity
**Purpose**: Manages frontend configuration, safe area settings, theme detection, and language detection

**Fields**:
- `id`: string (primary key)
- `environment`: 'development' | 'production'
- `api_base_url`: string
- `safe_area_top`: number (CSS env value)
- `safe_area_bottom`: number (CSS env value)
- `safe_area_left`: number (CSS env value)
- `safe_area_right`: number (CSS env value)
- `theme`: 'light' | 'dark' | 'auto'
- `theme_source`: 'telegram' | 'system' | 'manual'
- `language`: string (ISO 639-1 code, e.g., 'en', 'ru')
- `language_source`: 'telegram' | 'browser' | 'manual'
- `features`: object (feature flags)
- `created_at`: timestamp
- `updated_at`: timestamp

**Validation Rules**:
- `api_base_url` must be valid HTTP/HTTPS URL
- `environment` must be one of allowed values
- Safe area values must be non-negative numbers
- `theme` must be one of allowed values
- `theme_source` must be one of allowed values
- `language` must be valid ISO 639-1 language code
- `language_source` must be one of allowed values

**State Transitions**:
- `initialization` → `detecting` (on app startup)
- `detecting` → `configured` (after theme/language detection)
- `configured` → `updated` (on configuration change)
- `configured` → `detecting` (on theme/language change)

### Connection Status Entity
**Purpose**: Tracks frontend-backend connectivity status

**Fields**:
- `id`: string (primary key)
- `status`: 'connected' | 'disconnected' | 'error'
- `last_check`: timestamp
- `response_time_ms`: number
- `error_message`: string (nullable)
- `retry_count`: number
- `correlation_id`: string

**Validation Rules**:
- `status` must be one of allowed values
- `response_time_ms` must be non-negative
- `retry_count` must be non-negative integer
- `correlation_id` must be valid UUID format

**State Transitions**:
- `disconnected` → `connected` (on successful connection)
- `connected` → `disconnected` (on connection loss)
- `disconnected` → `error` (on connection failure)
- `error` → `disconnected` (on retry)

### Log Entry Entity
**Purpose**: Structured logging for observability

**Fields**:
- `id`: string (primary key)
- `timestamp`: timestamp
- `level`: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL'
- `service`: string (frontend/backend)
- `correlation_id`: string
- `message`: string
- `context`: object (additional data)
- `user_id`: string (nullable)
- `request_id`: string (nullable)

**Validation Rules**:
- `level` must be one of allowed values
- `service` must be non-empty string
- `correlation_id` must be valid UUID format
- `message` must be non-empty string
- `context` must be valid JSON object

### Development Environment Entity
**Purpose**: Manages local development configuration with Supabase database-only CLI integration

**Fields**:
- `id`: string (primary key)
- `name`: string (environment name)
- `frontend_port`: number
- `backend_port`: number
- `supabase_db_url`: string (http://localhost:54322 - database only)
- `supabase_db_password`: string
- `redis_url`: string (Upstash for production, local for dev)
- `storage_endpoint`: string (Tigris endpoint)
- `cors_origins`: array of strings
- `log_level`: string
- `hot_reload`: boolean
- `supabase_cli_version`: string
- `created_at`: timestamp
- `updated_at`: timestamp

**Validation Rules**:
- `name` must be unique
- Port numbers must be valid (1024-65535)
- Supabase database URL must be valid format
- `cors_origins` must be array of valid URLs
- `log_level` must be one of allowed values
- `supabase_cli_version` must be valid semantic version

**State Transitions**:
- `initialization` → `db_starting` (on `supabase db start`)
- `db_starting` → `ready` (on successful database start)
- `ready` → `migrating` (on `supabase db push`)
- `migrating` → `ready` (on successful migration)

## Entity Relationships

### UI Configuration ↔ Connection Status
- One-to-many relationship
- UI Configuration can have multiple connection status records
- Connection status belongs to one UI Configuration

### Log Entry ↔ Connection Status
- Many-to-one relationship
- Multiple log entries can reference one connection status
- Log entry belongs to one connection status

### Development Environment ↔ UI Configuration
- One-to-one relationship
- Each environment has one UI configuration
- UI configuration belongs to one environment

## Data Flow Patterns

### Configuration Flow
1. **Initialization**: Load default configuration
2. **Environment Detection**: Determine development/production
3. **Safe Area Detection**: Query device safe areas
4. **API Configuration**: Set backend connection details
5. **Feature Flags**: Load enabled features
6. **Validation**: Validate all configuration values

### Connection Flow
1. **Health Check**: Ping backend API
2. **Status Update**: Update connection status entity
3. **Error Handling**: Log connection errors
4. **Retry Logic**: Implement exponential backoff
5. **Recovery**: Attempt reconnection

### Logging Flow
1. **Event Generation**: Create log entry
2. **Correlation**: Add correlation ID
3. **Structured Output**: Format as JSON
4. **Transport**: Send to logging system
5. **Aggregation**: Collect in centralized system

## State Management

### Frontend State
- **Configuration State**: UI Configuration entity
- **Connection State**: Connection Status entity
- **Theme State**: Theme preferences
- **Feature State**: Feature flag states

### Backend State
- **Service State**: Service health status
- **Log State**: Logging configuration
- **Environment State**: Development environment settings

## Validation Rules

### Cross-Entity Validation
- Connection status must match environment configuration
- Log entries must have valid correlation IDs
- Safe area values must be consistent across UI configuration

### Business Rules
- Development environment must allow CORS from localhost
- Production environment must have secure CORS origins
- Log levels must be appropriate for environment
- Feature flags must be consistent across services

## Performance Considerations

### Caching Strategy
- UI Configuration cached in frontend
- Connection status cached with TTL
- Log entries batched for performance

### Optimization
- Lazy loading of configuration
- Debounced connection checks
- Compressed log entries
- Efficient state updates
