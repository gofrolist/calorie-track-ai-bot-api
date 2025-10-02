# Quickstart: Multi-Photo Meal Tracking & Enhanced Meals History

**Feature**: 003-update-logic-for
**Purpose**: Validate feature implementation through user story scenarios

## Prerequisites

### Environment Setup
```bash
# Backend
cd backend
uv sync --all-extras
cp .env.example .env
# Fill in: TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, SUPABASE_URL, SUPABASE_DB_PASSWORD, etc.

# Database migration
psql "$SUPABASE_DATABASE_URL" -f ../supabase/migrations/[timestamp]_multiphotos_meals.sql

# Frontend
cd ../frontend
npm install

# Start services
cd ../backend && uv run uvicorn src.calorie_track_ai_bot.main:app --reload &
cd ../frontend && npm run dev &
```

### Test Data Setup
```bash
# Run integration test data seeder
cd backend
uv run pytest tests/integration/test_multiphotos_workflow.py --setup-only
```

## Validation Scenarios

### Scenario 1: Multi-Photo Meal Submission (Bot)

**User Story**: Send 3 photos in one message with text caption

**Steps**:
1. Open Telegram bot chat
2. Select 3 photos from camera roll
3. Add caption: "Chicken pasta dinner"
4. Send message
5. Wait for bot response

**Expected Result**:
- ✅ Bot acknowledges message: "Processing 3 photos for your meal..."
- ✅ Single estimate created (not 3 separate ones)
- ✅ Estimate includes macronutrients: protein, carbs, fats in grams
- ✅ Bot replies with total calories and macro breakdown
- ✅ Meal appears in mini-app with all 3 photos

**API Validation**:
```bash
# Check photo grouping
curl http://localhost:8000/api/v1/meals/{meal_id} \
  -H "Authorization: Bearer $TOKEN" | jq '.photos | length'
# Expected: 3

# Check macronutrients
curl http://localhost:8000/api/v1/meals/{meal_id} \
  -H "Authorization: Bearer $TOKEN" | jq '.macronutrients'
# Expected: {"protein": 45.5, "carbs": 75.0, "fats": 18.2}
```

### Scenario 2: Multi-Photo Without Text

**User Story**: Send 2 photos in one message without caption

**Steps**:
1. Open Telegram bot chat
2. Select 2 photos
3. Send without caption
4. Wait for bot response

**Expected Result**:
- ✅ Bot processes photos without text
- ✅ Single estimate created from photos only
- ✅ Meal created with empty/null description
- ✅ Both photos associated with meal

**API Validation**:
```bash
curl http://localhost:8000/api/v1/meals/{meal_id} \
  -H "Authorization: Bearer $TOKEN" | jq '{description, photo_count: (.photos | length)}'
# Expected: {"description": null, "photo_count": 2}
```

### Scenario 3: 5-Photo Limit Enforcement

**User Story**: Attempt to send 6 photos in one message

**Steps**:
1. Open Telegram bot chat
2. Select 6 photos
3. Send message
4. Wait for bot response

**Expected Result**:
- ✅ Bot sends informational message: "⚠️ Maximum 5 photos allowed per meal. You can upload up to 5 photos in one message for better calorie estimation."
- ✅ Only first 5 photos processed
- ✅ Meal created with 5 photos

**API Validation**:
```bash
curl http://localhost:8000/api/v1/photos \
  -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"photos": [{}, {}, {}, {}, {}, {}]}'
# Expected: 400 Bad Request - "Maximum 5 photos allowed per meal"
```

### Scenario 4: Calendar-Based Meal History (Mini-App)

**User Story**: View meals from last week using calendar picker

**Steps**:
1. Open mini-app
2. Navigate to "Meals" page (formerly "Today")
3. See today's meals displayed by default
4. Tap calendar icon
5. Select date from last week
6. View meals from that date

**Expected Result**:
- ✅ Page title shows "Meals" (not "Today")
- ✅ Today's date selected by default
- ✅ Calendar shows dates with meal indicators (dots/badges)
- ✅ Dates older than 1 year are disabled/grayed out
- ✅ Future dates are disabled
- ✅ Selected date shows meals from that day only
- ✅ No data message if no meals on selected date

