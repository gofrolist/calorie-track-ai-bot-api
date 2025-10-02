
# Implementation Plan: Multi-Photo Meal Tracking & Enhanced Meals History

**Branch**: `003-update-logic-for` | **Date**: 2025-09-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-update-logic-for/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Enable users to submit multiple photos of the same meal for improved AI calorie estimation through holistic multi-angle analysis. Transform "Today" page into comprehensive "Meals" history with calendar navigation (1-year retention), inline expandable meal cards with Instagram-style photo carousels, actual meal photo thumbnails replacing generic icons, and detailed macronutrient display in grams. Add meal editing/deletion capabilities with automatic statistics updates. Fix Stats page graphs to properly fit mobile screen width without horizontal scrolling.

**Technical Approach**: Update Telegram bot message handler to group multi-photo messages as single meal, modify AI estimation service to accept photo arrays for combined analysis, extend database schema for one-to-many meal-photo relationships and macronutrient storage, redesign frontend Meals page with calendar picker and expandable card components, implement responsive chart sizing for mobile Stats page.

## Technical Context
**Language/Version**: TypeScript 5.x, Python 3.11, React 18
**Primary Dependencies**: FastAPI, @telegram-apps/sdk, tma.js, Vite, OpenAI gpt-5-mini, Supabase CLI, Upstash Redis, Tigris Storage
**Storage**: Supabase PostgreSQL (users, meals, photos, estimates with macronutrients), Tigris S3-compatible (photo files), Upstash Redis (queue)
**Testing**: pytest (backend), Jest/Playwright (frontend), integration tests
**Target Platform**: Telegram WebApp (mobile-first), Fly.io (backend), Vercel (frontend)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Best-effort estimation processing, <200ms API response time, <2s page load
**Constraints**: Mobile-first responsive design, 5 photos max per meal, 1-year data retention, no horizontal scroll on graphs
**Scale/Scope**: Multi-user calorie tracking with multi-photo AI analysis, calendar-based meal history, inline meal management

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principles Compliance
- ✅ **AI-First Nutrition Analysis**: Enhances AI estimation with multi-photo holistic analysis for better accuracy
- ✅ **Telegram Bot Excellence**: Improves bot UX with multi-photo handling and clear user feedback (5-photo limit message)
- ✅ **API-First Architecture**: Extends existing RESTful API design with new endpoints for meal management
- ✅ **Test-Driven Development (NON-NEGOTIABLE)**: Will write tests first for all new functionality
- ✅ **Observability & Monitoring**: Maintains structured logging for multi-photo processing and user interactions
- ✅ **Internationalization & Accessibility**: Preserves existing i18n support, adds accessible calendar and carousel components
- ✅ **Modern UI/UX Excellence**: Implements Instagram-style carousel, calendar picker, responsive graphs - mobile-first design
- ✅ **Feature Flag Management**: Can implement gradual rollout for multi-photo feature and new UI components
- ✅ **Data Protection & Privacy**: Maintains GDPR compliance with 1-year retention policy, no new PII collection

### Technical Standards Compliance
- ✅ **Frontend Mini-App Requirements**: Uses React with modern components (calendar, carousel), responsive design, accessibility
- ✅ **Backend API Standards**: FastAPI with async patterns, structured logging, input validation (5-photo limit), rate limiting
- ✅ **AI/ML Pipeline Standards**: Updates OpenAI integration to send photo arrays for combined analysis, maintains confidence scoring

### CI/CD & DevOps Excellence
- ✅ **Continuous Integration**: Automated testing for new components, contract testing for API changes, accessibility testing
- ✅ **Continuous Deployment**: Can use feature flags for gradual rollout, blue-green deployment compatible
- ✅ **Infrastructure & Scaling**: No infrastructure changes required, uses existing Supabase/Tigris/Redis

### Data Protection & Disaster Recovery
- ✅ **Data Protection Standards**: 1-year retention policy explicit, maintains encryption, consent management
- ✅ **Disaster Recovery**: Standard backup procedures apply to new meal/photo data

### Quality Gates
- ✅ **Test Coverage**: Will maintain 80%+ coverage for new code
- ✅ **Security**: Input validation for photo count, file validation maintained
- ✅ **Performance**: Best-effort estimation aligns with existing patterns
- ✅ **Accessibility**: Calendar and carousel will be keyboard-navigable and screen-reader friendly
- ✅ **API Compatibility**: Backward compatible - extends existing endpoints, doesn't break old ones

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── src/calorie_track_ai_bot/
│   ├── api/v1/
│   │   ├── bot.py              # Telegram bot webhook handler (multi-photo detection)
│   │   ├── meals.py            # Meal CRUD endpoints (new: edit/delete)
│   │   ├── photos.py           # Photo upload endpoints (updated for multi-photo)
│   │   └── estimates.py        # Estimation endpoints (updated for multi-photo)
│   ├── services/
│   │   ├── telegram.py         # Bot message processing (group photos logic)
│   │   ├── estimator.py        # AI estimation service (multi-photo analysis)
│   │   ├── storage.py          # Photo storage service
│   │   └── db.py               # Database operations
│   ├── workers/
│   │   └── estimate_worker.py  # Background estimation worker (multi-photo)
│   └── schemas.py              # Pydantic models (updated with macronutrients)
└── tests/
    ├── api/v1/
    │   ├── test_bot_multiphotos.py       # Bot multi-photo handling tests
    │   ├── test_meals_management.py      # Meal edit/delete tests
    │   └── test_estimates_multiphotos.py # Multi-photo estimation tests
    ├── services/
    │   └── test_estimator_multiphotos.py # Estimator multi-photo logic tests
    └── integration/
        └── test_multiphotos_workflow.py  # End-to-end multi-photo tests

