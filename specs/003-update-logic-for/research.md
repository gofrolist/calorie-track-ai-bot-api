# Research: Multi-Photo Meal Tracking & Enhanced Meals History

**Date**: 2025-09-30
**Feature**: 003-update-logic-for

## Executive Summary

This research covers the technical approach for implementing multi-photo meal tracking with enhanced UI/UX components. All technical stack decisions leverage existing project infrastructure (FastAPI, React, Supabase PostgreSQL, Tigris storage, Upstash Redis).

## 1. Multi-Photo Message Handling in Telegram Bot

### Decision: Media Group Detection via Telegram API

**Rationale**:
- Telegram groups multiple photos sent in one message as a "media_group_id"
- All photos with same media_group_id arrive in separate update messages
- Bot can detect and aggregate these using media_group_id field
- Text caption (if present) arrives with the first photo in the group

**Implementation Approach**:
```python
# In bot message handler
if update.message.media_group_id:
    # Aggregate all photos with same media_group_id
    # Wait briefly (100-200ms) to collect all photos in group
    # Process as single meal once group is complete
else:
    # Single photo - process immediately
```

**Alternatives Considered**:
- Sequential processing: Rejected - creates multiple meals for same dish
- Time-based grouping: Rejected - unreliable, no clear association signal

**Best Practices**:
- Set max wait time of 200ms for media group completion
- Enforce 5-photo limit before AI processing
- Store media_group_id with photos for traceability
- Handle partial failures gracefully (process available photos)

## 2. Multi-Photo AI Analysis with OpenAI Vision

### Decision: Array-Based Combined Analysis

**Rationale**:
- OpenAI gpt-5-mini supports multiple images in single API call
- Combined analysis provides holistic view of meal from different angles
- More accurate portion estimation from multiple perspectives
- Single API call reduces latency vs sequential calls

**Implementation Approach**:
```python
# Send all photos as image array to OpenAI
response = await openai_client.chat.completions.create(
    model="gpt-5-mini",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            *[{"type": "image_url", "image_url": url} for url in photo_urls]
        ]
    }]
)
```

**Alternatives Considered**:
- Sequential analysis + aggregation: Rejected - less accurate, slower
- Separate calls + averaging: Rejected - loses inter-photo context
- Hybrid approach: Rejected - unnecessary complexity for gpt-5-mini capabilities

**Best Practices**:
- Include photo count in prompt for context
- Request macronutrient breakdown (protein/carbs/fats in grams)
- Maintain existing confidence scoring mechanism
- Log individual photo URLs for debugging

## 3. Database Schema for One-to-Many Photo Relationships

### Decision: Separate Photos Table with meal_id Foreign Key

**Rationale**:
- PostgreSQL handles one-to-many naturally with foreign keys
- Allows flexible photo count per meal (1-5)
- Enables efficient querying with JOIN or array_agg
- Supports individual photo metadata (upload time, size, order)

**Schema Design**:
```sql
-- Extend existing meals table
ALTER TABLE meals ADD COLUMN protein_grams DECIMAL(6,2);
ALTER TABLE meals ADD COLUMN carbs_grams DECIMAL(6,2);
ALTER TABLE meals ADD COLUMN fats_grams DECIMAL(6,2);

-- Photos table already exists, add meal relationship
ALTER TABLE photos ADD COLUMN meal_id UUID REFERENCES meals(id);
ALTER TABLE photos ADD COLUMN display_order INTEGER DEFAULT 0;
ALTER TABLE photos ADD COLUMN media_group_id VARCHAR(255);
CREATE INDEX idx_photos_meal_id ON photos(meal_id);
CREATE INDEX idx_photos_media_group ON photos(media_group_id);
```

**Alternatives Considered**:
- JSON array in meals table: Rejected - harder to query, no referential integrity
- Separate junction table: Rejected - unnecessary for simple one-to-many
- Embedded photo URLs: Rejected - inflexible, poor normalization

**Best Practices**:
- Add display_order for carousel photo sequence
- Keep media_group_id for Telegram traceability
- Use CASCADE DELETE for meal deletion
- Index meal_id for efficient photo fetching

## 4. React Calendar Picker for Mobile

### Decision: react-day-picker with Custom Mobile Styling

**Rationale**:
- Lightweight (~15KB), widely used in React ecosystem
- Excellent mobile touch support
- Highly customizable with CSS
- Accessible (ARIA labels, keyboard navigation)
- Works well with Telegram WebApp constraints

