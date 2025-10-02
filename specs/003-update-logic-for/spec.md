# Feature Specification: Multi-Photo Meal Tracking & Enhanced Meals History

**Feature Branch**: `003-update-logic-for`
**Created**: September 30, 2025
**Status**: Ready for Planning
**Input**: User description: "update logic for telegram bot, for now it's using one estimate per photo even it user send two photos in one message bot will indentify it's as a two separate estimates. I need to update this logic: if user send more that one photos in one message and a clarifiyng text follow to this that means it's a one meal and additional photos acts as a different angle of the same meal to make better estimate. As well I need to fix some UI: let's rework "today" page into "meals" and this is where user can see past history of their meals. User should be able to see not only today's meals but go back in time and have a list of all his meals. Probably it should be a calendar style, or maybe just a list with a dates (i'm not sure what fits best). As well replace "apple" icon to a small preview photo of a meal which user sent. Make sure that we store macronutritient information and show it in UI as well. Fix "stats" page to show week/month graphs properly to fit the wide of the mobile screen."

## Execution Flow (main)
```
1. Parse user description from Input
   → SUCCESS: Feature involves bot logic update and UI enhancements
2. Extract key concepts from description
   → Identified: multi-photo handling, meal history, visual improvements, macronutrient display
3. For each unclear aspect:
   → RESOLVED: All clarifications provided by stakeholder
4. Fill User Scenarios & Testing section
   → SUCCESS: Clear user flows identified
5. Generate Functional Requirements
   → Each requirement testable and unambiguous
6. Identify Key Entities
   → Meal, Photo, MacronutrientData entities identified
7. Run Review Checklist
   → SUCCESS: All requirements clear and testable
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## Clarifications

### Session 2025-09-30

- Q: When a user sends multiple photos (e.g., 3 photos) in one message, what should happen if one photo fails to upload or is corrupted? → A: Process successfully uploaded photos only - create estimate with available photos
- Q: What are the acceptable performance targets for the calorie estimation process when multiple photos are submitted? → A: Best effort - no specific target, process as fast as possible
- Q: When a user taps on a meal entry thumbnail in the meals list, what should happen? → A: Expand inline - show full nutritional details and carousel within the list
- Q: Should the system allow users to edit or delete meals after they have been created? → A: Edit and delete - users can both edit meal details and delete meals
- Q: When submitting multiple photos for calorie estimation, how should the AI estimation service process them? → A: Combined analysis - send all photos together for holistic multi-angle analysis

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story

As a calorie tracking user, when I send multiple photos of the same meal from different angles to the Telegram bot along with a description, I want the system to recognize them as a single meal and use all photos to create one comprehensive calorie estimate. I also want to browse my complete meal history beyond just today's entries, see visual previews of my meals, view detailed macronutrient breakdowns, and see properly formatted statistics on my mobile device.

### Acceptance Scenarios

1. **Given** a user is in the Telegram bot chat, **When** they send 3 photos in one message followed by text "Chicken pasta dinner", **Then** the system creates a single meal estimate using all 3 photos for better accuracy

2. **Given** a user is in the Telegram bot chat, **When** they send 2 photos in one message without any text, **Then** the system creates a single meal estimate based only on the photos

3. **Given** a user opens the meals page, **When** they first access it, **Then** they see today's meals by default with a calendar picker available

4. **Given** a user is on the meals page, **When** they select a date from the calendar picker, **Then** they see all meals from that selected date

5. **Given** a user views their meals list, **When** they look at a meal entry, **Then** they see a thumbnail preview of the actual meal photo instead of a generic icon

6. **Given** a user views a meal entry in the list, **When** they tap on the meal thumbnail, **Then** the entry expands inline to show full nutritional details and photo carousel

7. **Given** a user views an expanded meal with multiple photos, **When** they interact with the carousel, **Then** they can swipe through photos with Instagram-style carousel (dots at bottom, arrows on sides)

8. **Given** a user views an expanded meal entry, **When** they examine the nutritional information, **Then** they see detailed macronutrient breakdown in grams (protein, carbs, fats)

9. **Given** a user opens the stats page on their mobile device, **When** they view weekly or monthly graphs, **Then** the graphs are properly sized to fit the mobile screen width without overflow

10. **Given** a user sends a single photo with or without text, **When** the bot processes it, **Then** it creates a single meal estimate

11. **Given** a user attempts to send 6 photos in one message, **When** the bot receives it, **Then** the system displays an informational message about the 5-photo limit

12. **Given** a user views an expanded meal entry, **When** they choose to edit the meal, **Then** they can modify meal details (description, nutritional values)

13. **Given** a user views an expanded meal entry, **When** they choose to delete the meal, **Then** the meal is removed from their history

### Edge Cases

- What happens when a user sends photos in one message but the text arrives in a separate message? (Text is ignored if not in same message; estimate created from photos only)
- What happens when a user sends 6+ photos in one message? (System enforces 5-photo limit and displays informational message)
- How does the system handle corrupted or invalid photo files in a multi-photo message? (Process successfully uploaded photos only; create estimate with available photos)
- What happens when meal history extends beyond 1 year? (Data older than 1 year is not retained/displayed)
- How should the system handle meals without photos when displaying thumbnails? (Display placeholder or default icon)
- What happens when network issues prevent all photos from uploading? (Process successfully uploaded photos; if none succeed, handle as error)
- How does the carousel behave with a single photo? (No carousel controls shown for single photo meals)

## Requirements *(mandatory)*

### Functional Requirements

**Bot Photo Processing:**
- **FR-001**: System MUST detect when multiple photos are sent in a single Telegram message
- **FR-002**: System MUST associate text caption within the same message with the photo group to form a single meal entry
- **FR-003**: System MUST use all photos in a group to generate one comprehensive calorie and macronutrient estimate
- **FR-004**: System MUST send all photos together to AI estimation service for holistic multi-angle analysis
- **FR-005**: System MUST create estimate from photos only if no text is provided in the same message
- **FR-006**: System MUST support single photo with or without text as a single meal (existing behavior)
- **FR-007**: System MUST enforce a maximum limit of 5 photos per message
- **FR-008**: System MUST display an informational message when user attempts to send more than 5 photos, explaining the limit and capability
- **FR-009**: System MUST process successfully uploaded photos when some photos fail or are corrupted, creating estimate with available photos

**Meal History & Display:**
- **FR-010**: System MUST rename "Today" page to "Meals" page
- **FR-011**: System MUST display today's meals by default when opening the Meals page
- **FR-012**: System MUST provide a calendar picker for selecting historical dates
- **FR-013**: System MUST allow users to view meals from any date within the past year
- **FR-014**: System MUST display meal entries with photo thumbnails instead of generic apple icons
- **FR-015**: System MUST expand meal entry inline when user taps on thumbnail to show full nutritional details and photo carousel
- **FR-016**: System MUST display multi-photo meals with Instagram-style carousel (navigation dots at bottom, arrows on sides)
- **FR-017**: System MUST hide carousel controls for single-photo meals
- **FR-018**: System MUST show macronutrient information in grams (protein, carbohydrates, fats) for each meal
- **FR-019**: System MUST persist macronutrient data for all meals

**Meal Management:**
- **FR-020**: System MUST allow users to edit meal details including description and nutritional values
- **FR-021**: System MUST allow users to delete meals from their history
- **FR-022**: System MUST update statistics and summaries when meals are edited or deleted

**Visual & Responsiveness:**
- **FR-023**: System MUST display statistics graphs (week/month) properly sized for mobile screen width
- **FR-024**: System MUST prevent horizontal scrolling on stats page graphs
- **FR-025**: System MUST maintain graph readability when scaled to mobile dimensions

**Data Management:**
- **FR-026**: System MUST store association between multiple photos and a single meal
- **FR-027**: System MUST store macronutrient breakdown data with precision in grams
- **FR-028**: System MUST retain meal history for 1 year from meal creation date
- **FR-029**: System MUST not display meals older than 1 year in the history

### Non-Functional Requirements

**Performance:**
- **NFR-001**: Calorie estimation processing should use best-effort approach with no specific time constraint; optimize for speed without guaranteed SLA

### Key Entities *(include if feature involves data)*

- **Meal**: Represents a food intake event; contains timestamp, user identifier, description/caption, calorie estimate, macronutrient breakdown (protein, carbs, fats), and reference to one or more photos

- **Photo**: Represents an image of food; contains image data/reference, upload timestamp, association to a Meal (one-to-many relationship where one Meal can have multiple Photos)

- **MacronutrientData**: Nutritional breakdown associated with a Meal; contains protein amount, carbohydrate amount, fat amount, measurement units, and calculation confidence/source

- **MealHistory**: Collection of Meals for a user; supports filtering by date range, pagination for display, and chronological ordering

- **DailySummary**: Aggregated daily nutrition data; contains total calories and macronutrients for a day; automatically updated when meals are created, edited, or deleted

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain - **All clarifications resolved**
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

**Resolved Decisions:**
1. ✅ Single photo with or without text creates estimate immediately
2. ✅ Calendar picker UI with today's meals shown by default
3. ✅ 1 year meal history retention and access
4. ✅ Text must be in same message as photos; otherwise photos-only estimate
5. ✅ 5 photo maximum per meal with informational message
6. ✅ Instagram-style carousel for multi-photo display
7. ✅ Macronutrient precision in grams
8. ✅ 1 year data retention policy

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked and resolved
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed
- [x] All clarifications obtained and incorporated

---
