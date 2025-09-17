# Tasks: Frontend Telegram Mini App

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
- [ ] T001 Create `frontend/` using community template (React+Vite or Next) — `frontend/`
- [ ] T002 Initialize project config: package.json scripts, tsconfig, eslint/prettier — `frontend/`
- [ ] T003 [P] Install deps: `@telegram-apps/sdk` or `tma.js`, i18n, axios/fetch wrapper — `frontend/`
- [ ] T004 [P] Add i18n scaffolding (EN, RU) — `frontend/src/i18n/`

## Phase 3.2: Tests First (TDD)
- [ ] T005 [P] Unit test: i18n loader selects EN/RU — `frontend/tests/i18n.test.ts`
- [ ] T006 [P] Contract tests: typed client shapes for `/photos`, `/photos/{id}/estimate`, `/estimates/{id}`, `/meals` — `frontend/tests/contracts/*.test.ts`
- [ ] T007 [P] Integration test (Playwright): Today view lists meals and totals — `frontend/tests/e2e/today.spec.ts`
- [ ] T008 [P] Integration test: Meal detail allows corrections and saves — `frontend/tests/e2e/meal-detail.spec.ts`
- [ ] T009 [P] Integration test: Goals update progress indicators — `frontend/tests/e2e/goals.spec.ts`

## Phase 3.3: Core Implementation
- [ ] T010 [P] App shell with Telegram WebApp integration — `frontend/src/main.tsx`, `frontend/src/app.tsx`
- [ ] T011 [P] API client wrapper with base URL, initData/session token, correlation ID — `frontend/src/services/api.ts`
- [ ] T012 [P] Today view: list + totals — `frontend/src/pages/today.tsx`
- [ ] T013 [P] Meal detail: edit and save — `frontend/src/pages/meal-detail.tsx`
- [ ] T014 [P] Week/Month stats with charts — `frontend/src/pages/stats.tsx`
- [ ] T015 [P] Goals UI — `frontend/src/pages/goals.tsx`
- [ ] T016 [P] Share action — `frontend/src/components/share.tsx`

## Phase 3.4: Integration
- [ ] T017 Configure backend base URL and environment handling — `frontend/src/config.ts`
- [ ] T018 Wire typed client to `/photos`, `/estimates`, `/meals` endpoints — `frontend/src/services/api.ts`
- [ ] T019 Error boundary and loading states — `frontend/src/components/*`
- [ ] T020 i18n strings for all screens (EN, RU) — `frontend/src/i18n/*`

## Phase 3.5: Polish
- [ ] T021 [P] Lighthouse pass: mobile performance and a11y — docs
- [ ] T022 [P] E2E happy-path runbook and screenshots — docs
- [ ] T023 [P] Update `frontend/README.md` with setup, scripts, deploy

## Dependencies
- Setup (T001–T004) → Tests (T005–T009) → Core (T010–T016) → Integration (T017–T020) → Polish (T021–T023)

## Parallel Example
```
# Parallelizable test tasks (different files):
T005, T006, T007, T008, T009
```

## Validation Checklist
- [ ] All contracts have corresponding tests
- [ ] All entities have model tasks
- [ ] All tests come before implementation
- [ ] Parallel tasks truly independent
- [ ] Each task specifies exact file path
- [ ] No task modifies same file as another [P] task