**Implementation Approach**:
```tsx
import { DayPicker } from 'react-day-picker';

<DayPicker
  mode="single"
  selected={selectedDate}
  onSelect={handleDateChange}
  disabled={(date) => date > new Date() || date < oneYearAgo}
  modifiers={{ hasData: datesWithMeals }}
  className="mobile-optimized"
/>
```

**Alternatives Considered**:
- react-datepicker: Rejected - heavier bundle, less mobile-optimized
- Native input[type="date"]: Rejected - inconsistent across browsers/Telegram
- Custom implementation: Rejected - unnecessary complexity

**Best Practices**:
- Show visual indicators on dates with meals
- Disable future dates and dates >1 year old
- Use bottom sheet pattern for mobile presentation
- Provide quick navigation (today, this week buttons)
- Optimize for touch targets (min 44x44px)

## 5. Instagram-Style Photo Carousel in React

### Decision: swiper.js with Custom Controls

**Rationale**:
- Industry-standard carousel library (used by Instagram)
- Excellent touch/swipe gestures
- Supports pagination dots and navigation arrows
- Lazy loading for performance
- RTL support for internationalization

**Implementation Approach**:
```tsx
import { Swiper, SwiperSlide } from 'swiper/react';
import { Navigation, Pagination } from 'swiper/modules';

<Swiper
  modules={[Navigation, Pagination]}
  navigation={photos.length > 1}
  pagination={{ clickable: true }}
  loop={false}
  spaceBetween={10}
>
  {photos.map(photo => (
    <SwiperSlide key={photo.id}>
      <img src={photo.url} alt={photo.description} />
    </SwiperSlide>
  ))}
</Swiper>
```

**Alternatives Considered**:
- react-slick: Rejected - older, heavier, less mobile-optimized
- Custom CSS scroll-snap: Rejected - lacks pagination/navigation controls
- Pure React implementation: Rejected - reinventing the wheel

**Best Practices**:
- Hide controls for single-photo meals
- Use lazy loading for off-screen images
- Optimize image sizes (thumbnails in list, full in expanded view)
- Add keyboard navigation (arrow keys)
- Include ARIA labels for accessibility

## 6. Responsive Chart Sizing for Mobile

### Decision: Container Query + Responsive Chart Config

**Rationale**:
- Charts must adapt to mobile screen width (typically 320-428px)
- Current charts likely use fixed width causing overflow
- Chart.js/Recharts support responsive sizing natively
- Container queries prevent parent layout issues

**Implementation Approach**:
```tsx
// For Chart.js
const options = {
  responsive: true,
  maintainAspectRatio: true,
  aspectRatio: 2, // width:height ratio optimized for mobile
  scales: {
    x: {
      ticks: {
        maxRotation: 45,
        minRotation: 45,
        font: { size: 10 } // Smaller labels for mobile
      }
    }
  }
};

// Container
<div style={{ width: '100%', maxWidth: '100vw', overflow: 'hidden' }}>
  <Chart data={data} options={options} />
</div>
```

**Alternatives Considered**:
- Fixed small size: Rejected - poor readability
- Horizontal scrolling: Rejected - bad UX per requirements
- Separate mobile charts: Rejected - unnecessary duplication

**Best Practices**:
- Use percentage-based widths (100% of container)
- Adjust font sizes for mobile (10-12px labels)
- Reduce tick count for narrow screens
- Use responsive aspectRatio (2:1 for mobile)
- Test on 320px width (iPhone SE minimum)

## 7. Inline Expandable Meal Cards

### Decision: Accordion Pattern with Smooth Animation

**Rationale**:
- Common mobile pattern, intuitive for users
- Keeps context (other meals visible)
- Saves navigation overhead vs modal
- Smooth animations improve perceived performance

**Implementation Approach**:
```tsx
const [expandedId, setExpandedId] = useState<string | null>(null);

<div className={`meal-card ${expanded ? 'expanded' : ''}`}>
  <div className="meal-thumbnail" onClick={() => toggleExpand(meal.id)}>
    <img src={meal.photos[0].thumbnail} />
  </div>

  <div className={`meal-details ${expanded ? 'visible' : 'hidden'}`}>
    <PhotoCarousel photos={meal.photos} />
    <Macronutrients protein={meal.protein_grams} carbs={meal.carbs_grams} fats={meal.fats_grams} />
    <MealActions onEdit={handleEdit} onDelete={handleDelete} />
  </div>
</div>
```

**Alternatives Considered**:
- Modal/overlay: Rejected - requires dismissal, loses context
- Separate detail page: Rejected - extra navigation step
- Always expanded: Rejected - doesn't scale with many meals

