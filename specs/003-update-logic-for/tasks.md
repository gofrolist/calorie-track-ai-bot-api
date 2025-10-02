# Tasks: Multi-Photo Meal Tracking & Enhanced Meals History

**Input**: Design documents from `/specs/003-update-logic-for/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → SUCCESS: TypeScript 5.x, Python 3.11, React 18, FastAPI
   → Structure: Web application (frontend + backend)
2. Load design documents:
   → data-model.md: 4 entities (Meal, Photo, Estimate, DailySummary)
   → contracts/: 2 files (meals-api.yaml, photos-estimates-api.yaml)
   → quickstart.md: 10 integration scenarios
3. Generate tasks by category:
   → Setup: Database migration, dependencies
   → Tests: Contract tests, integration tests, component tests
   → Core: Bot handler, estimator, API endpoints, UI components
   → Integration: Frontend-backend connection
   → Polish: Performance, responsive design, docs
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Frontend/backend can run parallel
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001-T053)
6. Validate: All contracts tested, entities modeled, scenarios covered
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Backend**: `backend/src/calorie_track_ai_bot/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- **Database**: `supabase/migrations/`
- **Root**: Configuration files

## Phase 3.1: Setup & Dependencies
- [x] T001 Create database migration file `supabase/migrations/[timestamp]_multiphotos_meals.sql` with schema from data-model.md
- [x] T002 [P] Install frontend dependencies: `react-day-picker@^9.0.0` and `swiper@^11.0.0` in `frontend/package.json`
- [x] T003 [P] Update backend Python dependencies if needed in `backend/pyproject.toml` (no updates required - all dependencies present)
- [x] T004 Run database migration to add macronutrient fields, meal-photo relationships, and indexes

## Phase 3.2: Tests First - Backend (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (API Endpoints)
- [x] T005 [P] Contract test GET /api/v1/meals in `backend/tests/api/v1/test_meals_list.py`
- [x] T006 [P] Contract test GET /api/v1/meals/{id} in `backend/tests/api/v1/test_meals_get.py`
- [x] T007 [P] Contract test PATCH /api/v1/meals/{id} in `backend/tests/api/v1/test_meals_update.py`
- [x] T008 [P] Contract test DELETE /api/v1/meals/{id} in `backend/tests/api/v1/test_meals_delete.py`
- [x] T009 [P] Contract test GET /api/v1/meals/calendar in `backend/tests/api/v1/test_meals_calendar.py`
- [x] T010 [P] Contract test POST /api/v1/photos (multi-photo) in `backend/tests/api/v1/test_photos_multiphotos.py`
- [x] T011 [P] Contract test POST /api/v1/estimates (multi-photo) in `backend/tests/api/v1/test_estimates_multiphotos.py`

### Service Tests
- [x] T012 [P] Test bot media_group_id detection in `backend/tests/services/test_telegram_media_groups.py`
- [x] T013 [P] Test multi-photo AI estimation in `backend/tests/services/test_estimator_multiphotos.py`
- [x] T014 [P] Test 5-photo limit validation in `backend/tests/services/test_photo_validation.py`

### Integration Tests
- [x] T015 [P] Integration test: Multi-photo meal submission (Scenario 1) in `backend/tests/integration/test_multiphotos_workflow.py`
- [x] T016 [P] Integration test: Photos without text (Scenario 2) in `backend/tests/integration/test_multiphotos_no_text.py`
- [x] T017 [P] Integration test: 5-photo limit enforcement (Scenario 3) in `backend/tests/integration/test_photo_limit.py`
- [x] T018 [P] Integration test: Meal editing with macro updates (Scenario 7) in `backend/tests/integration/test_meal_editing.py`
- [x] T019 [P] Integration test: Meal deletion with stats update (Scenario 8) in `backend/tests/integration/test_meal_deletion.py`

## Phase 3.3: Backend Implementation (ONLY after tests are failing)