**Frontend Validation**:
```bash
# Check calendar component
npm run test -- MealCalendar.test.tsx

# E2E test
npm run test:e2e -- meals-history.spec.ts
```

### Scenario 5: Inline Meal Card Expansion

**User Story**: Tap meal thumbnail to expand and view details

**Steps**:
1. On Meals page with meal list
2. Tap on meal thumbnail image
3. View expanded meal details
4. Tap another meal
5. Tap same meal again to collapse

**Expected Result**:
- ✅ Meal card expands smoothly (animation)
- ✅ Shows photo carousel (if multiple photos)
- ✅ Displays macronutrients: "Protein: 45g | Carbs: 75g | Fats: 18g"
- ✅ Edit and Delete buttons visible
- ✅ Previous expanded card collapses when new one opens
- ✅ Scroll position preserved

**Component Validation**:
```bash
npm run test -- MealCard.test.tsx
# Test: should expand on thumbnail click
# Test: should show carousel for multi-photo meals
# Test: should display macronutrients in grams
# Test: should collapse others when expanding new card
```

### Scenario 6: Instagram-Style Photo Carousel

**User Story**: Swipe through multiple meal photos

**Steps**:
1. Expand meal with 3 photos
2. Swipe left on photo carousel
3. Swipe right
4. Tap pagination dot
5. Use arrow buttons (if visible)

**Expected Result**:
- ✅ Carousel shows first photo by default
- ✅ Smooth swipe transition
- ✅ Pagination dots at bottom (1 active, 2 inactive)
- ✅ Navigation arrows on sides (desktop/tablet)
- ✅ For single photo: no carousel controls shown
- ✅ Keyboard navigation works (arrow keys)

**Component Validation**:
```bash
npm run test -- PhotoCarousel.test.tsx
# Test: should navigate on swipe
# Test: should update active dot on navigation
# Test: should hide controls for single photo
```

### Scenario 7: Meal Editing

**User Story**: Edit meal description and macronutrients

**Steps**:
1. Expand a meal card
2. Tap "Edit" button
3. Update description: "Updated: Grilled chicken pasta"
4. Change protein to 50g, carbs to 70g, fats to 20g
5. Save changes
6. Verify update

**Expected Result**:
- ✅ Edit modal/form opens
- ✅ Current values pre-filled
- ✅ Changes saved successfully
- ✅ Meal card updates immediately (optimistic update)
- ✅ Calories recalculated automatically (50*4 + 70*4 + 20*9 = 660 kcal)
- ✅ Daily summary updates

**API Validation**:
```bash
curl -X PATCH http://localhost:8000/api/v1/meals/{meal_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated: Grilled chicken pasta", "protein_grams": 50, "carbs_grams": 70, "fats_grams": 20}' \
  | jq '{description, calories, macronutrients}'
# Expected: {"description": "Updated: Grilled chicken pasta", "calories": 660, "macronutrients": {...}}
```

### Scenario 8: Meal Deletion

**User Story**: Delete a meal from history

**Steps**:
1. Expand a meal card
2. Tap "Delete" button
3. Confirm deletion (if confirmation dialog shown)
4. Verify meal removed

**Expected Result**:
- ✅ Meal card removed from list
- ✅ Daily summary updated (calories and macros reduced)
- ✅ Associated photos deleted/unlinked
- ✅ Cannot retrieve deleted meal via API

**API Validation**:
```bash
curl -X DELETE http://localhost:8000/api/v1/meals/{meal_id} \
  -H "Authorization: Bearer $TOKEN"
# Expected: 204 No Content

curl http://localhost:8000/api/v1/meals/{meal_id} \
  -H "Authorization: Bearer $TOKEN"
# Expected: 404 Not Found
```

### Scenario 9: Responsive Stats Page Graphs

**User Story**: View weekly/monthly graphs on mobile without horizontal scroll

**Steps**:
1. Navigate to Stats page
2. View weekly graph
3. Switch to monthly graph
4. Rotate device (if mobile)
5. Resize browser window (if desktop)