**Best Practices**:
- Single expansion at a time (close others when opening new)
- Smooth CSS transitions (max-height animation)
- Preserve scroll position on expand/collapse
- Show loading state during expansion if data fetch needed
- Include edit/delete actions in expanded state

## 8. Meal Edit/Delete Functionality

### Decision: RESTful PATCH/DELETE with Optimistic Updates

**Rationale**:
- Standard REST verbs for clarity
- PATCH for partial updates (description, macros)
- Optimistic UI updates for responsiveness
- Revert on failure with error toast

**Implementation Approach**:
```python
# Backend
@router.patch("/api/v1/meals/{meal_id}")
async def update_meal(meal_id: UUID, updates: MealUpdate):
    # Validate user owns meal
    # Update allowed fields (description, protein, carbs, fats)
    # Recalculate total calories if macros changed
    # Update daily_summary stats
    # Return updated meal

@router.delete("/api/v1/meals/{meal_id}")
async def delete_meal(meal_id: UUID):
    # Validate user owns meal
    # Soft delete or hard delete (TBD)
    # Update daily_summary stats
    # Return success
```

**Alternatives Considered**:
- PUT for updates: Rejected - requires full object, inflexible
- Soft delete only: Deferred - decide based on data retention needs
- Separate endpoint for stats update: Rejected - should be atomic

**Best Practices**:
- Validate ownership before any operation
- Update daily_summary atomically with meal changes
- Use database transactions for consistency
- Return updated meal object for UI sync
- Implement undo functionality (optional enhancement)

## 9. One-Year Data Retention Implementation

### Decision: Date-Based Filtering + Optional Archival Job

**Rationale**:
- Simple filtering in queries: WHERE created_at >= NOW() - INTERVAL '1 year'
- Optional background job for actual deletion/archival
- Keeps database size manageable
- Complies with retention policy

**Implementation Approach**:
```python
# In meal query services
def get_user_meals(user_id: UUID, date: datetime = None):
    one_year_ago = datetime.now() - timedelta(days=365)
    query = (
        select(Meal)
        .where(Meal.user_id == user_id)
        .where(Meal.created_at >= one_year_ago)
    )
    if date:
        query = query.where(func.date(Meal.created_at) == date.date())
    return query

# Optional: Background job (monthly)
async def archive_old_meals():
    one_year_ago = datetime.now() - timedelta(days=365)
    # Move to archive table or delete
    # Also handle associated photos in Tigris
```

**Alternatives Considered**:
- Hard retention cutoff: Rejected - abrupt data loss, poor UX
- Infinite retention: Rejected - violates spec, storage costs
- Manual user control: Rejected - complexity, not required

**Best Practices**:
- Filter at query level for immediate effect
- Add index on created_at for performance
- Provide user export before archival (GDPR)
- Document retention policy in terms of service
- Test boundary conditions (exactly 365 days ago)

## Technology Stack Summary

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Backend Framework | FastAPI | Current | API endpoints, async processing |
| Bot Integration | python-telegram-bot | Current | Telegram webhook handling |
| AI Vision | OpenAI gpt-5-mini | Current | Multi-photo calorie estimation |
| Database | Supabase PostgreSQL | Current | Meal/photo storage, relationships |
| Object Storage | Tigris S3-compatible | Current | Photo file storage |
| Queue | Upstash Redis | Current | Background job queue |
| Frontend Framework | React 18 | Current | UI components |
| Build Tool | Vite | Current | Fast dev builds |
| Calendar | react-day-picker | ~9.x | Date selection |
| Carousel | swiper.js | ~11.x | Photo slideshow |
| Charts | Chart.js / Recharts | Current | Responsive graphs |
| Testing (BE) | pytest | Current | Backend tests |
| Testing (FE) | Jest, Playwright | Current | Frontend/E2E tests |

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Media group timing issues | Medium | Implement 200ms wait window with timeout |
| AI cost increase (multi-photo) | Low | Monitor usage, optimize prompts |
| Database query performance | Low | Proper indexing on meal_id, created_at |
| Mobile carousel performance | Medium | Lazy load images, optimize sizes |
| Data migration complexity | Low | Backward compatible schema additions |

## Next Steps (Phase 1)

1. Design detailed data model with all fields and relationships
2. Create OpenAPI contracts for new/updated endpoints
3. Write contract tests for API changes
4. Generate integration test scenarios from user stories
5. Create quickstart.md with validation steps
6. Update agent context file with new components

---

*All decisions align with existing tech stack and constitutional principles. No new external dependencies required beyond optional react-day-picker and swiper.js for UI components.*