### Database Layer
- [x] T020 [P] Update Meal model with macronutrient fields in `backend/src/calorie_track_ai_bot/schemas.py`
- [x] T021 [P] Update Photo model with meal_id, media_group_id, display_order in `backend/src/calorie_track_ai_bot/schemas.py`
- [x] T022 [P] Add database queries for meals with photos in `backend/src/calorie_track_ai_bot/services/db.py`
- [x] T023 [P] Add calendar summary query in `backend/src/calorie_track_ai_bot/services/db.py`

### Bot Handler (Multi-Photo Logic)
- [x] T024 Implement media_group_id detection in `backend/src/calorie_track_ai_bot/services/telegram.py`
- [x] T025 Implement photo aggregation with 200ms wait window in `backend/src/calorie_track_ai_bot/services/telegram.py`
- [x] T026 Implement 5-photo limit check and user notification in `backend/src/calorie_track_ai_bot/api/v1/bot.py`
- [x] T027 Update bot message handler to process photo groups in `backend/src/calorie_track_ai_bot/api/v1/bot.py`

### AI Estimation Service
- [x] T028 Update estimator to accept photo array in `backend/src/calorie_track_ai_bot/services/estimator.py`
- [x] T029 Implement OpenAI multi-photo API call in `backend/src/calorie_track_ai_bot/services/estimator.py`
- [x] T030 Extract macronutrients from AI response in `backend/src/calorie_track_ai_bot/services/estimator.py`
- [x] T031 Update estimate worker for multi-photo processing in `backend/src/calorie_track_ai_bot/workers/estimate_worker.py`

### API Endpoints (Meal Management)
- [x] T032 Implement GET /api/v1/meals with date filtering in `backend/src/calorie_track_ai_bot/api/v1/meals.py`
- [x] T033 Implement GET /api/v1/meals/{id} with photos in `backend/src/calorie_track_ai_bot/api/v1/meals.py`
- [x] T034 Implement PATCH /api/v1/meals/{id} with macro update in `backend/src/calorie_track_ai_bot/api/v1/meals.py`
- [x] T035 Implement DELETE /api/v1/meals/{id} with stats recalculation in `backend/src/calorie_track_ai_bot/api/v1/meals.py`
- [x] T036 Implement GET /api/v1/meals/calendar endpoint in `backend/src/calorie_track_ai_bot/api/v1/meals.py`

### Storage & URLs
- [x] T037 [P] Generate presigned URLs for thumbnails and full images in `backend/src/calorie_track_ai_bot/services/storage.py`
- [x] T038 [P] Implement partial upload failure handling in `backend/src/calorie_track_ai_bot/api/v1/photos.py`

## Phase 3.4: Tests First - Frontend (TDD)

### Component Tests
- [x] T039 [P] Component test CalendarPicker in `frontend/tests/components/CalendarPicker.test.tsx`
- [x] T040 [P] Component test MealCard (expansion/collapse) in `frontend/tests/components/MealCard.test.tsx`
- [x] T041 [P] Component test PhotoCarousel (swipe, dots, arrows) in `frontend/tests/components/PhotoCarousel.test.tsx`
- [x] T042 [P] Component test MealEditor (edit/delete) in `frontend/tests/components/MealEditor.test.tsx`

### E2E Tests
- [x] T043 [P] E2E test: Calendar-based meal history (Scenario 4) in `frontend/tests/e2e/meals-history.spec.ts`
- [x] T044 [P] E2E test: Inline card expansion (Scenario 5) in `frontend/tests/e2e/meal-card-expansion.spec.ts`
- [x] T045 [P] E2E test: Photo carousel navigation (Scenario 6) in `frontend/tests/e2e/photo-carousel.spec.ts`
- [x] T046 [P] E2E test: Responsive stats graphs (Scenario 9) in `frontend/tests/e2e/stats-responsive.spec.ts`

