# Tasks: Telegram Food Photo Nutrition Analyzer

**Input**: Design documents from `/specs/001-description-i-am/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Extract: tech stack, libraries, structure
2. Load design documents:
   → data-model.md: Extract entities → model tasks
   → contracts/: Map endpoints → contract test tasks
   → research.md: Extract decisions → setup tasks
3. Generate tasks by category:
   → Setup → Tests → Core → Integration → Polish
4. Apply task rules:
   → Different files = mark [P] for parallel; same file = sequential
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Create dependency graph
7. Validate completeness
8. Return: SUCCESS (tasks ready)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Phase 3.1: Setup
- [x] T001 Create Mini App scaffold from community template (reference in README) [docs only]
- [x] T002 Ensure backend FastAPI project uses Python 3.12 (verify `backend/pyproject.toml`)
- [x] T003 [P] Configure linting/type-check hooks in Makefile (`uv run ruff check`, `uv run pyright`, `uv run pytest`)
- [x] T004 [P] Add `.env.example` fields per backend README and constitution

## Phase 3.2: Tests First (TDD)
- [x] T005 [P] Contract test POST `/api/v1/photos` in `backend/tests/api/v1/test_photos.py` (presign schema)
- [x] T006 [P] Contract test POST `/api/v1/photos/{photo_id}/estimate` in `backend/tests/api/v1/test_estimates.py`
- [x] T007 [P] Contract test GET `/api/v1/estimates/{estimate_id}` in `backend/tests/api/v1/test_estimates.py`
- [x] T008 [P] Contract test POST `/api/v1/meals` in `backend/tests/api/v1/test_meals.py`
- [x] T009 [P] Bot webhook flow test in `backend/tests/api/v1/test_bot.py` (photo message → enqueue)
- [x] T010 [P] Mini App auth test in `backend/tests/api/v1/test_auth.py`
- [x] T011 Integration test: Today view totals (backend aggregation) in `backend/tests/services/test_db.py`

## Phase 3.3: Core Implementation
- [x] T012 [P] Implement `User`, `FoodPhoto`, `Estimate`, `Meal`, `Goal` models in `backend/src/calorie_track_ai_bot/schemas.py` and persistence layer in `backend/src/calorie_track_ai_bot/services/db.py`
- [x] T013 [P] Presign upload endpoint `POST /api/v1/photos` in `backend/src/calorie_track_ai_bot/api/v1/photos.py`
- [x] T014 [P] Enqueue estimate endpoint `POST /api/v1/photos/{photo_id}/estimate` in `backend/src/calorie_track_ai_bot/api/v1/estimates.py`
- [x] T015 [P] Get estimate endpoint `GET /api/v1/estimates/{estimate_id}` in `backend/src/calorie_track_ai_bot/api/v1/estimates.py`
- [x] T016 [P] Create meal endpoint `POST /api/v1/meals` in `backend/src/calorie_track_ai_bot/api/v1/meals.py`
- [x] T017 [P] Telegram webhook `POST /bot` minimal flow in `backend/src/calorie_track_ai_bot/api/v1/bot.py`
- [x] T018 [P] Worker: consume queue, call vision, persist estimate in `backend/src/calorie_track_ai_bot/workers/estimate_worker.py`

## Phase 3.4: Integration
- [x] T019 Wire presigned URLs to Tigris (no proxy) in `backend/src/calorie_track_ai_bot/services/storage.py`
- [x] T020 Redis queue integration in `backend/src/calorie_track_ai_bot/services/queue.py`
- [x] T021 OpenAI Vision integration in `backend/src/calorie_track_ai_bot/services/estimator.py`
- [x] T022 Supabase Postgres integration (RLS-aware) in `backend/src/calorie_track_ai_bot/services/db.py`
- [x] T023 Internationalization baseline (EN, RU) in bot replies and Mini App strings (docs)
- [x] T024 Share action entry point in Mini App (docs)

## Phase 3.5: Polish
- [x] T025 [P] Unit tests for estimator edge cases in `backend/tests/services/test_estimator.py`
- [x] T026 [P] Unit tests for queue idempotency in `backend/tests/services/test_queue.py`
- [x] T027 [P] Unit tests for storage mime-type validation in `backend/tests/services/test_storage.py`
- [x] T028 Performance validation: webhook/presign p95 and e2e estimate P95 (docs)
- [x] T029 [P] Update `specs/001-description-i-am/quickstart.md` with Mini App setup steps
- [x] T030 [P] Update `README.md` references and environment variable tables

## Dependencies
- Tests (T005–T011) before implementation (T012–T018)
- T012 unblocks T013–T016, T022
- T017 unblocks T019–T021
- Implementation before polish (T025–T030)

## Parallel Example
```
# Launch contract tests together (different files):
T005, T006, T007, T008, T009, T010
```

## Validation Checklist
- [x] All contracts have corresponding tests (T005–T010)
- [x] All entities have model tasks (T012)
- [x] All tests come before implementation
- [x] Parallel tasks truly independent
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