frontend/
├── src/
│   ├── pages/
│   │   ├── Meals.tsx           # NEW: Meals history page (was Today.tsx)
│   │   └── Stats.tsx           # UPDATED: Fixed responsive graphs
│   ├── components/
│   │   ├── MealCard.tsx        # NEW: Expandable meal card with carousel
│   │   ├── PhotoCarousel.tsx   # NEW: Instagram-style photo carousel
│   │   ├── CalendarPicker.tsx  # NEW: Date picker for meal history
│   │   └── MealEditor.tsx      # NEW: Meal edit/delete modal
│   ├── services/
│   │   ├── api.ts              # API client (updated for new endpoints)
│   │   └── meals.ts            # Meal service (CRUD operations)
│   └── hooks/
│       └── useMeals.ts         # NEW: Meal data fetching hook
└── tests/
    ├── components/
    │   ├── MealCard.test.tsx
    │   ├── PhotoCarousel.test.tsx
    │   └── CalendarPicker.test.tsx
    └── e2e/
        └── meals-history.spec.ts  # E2E tests for meal history flow

supabase/migrations/
└── [NEW]_multiphotos_meals.sql    # Schema updates for multi-photo support
```

**Structure Decision**: Web application architecture with separate backend (Python/FastAPI) and frontend (TypeScript/React). Backend handles Telegram bot logic, multi-photo processing, and API endpoints. Frontend implements calendar-based meal history with inline expandable cards and responsive charts. Database migrations extend existing schema for one-to-many meal-photo relationships and macronutrient storage.

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh cursor`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Load `.specify/templates/tasks-template.md` as base structure
2. Generate tasks from Phase 1 artifacts:
   - **From contracts/** → Contract test tasks (TDD - write tests first)
   - **From data-model.md** → Database migration + model tasks
   - **From quickstart.md** → Integration test scenarios
   - Implementation tasks to make all tests pass

**Task Categories** (in TDD order):
- **Setup**: Database migration, dependency updates
- **Tests First** (MUST complete before implementation):
  - Contract tests for updated APIs (meals, photos, estimates)
  - Integration tests for multi-photo workflow
  - Frontend component tests (MealCard, PhotoCarousel, CalendarPicker)
  - E2E tests for user scenarios
- **Implementation**:
  - Backend: Bot handler, estimator service, API endpoints, workers
  - Frontend: Components, pages, services, hooks
  - Database: Queries, indexes, data access layer
- **Integration**: Connect frontend to backend, test end-to-end
- **Polish**: Performance optimization, responsive design validation, documentation

**Ordering Strategy**:
- Strict TDD: All tests written and failing before implementation starts
- Backend tests → Backend implementation → Frontend tests → Frontend implementation
- Mark [P] for parallel tasks (different files/components)
- Dependencies respected (e.g., migration before models, models before services)

**Specific Task Areas**:
1. **Bot Multi-Photo** (5-7 tasks): Media group detection, photo aggregation, 5-photo limit
2. **AI Estimation** (3-4 tasks): Multi-photo API integration, macronutrient extraction
3. **Database** (4-5 tasks): Migration, queries, meal-photo relationship
4. **Meals API** (6-8 tasks): CRUD endpoints, calendar view, validation
5. **Frontend Meals Page** (8-10 tasks): Calendar picker, expandable cards, carousel
6. **Frontend Stats** (2-3 tasks): Responsive chart sizing, mobile optimization
7. **Testing** (10-12 tasks): Contract, integration, E2E, accessibility

**Estimated Output**: 45-55 numbered, ordered tasks in tasks.md

**Quality Gates**:
- All tests must fail initially (red phase)
- Implementation makes tests pass (green phase)
- Refactoring preserves test success
- Coverage remains >80%

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No constitutional violations | All requirements align with existing principles |

**Notes**: This feature extends existing architecture without adding complexity. Uses established patterns for multi-photo handling, UI components, and data modeling.

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) ✅ research.md created
- [x] Phase 1: Design complete (/plan command) ✅ data-model.md, contracts/, quickstart.md, agent context updated
- [x] Phase 2: Task planning complete (/plan command - describe approach only) ✅ Task strategy documented
- [x] Phase 3: Tasks generated (/tasks command) ✅ 89 tasks created in tasks.md - **Next step: Begin implementation**
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS ✅ No violations identified
- [x] Post-Design Constitution Check: PASS ✅ Design aligns with all principles
- [x] All NEEDS CLARIFICATION resolved ✅ No unknowns in Technical Context
- [x] Complexity deviations documented ✅ No deviations required

**Artifacts Generated**:
- ✅ `/specs/003-update-logic-for/research.md` - Technology decisions and best practices
- ✅ `/specs/003-update-logic-for/data-model.md` - Entity relationships and schema migrations
- ✅ `/specs/003-update-logic-for/contracts/meals-api.yaml` - Meals management API contract
- ✅ `/specs/003-update-logic-for/contracts/photos-estimates-api.yaml` - Multi-photo API contract
- ✅ `/specs/003-update-logic-for/quickstart.md` - Integration test scenarios
- ✅ `/specs/003-update-logic-for/tasks.md` - 89 ordered implementation tasks (TDD)
- ✅ `.cursor/rules/specify-rules.mdc` - Updated agent context

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