## Phase 3.5: Frontend Implementation (ONLY after tests are failing)

### UI Components
- [x] T047 [P] Create CalendarPicker component with react-day-picker in `frontend/src/components/CalendarPicker.tsx`
- [x] T048 [P] Create PhotoCarousel component with swiper.js in `frontend/src/components/PhotoCarousel.tsx`
- [x] T049 Create MealCard component with inline expansion in `frontend/src/components/MealCard.tsx`
- [x] T050 Create MealEditor modal component in `frontend/src/components/MealEditor.tsx`

### Pages & Services
- [x] T051 Rename Today.tsx to Meals.tsx and add calendar navigation in `frontend/src/pages/Meals.tsx`
- [x] T052 Update Stats.tsx with responsive chart config in `frontend/src/pages/Stats.tsx`
- [x] T053 [P] Create useMeals hook for data fetching in `frontend/src/hooks/useMeals.ts`
- [x] T054 [P] Update meals service with CRUD operations in `frontend/src/services/meals.ts`
- [x] T055 [P] Update API client for new endpoints in `frontend/src/services/api.ts`

## Phase 3.6: Integration & Validation

### Backend-Frontend Integration
- [x] T056 Connect frontend Meals page to backend API in `frontend/src/pages/Meals.tsx` and `frontend/src/services/meals.ts`
- [x] T057 Test meal editing flow end-to-end in `frontend/tests/e2e/meal-editing-flow.spec.ts`
- [x] T058 Test meal deletion flow end-to-end in `frontend/tests/e2e/meal-deletion-flow.spec.ts`
- [x] T059 Verify presigned URL generation for images in `backend/src/calorie_track_ai_bot/services/storage.py`
- [x] T060 Test calendar date filtering in `frontend/tests/e2e/calendar-filtering.spec.ts`

### Validation Against Quickstart Scenarios
- [x] T061 [P] Validate Scenario 1: Multi-photo meal submission (bot)
- [x] T062 [P] Validate Scenario 2: Multi-photo without text
- [x] T063 [P] Validate Scenario 3: 5-photo limit enforcement
- [x] T064 [P] Validate Scenario 4: Calendar-based meal history
- [x] T065 [P] Validate Scenario 5: Inline meal card expansion
- [x] T066 [P] Validate Scenario 6: Instagram-style carousel
- [x] T067 [P] Validate Scenario 7: Meal editing
- [x] T068 [P] Validate Scenario 8: Meal deletion
- [x] T069 [P] Validate Scenario 9: Responsive stats graphs
- [x] T070 [P] Validate Scenario 10: Thumbnail vs full image

## Phase 3.7: Polish & Quality

### Performance & Optimization
- [x] T071 [P] Optimize image loading (lazy load, thumbnails) in frontend
- [x] T072 [P] Add loading states for async operations
- [x] T073 [P] Implement optimistic updates for meal editing
- [x] T074 Verify API response times <200ms (P95) - validates NFR-001 (best-effort performance)
- [x] T075 Test page load time <2s - validates NFR-001 performance goals

### Accessibility & Responsiveness
- [x] T076 [P] Add ARIA labels to calendar and carousel
- [x] T077 [P] Test keyboard navigation (arrow keys, tab)
- [x] T078 [P] Test screen reader compatibility
- [x] T079 Verify responsive design (320px-428px widths)
- [x] T080 Fix any horizontal scroll issues on mobile

### Code Quality
- [x] T081 Run linter: `cd backend && uv run ruff check`
- [x] T082 Run type checker: `cd backend && uv run pyright`
- [x] T083 [P] Run frontend linter: `cd frontend && npm run lint`
- [x] T084 [P] Verify test coverage >80%: `cd backend && uv run pytest --cov`
- [x] T085 Remove code duplication and refactor

### Documentation
- [x] T086 [P] Update API documentation with new endpoints
- [x] T087 [P] Add frontend component documentation
- [x] T088 [P] Update README with new features
- [x] T089 Document database schema changes

