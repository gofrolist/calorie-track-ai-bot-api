# Tasks: Backend-Frontend Integration & Modern UI/UX Enhancement

**Input**: Design documents from `/specs/002-i-need-to/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: TypeScript 5.x, Python 3.11, React 18, FastAPI
   → Structure: Web application (frontend + backend)
2. Load design documents:
   → data-model.md: 4 entities → model tasks
   → contracts/: 2 files → contract test tasks
   → quickstart.md: Integration scenarios
3. Generate tasks by category:
   → Setup: Telegram Mini Apps template, dependencies
   → Tests: contract tests, integration tests (TDD)
   → Core: models, services, API endpoints
   → Integration: CORS, logging, connectivity
   → Polish: performance, docs, validation
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Frontend/backend can run parallel
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001-T072)
6. Validate: All contracts tested, entities modeled
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Frontend**: `frontend/src/`, `frontend/tests/`
- **Backend**: `backend/src/calorie_track_ai_bot/`, `backend/tests/`
- **Docs**: `docs/`
- **Root**: `Makefile`, configuration files

## Phase 3.1: Setup
- [x] T001 Update frontend to Telegram Mini Apps React template in `frontend/`
- [x] T002 [P] Configure Supabase database-only CLI setup with `supabase db start`
- [x] T003 [P] Set up CORS configuration for development and production environments
- [x] T004 [P] Initialize structured logging dependencies in `backend/pyproject.toml`

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests
- [x] T005 [P] Contract test GET /health/connectivity in `backend/tests/api/v1/test_health_connectivity.py`
- [x] T006 [P] Contract test GET /api/v1/config/ui in `backend/tests/api/v1/test_config_ui_get.py`
- [x] T007 [P] Contract test PUT /api/v1/config/ui in `backend/tests/api/v1/test_config_ui_put.py`
- [x] T008 [P] Contract test GET /api/v1/config/theme in `backend/tests/api/v1/test_config_theme.py`
- [x] T009 [P] Contract test GET /api/v1/config/language in `backend/tests/api/v1/test_config_language.py`
- [x] T010 [P] Contract test POST /api/v1/logs in `backend/tests/api/v1/test_logs.py`
- [x] T011 [P] Contract test GET /api/v1/dev/environment in `backend/tests/api/v1/test_dev_environment.py`
- [x] T012 [P] Contract test GET /api/v1/dev/supabase/status in `backend/tests/api/v1/test_dev_supabase_status.py`
- [x] T012a [P] Performance contract test CPU/memory usage in `backend/tests/api/v1/test_performance_contracts.py`

### Frontend Contract Tests
- [x] T013 [P] Frontend API contract tests in `frontend/tests/contracts/config.test.ts`
- [x] T014 [P] Frontend theme detection tests in `frontend/tests/contracts/theme-detection.test.ts`
- [x] T015 [P] Frontend language detection tests in `frontend/tests/contracts/language-detection.test.ts`

### Integration Tests
- [x] T016 [P] Integration test frontend-backend connectivity in `backend/tests/integration/test_connectivity.py`
- [x] T017 [P] Integration test mobile safe areas in `frontend/tests/e2e/safe-areas.spec.ts`
- [x] T018 [P] Integration test theme switching in `frontend/tests/e2e/theme-switching.spec.ts`
- [x] T019 [P] Integration test language detection in `frontend/tests/e2e/language-detection.spec.ts`
- [x] T020 [P] Integration test logging system in `backend/tests/integration/test_logging_system.py`
- [x] T020a [P] Integration test error handling and user feedback in `backend/tests/integration/test_error_handling.py`

## Phase 3.3: Backend Core Implementation (ONLY after tests are failing)

### Data Models
- [x] T021 UIConfiguration model in `backend/src/calorie_track_ai_bot/schemas.py`
- [x] T022 ConnectionStatus model in `backend/src/calorie_track_ai_bot/schemas.py` (depends on T021)
- [x] T023 LogEntry model in `backend/src/calorie_track_ai_bot/schemas.py` (depends on T022)
- [x] T024 DevelopmentEnvironment model in `backend/src/calorie_track_ai_bot/schemas.py` (depends on T023)

### Services
- [x] T025 [P] UIConfigurationService in `backend/src/calorie_track_ai_bot/services/config.py`
- [x] T026 [P] ThemeDetectionService in `backend/src/calorie_track_ai_bot/services/theme_detection.py`
- [x] T027 [P] LanguageDetectionService in `backend/src/calorie_track_ai_bot/services/language_detection.py`
- [x] T028 [P] StructuredLoggingService in `backend/src/calorie_track_ai_bot/services/logging_service.py`

### API Endpoints
- [x] T029 GET /health/connectivity endpoint in `backend/src/calorie_track_ai_bot/api/v1/connectivity.py`
- [x] T030 GET /api/v1/config/ui endpoint in `backend/src/calorie_track_ai_bot/api/v1/config.py`
- [x] T031 PUT /api/v1/config/ui endpoint in `backend/src/calorie_track_ai_bot/api/v1/config.py`
- [x] T032 GET /api/v1/config/theme endpoint in `backend/src/calorie_track_ai_bot/api/v1/config.py`
- [x] T033 GET /api/v1/config/language endpoint in `backend/src/calorie_track_ai_bot/api/v1/config.py`
- [x] T034 POST /api/v1/logs endpoint in `backend/src/calorie_track_ai_bot/api/v1/logs.py`
- [x] T035 [P] GET /api/v1/dev/environment endpoint in `backend/src/calorie_track_ai_bot/api/v1/dev.py`
- [x] T036 [P] GET /api/v1/dev/supabase/status endpoint in `backend/src/calorie_track_ai_bot/api/v1/dev.py`

## Phase 3.4: Frontend Core Implementation

### UI Components
- [x] T037 [P] Mobile safe areas CSS implementation in `frontend/src/telegram-webapp.css`
- [x] T038 [P] Theme detection component in `frontend/src/components/ThemeDetector.tsx`
- [x] T039 [P] Language detection component in `frontend/src/components/LanguageDetector.tsx`
- [x] T040 [P] Safe area wrapper component in `frontend/src/components/SafeAreaWrapper.tsx`

### Services
- [x] T041 [P] Configuration API service in `frontend/src/services/config.ts`
- [x] T042 [P] Theme detection service in `frontend/src/services/theme-detection.ts`
- [x] T043 [P] Language detection service in `frontend/src/services/language-detection.ts`
- [x] T044 [P] Connectivity monitoring service in `frontend/src/services/connectivity.ts`

### Configuration
- [x] T045 Update frontend configuration in `frontend/src/config.ts`
- [x] T046 Environment-specific API base URLs in `frontend/src/config.ts` (depends on T045)

## Phase 3.5: Integration & Middleware

### Backend Integration
- [x] T047 CORS middleware configuration in `backend/src/calorie_track_ai_bot/main.py`
- [x] T048 Structured logging middleware in `backend/src/calorie_track_ai_bot/services/logging_service.py`
- [x] T049 Error handling middleware with correlation IDs in `backend/src/calorie_track_ai_bot/main.py`
- [x] T050 Database integration for UI configuration in `backend/src/calorie_track_ai_bot/services/db.py`

### Frontend Integration
- [x] T051 API client integration in `frontend/src/services/api.ts`
- [x] T052 Theme switching implementation in `frontend/src/app.tsx`
- [x] T053 Language switching implementation in `frontend/src/app.tsx`
- [x] T054 Safe area detection implementation in `frontend/src/app.tsx`

## Phase 3.6: Development Environment

### Local Development
- [x] T055 [P] Docker Compose configuration in `docker-compose.yml`
- [x] T056 [P] Supabase local development setup in `backend/env.template`
- [x] T057 [P] Development scripts in `backend/Makefile`
- [x] T058 [P] Frontend development configuration in `frontend/package.json`

### Testing Infrastructure
- [x] T059 [P] Performance monitoring setup in `backend/src/calorie_track_ai_bot/services/monitoring.py`
- [x] T060 [P] Integration test helpers in `backend/tests/conftest.py`
- [x] T061 [P] E2E test configuration in `frontend/playwright.config.ts`

## Phase 3.7: Documentation & Polish

### Documentation
- [x] T062 [P] Update architecture documentation in `docs/ARCHITECTURE.md`
- [x] T063 [P] Create integration testing guide in `docs/INTEGRATION_TESTING.md`
- [x] T064 [P] Mobile safe areas guide in `docs/MOBILE_SAFE_AREAS.md`
- [x] T065 [P] API documentation updates in `backend/specs/openapi.yaml`

### Performance & Validation
- [x] T066 [P] CPU/memory optimization validation in `backend/tests/performance/test_resource_usage.py`
- [x] T067 [P] Mobile device testing validation in `frontend/tests/e2e/mobile-devices.spec.ts`
- [x] T068 [P] Connectivity performance tests (integrated in T066)

### Final Validation
- [x] T069 Run quickstart validation scenarios (all scenarios implemented and tested)
- [x] T070 Performance benchmarks validation (tests confirm <200ms API, <2s page load)
- [x] T071 [P] Linting and code quality checks across all files
- [x] T072 [P] Security validation for CORS and authentication

## Dependencies

### Critical Path
- Setup (T001-T004) → Tests (T005-T020a) → Implementation (T021-T061) → Polish (T062-T072)
- Tests MUST fail before any implementation begins
- T021-T024 (models) before T025-T028 (services)
- T025-T028 (services) before T029-T036 (endpoints)
- T047-T050 (backend integration) before T051-T054 (frontend integration)

### Blocking Dependencies
- T001 blocks T037-T046 (frontend depends on template update)
- T021-T024 block T025-T028 (services need models)
- T025-T028 block T029-T036 (endpoints need services)
- T047-T050 block T051-T054 (frontend needs backend endpoints)
- Implementation (T021-T061) blocks documentation (T062-T068)

## Parallel Execution Examples

### Phase 3.2 - All Contract Tests (Different Files)
```bash
# Launch T005-T012 together (backend contract tests):
Task: "Contract test GET /health/connectivity in backend/tests/api/v1/test_health_connectivity.py"
Task: "Contract test GET /api/v1/config/ui in backend/tests/api/v1/test_config_ui_get.py"
Task: "Contract test PUT /api/v1/config/ui in backend/tests/api/v1/test_config_ui_put.py"
Task: "Contract test GET /api/v1/config/theme in backend/tests/api/v1/test_config_theme.py"
Task: "Contract test GET /api/v1/config/language in backend/tests/api/v1/test_config_language.py"
Task: "Contract test POST /api/v1/logs in backend/tests/api/v1/test_logs.py"
Task: "Contract test GET /api/v1/dev/environment in backend/tests/api/v1/test_dev_environment.py"
Task: "Contract test GET /api/v1/dev/supabase/status in backend/tests/api/v1/test_dev_supabase_status.py"
```

### Phase 3.3 - Model Creation (Sequential - Same File)
```bash
# Execute T021-T024 sequentially (all models in schemas.py):
# T021 → T022 → T023 → T024 (sequential execution required)
Task: "UIConfiguration model in backend/src/calorie_track_ai_bot/schemas.py"
# Wait for completion, then:
Task: "ConnectionStatus model in backend/src/calorie_track_ai_bot/schemas.py"
# Continue sequentially...
```

### Phase 3.4 - Frontend Components (Different Files)
```bash
# Launch T037-T044 together (different component files):
Task: "Mobile safe areas CSS implementation in frontend/src/telegram-webapp.css"
Task: "Theme detection component in frontend/src/components/ThemeDetector.tsx"
Task: "Language detection component in frontend/src/components/LanguageDetector.tsx"
Task: "Safe area wrapper component in frontend/src/components/SafeAreaWrapper.tsx"
Task: "Configuration API service in frontend/src/services/config.ts"
Task: "Theme detection service in frontend/src/services/theme-detection.ts"
Task: "Language detection service in frontend/src/services/language-detection.ts"
Task: "Connectivity monitoring service in frontend/src/services/connectivity.ts"
```

### Phase 3.7 - Documentation (Different Files)
```bash
# Launch T062-T065 together (different documentation files):
Task: "Update architecture documentation in docs/ARCHITECTURE.md"
Task: "Create integration testing guide in docs/INTEGRATION_TESTING.md"
Task: "Mobile safe areas guide in docs/MOBILE_SAFE_AREAS.md"
Task: "API documentation updates in backend/specs/openapi.yaml"
```

## Notes
- [P] tasks = different files, no dependencies
- Verify ALL tests fail before implementing ANY features
- Commit after each task completion
- Frontend and backend tasks can often run in parallel
- Safe area implementation requires actual mobile device testing
- Theme/language detection needs Telegram WebApp environment

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts**:
   - api-contracts.yaml → 8 contract test tasks [P]
   - Each endpoint → implementation task

2. **From Data Model**:
   - 4 entities → 4 model creation tasks (sequential - same file)
   - Entity relationships → service layer tasks [P]

3. **From Quickstart Scenarios**:
   - Connectivity testing → integration test [P]
   - Safe area validation → E2E test [P]
   - Theme switching → integration test [P]

4. **Ordering**:
   - Setup → Tests → Models → Services → Endpoints → Integration → Polish
   - TDD: Tests before implementation
   - Dependencies: Models before services before endpoints

## Validation Checklist
*GATE: Checked before execution*

- [x] All contracts have corresponding tests (T005-T015, T012a, T020a)
- [x] All entities have model tasks (T021-T024)
- [x] All tests come before implementation (T005-T020a before T021+)
- [x] Parallel tasks in different files ([P] marked correctly)
- [x] Each task specifies exact file path
- [x] No [P] task modifies same file as another [P] task
- [x] Frontend/backend separation maintained
- [x] Mobile-first and safe area requirements addressed
- [x] Theme/language detection implementation planned
- [x] Performance optimization tasks included
- [x] Documentation and validation tasks complete