**Expected Result**:
- ✅ Graphs fit mobile screen width (320px minimum)
- ✅ No horizontal scrolling required
- ✅ Labels readable (rotated if needed)
- ✅ Maintains aspect ratio
- ✅ Responsive to screen size changes
- ✅ Touch-friendly on mobile

**Visual Regression Test**:
```bash
npm run test:e2e -- stats-responsive.spec.ts
# Captures screenshots at 320px, 375px, 428px widths
# Compares against baseline
```

### Scenario 10: Photo Thumbnail vs Full Image

**User Story**: See photo thumbnail in list, full image in carousel

**Steps**:
1. View meals list
2. Observe meal thumbnails (small preview)
3. Expand meal to view carousel
4. Compare image quality

**Expected Result**:
- ✅ List shows optimized thumbnails (~150x150px)
- ✅ Thumbnails load quickly
- ✅ Carousel shows full-size images
- ✅ Full images load progressively/lazily
- ✅ Presigned URLs valid for 1 hour

**Performance Validation**:
```bash
# Check thumbnail size
curl -I "https://storage.example.com/thumbnail_url" | grep -i content-length
# Expected: < 50KB

# Check full image size
curl -I "https://storage.example.com/full_url" | grep -i content-length
# Expected: < 500KB
```

## Integration Test Execution

### Run All Scenarios
```bash
# Backend integration tests
cd backend
uv run pytest tests/integration/test_multiphotos_workflow.py -v

# Frontend E2E tests
cd ../frontend
npm run test:e2e -- meals-history.spec.ts

# Contract tests
cd ../backend
uv run pytest tests/api/v1/test_meals_management.py -v
uv run pytest tests/api/v1/test_estimates_multiphotos.py -v
```

### Coverage Report
```bash
cd backend
uv run pytest --cov=src/calorie_track_ai_bot --cov-report=html
# Open htmlcov/index.html to verify >80% coverage
```

## Acceptance Criteria Checklist

### Bot Multi-Photo Handling
- [ ] Detects media_group_id for grouped photos
- [ ] Creates single meal for multi-photo messages
- [ ] Processes text caption with photo group
- [ ] Enforces 5-photo limit with user message
- [ ] Handles partial upload failures gracefully

### AI Estimation
- [ ] Sends all photos to OpenAI in single request
- [ ] Returns macronutrients in grams (protein, carbs, fats)
- [ ] Calculates calories from macros (4-4-9 formula)
- [ ] Maintains confidence scoring

### Database & Storage
- [ ] One-to-many meal-photo relationship works
- [ ] Macronutrient fields stored correctly
- [ ] Queries filter meals older than 1 year
- [ ] Photos cascade delete with meals
- [ ] Presigned URLs generated for thumbnails and full images

### Frontend UI
- [ ] "Meals" page replaces "Today" page
- [ ] Calendar picker shows dates with meals
- [ ] Inline meal card expansion works smoothly
- [ ] Instagram-style carousel for multi-photo meals
- [ ] Macronutrients displayed in grams
- [ ] Edit/delete functionality works
- [ ] Stats graphs fit mobile screen (no horizontal scroll)
- [ ] Responsive design (320px-428px tested)

### Performance
- [ ] API response time <200ms (P95)
- [ ] Page load time <2s
- [ ] Smooth animations (60fps)
- [ ] Thumbnail optimization (<50KB per image)

## Troubleshooting

### Issue: Bot creates separate meals for each photo
**Solution**: Check media_group_id detection in bot handler. Verify 200ms wait window for photo aggregation.

### Issue: Horizontal scroll on Stats graphs
**Solution**: Verify Chart.js responsive config. Check container CSS: `width: 100%; max-width: 100vw; overflow: hidden;`

### Issue: Calendar shows future dates as selectable
**Solution**: Check DayPicker `disabled` prop: `(date) => date > new Date() || date < oneYearAgo`

### Issue: Macronutrients not displaying
**Solution**: Verify database migration applied. Check API response includes `macronutrients` field. Validate frontend TypeScript types.

---

**Success Criteria**: All scenarios pass, acceptance checklist complete, no regressions in existing functionality