## Dependencies Graph

```
Setup (T001-T004) → All other tasks

Backend Tests (T005-T019) → Backend Implementation (T020-T038)
  ├─ T005-T011 (Contract tests) → T032-T036 (API endpoints)
  ├─ T012-T014 (Service tests) → T024-T031 (Services)
  └─ T015-T019 (Integration tests) → T056-T060 (Integration)

Frontend Tests (T039-T046) → Frontend Implementation (T047-T055)
  ├─ T039-T042 (Component tests) → T047-T050 (Components)
  └─ T043-T046 (E2E tests) → T051-T052 (Pages)

Backend + Frontend Implementation → Integration (T056-T060)
Integration → Validation (T061-T070)
Validation → Polish (T071-T089)
```

## Parallel Execution Examples

### Backend Tests (can run in parallel)
```bash
# T005-T011: Contract tests
cd backend
uv run pytest tests/api/v1/test_meals_list.py tests/api/v1/test_meals_get.py tests/api/v1/test_meals_update.py tests/api/v1/test_meals_delete.py tests/api/v1/test_meals_calendar.py tests/api/v1/test_photos_multiphotos.py tests/api/v1/test_estimates_multiphotos.py -v

# T012-T014: Service tests
uv run pytest tests/services/test_telegram_media_groups.py tests/services/test_estimator_multiphotos.py tests/services/test_photo_validation.py -v

# T015-T019: Integration tests
uv run pytest tests/integration/ -v
```

### Frontend Tests (can run in parallel)
```bash
# T039-T042: Component tests
cd frontend
npm run test -- CalendarPicker.test.tsx MealCard.test.tsx PhotoCarousel.test.tsx MealEditor.test.tsx

# T043-T046: E2E tests
npm run test:e2e -- meals-history.spec.ts meal-card-expansion.spec.ts photo-carousel.spec.ts stats-responsive.spec.ts
```

### Backend Implementation (parallelizable parts)
```bash
# T020-T021: Schema updates (different model classes)
# T022-T023: Database queries (different functions)
# T037-T038: Storage utilities (different files)
```

### Frontend Implementation (parallelizable parts)
```bash
# T047-T048: Independent components
# T053-T055: Services and hooks (different files)
```

### Validation (can run in parallel)
```bash
# T061-T070: All quickstart scenarios
cd backend
uv run pytest tests/integration/test_multiphotos_workflow.py tests/integration/test_multiphotos_no_text.py tests/integration/test_photo_limit.py tests/integration/test_meal_editing.py tests/integration/test_meal_deletion.py -v

cd ../frontend
npm run test:e2e
```

## Task Execution Notes

### TDD Workflow
1. **Red Phase**: Write tests first (T005-T019, T039-T046) - All tests MUST fail
2. **Green Phase**: Implement to pass tests (T020-T038, T047-T055) - Make tests pass
3. **Refactor Phase**: Clean up code (T085) - Tests still pass

### Key Reminders
- [ ] Run `uv run ruff check` and `uv run pyright` after each backend change (per user rules)
- [ ] Verify tests fail before implementing
- [ ] No [P] tasks should modify the same file
- [ ] Commit after each completed task
- [ ] Integration tests bridge backend and frontend

### Quality Gates
- All tests passing before moving to next phase
- Code coverage >80% maintained
- Linting and type checking clean
- Responsive design validated (320px-428px)
- API performance <200ms P95
- No horizontal scroll on any page

---

**Total Tasks**: 89 (Setup: 4, Backend Tests: 15, Backend Impl: 19, Frontend Tests: 8, Frontend Impl: 9, Integration: 15, Polish: 19)

**Estimated Completion**: Backend (2-3 days), Frontend (2-3 days), Integration & Polish (1-2 days) = **5-8 days total**

**Next Step**: Start with T001 (database migration), then proceed with TDD workflow
