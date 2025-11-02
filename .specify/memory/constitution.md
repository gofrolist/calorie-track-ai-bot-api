<!--
SYNC IMPACT REPORT
==================
Version Change: 1.0.0 → 2.0.0 (MAJOR)
Date: 2025-11-01
Rationale: Complete philosophical rewrite from technical implementation principles to
           user-experience focused governance. This is a backward-incompatible change
           in how the project defines success and makes decisions.

Modified Principles:
- AI-First Nutrition Analysis → Removed (technical detail)
- Telegram Bot Excellence → Removed (technical detail)
- API-First Architecture → Removed (technical detail)
- Test-Driven Development → Removed (now implementation detail, not constitutional)
- Observability & Monitoring → Removed (technical detail)
- Internationalization & Accessibility → Transformed into "Multilingual and Inclusive" principle
- Modern UI/UX Excellence → Transformed into "Mobile-First, Modern Design" principle
- Feature Flag Management → Removed (technical detail)
- Data Protection & Privacy → Transformed into "Respect for Privacy" principle

Added Sections:
- "What We Are Building" - Project vision and purpose
- "Who This Is For" - Target user definition
- "The Core Experience" - User journey descriptions
- "How People Use It" - User persona patterns
- "What Success Looks Like" - User-centric success metrics
- "What We Deliberately Avoid" - Scope boundaries and anti-patterns
- "The Long-Term Vision" - Strategic direction
- "Measuring Our Success" - Observable outcomes

Removed Sections:
- "Technical Standards" - moved to implementation documentation
- "CI/CD & DevOps Excellence" - moved to implementation documentation
- "Data Protection & Disaster Recovery" - moved to implementation documentation
- "Governance" - simplified and integrated into core principles

Templates Requiring Updates:
- ✅ plan-template.md - Constitution Check section needs update to reference user-centric principles
- ✅ spec-template.md - No changes needed (already user-story focused)
- ✅ tasks-template.md - No changes needed (implementation agnostic)
- ✅ agent-file-template.md - No changes needed (auto-generated from plans)
- ✅ checklist-template.md - No changes needed (context-specific)

Follow-up Actions:
- Update existing feature specifications to reference new constitution principles
- Review plan.md files to ensure Constitution Check aligns with new principles
- Communicate constitution change to all stakeholders
- Archive old technical principles as implementation guidelines (separate document)
-->

# Calorie Track AI Bot - Project Constitution

## What We Are Building

A simple, intelligent companion for anyone who wants to understand their nutrition without the hassle of manual tracking. We're creating a Telegram-based calorie tracking experience that transforms food photos into nutritional insights instantly.

## Who This Is For

This is for people who:
- Want to track their calories and nutrition without complex apps or manual data entry
- Prefer quick, frictionless interactions over detailed form filling
- Need flexibility to track both privately and in social contexts with friends or fitness groups
- Value simplicity and speed in their daily routines
- Want to understand what they eat, set goals, and see their progress over time

## The Core Experience

### The Simplest Entry Point
Send a photo of your meal to a Telegram bot. That's it. Within seconds, you receive an estimate of calories, proteins, fats, and carbohydrates. No accounts to create, no complex interfaces—just a photo and instant feedback.

### Works Where You Already Are
Whether you're chatting privately or sharing meals with friends in a group chat, the bot meets you where you are. Forward a photo inline, get your analysis right there in the conversation, without switching apps or breaking your flow.

### Details When You Need Them
For those who want more, a modern Telegram Mini App provides:
- A beautiful daily view of all your logged meals
- Calendar navigation to review past days, weeks, or months
- The ability to correct AI estimates when you know better
- Goal setting and progress tracking
- Visual summaries and trends over time
- Instagram-style photo carousels for multi-photo meals

## Core Principles

### 1. Simplicity First
The default experience should be trivial: photo in, information out. Everything else is optional depth for those who seek it.

**Rationale**: Complexity is the enemy of adoption. Users should never feel overwhelmed or confused about the core interaction. Every feature must justify its existence by solving a real user problem, not by being "nice to have."

### 2. Respect for Privacy
Your food photos and personal data are yours. The system processes what it needs and keeps only what helps you track your progress. Group interactions don't create permanent records without your consent.

**Rationale**: Trust is foundational. Users must feel safe sharing their meals and dietary information. Transparency about data handling builds confidence and long-term engagement.

### 3. Honest About Limitations
AI estimates are helpful approximations, not medical-grade measurements. The system clearly communicates confidence levels and encourages manual corrections when accuracy matters.

**Rationale**: Overpromising accuracy creates disappointment and mistrust. Being honest about limitations while providing correction mechanisms gives users control and builds realistic expectations.

### 4. Mobile-First, Modern Design
Built for phones, optimized for quick interactions, beautiful to use. The interface adapts to your device, respects screen boundaries, and follows modern design principles.

**Rationale**: Mobile devices are where users live. A design that feels native to mobile, respects device conventions, and looks modern increases engagement and satisfaction.

### 5. Multilingual and Inclusive
Speaks your language—starting with English and Russian, with room to grow. Automatically adapts to your Telegram settings.

**Rationale**: Nutrition tracking should be accessible regardless of language. Automatic language detection removes barriers and makes the tool welcoming to diverse users.

### 6. Fast and Reliable
Quick acknowledgments, clear status updates, and graceful handling when things go wrong. You should never wonder if your request was received or lost.

**Rationale**: Speed and reliability build trust. Every second of delay creates doubt. Clear communication about system status prevents user frustration.

## How People Use It

### The Quick Tracker
Takes a photo at every meal, glances at the estimate, moves on with their day. Checks weekly totals in the Mini App to stay generally aware of their intake.

### The Goal-Oriented Dieter
Sets daily calorie targets, reviews each estimate carefully, makes corrections when needed, and watches daily progress bars. Uses historical trends to adjust their approach.

### The Social Sharer
Analyzes meals in group chats with friends or accountability partners. Uses inline mode to get instant feedback while discussing meal choices with others.

### The Data Enthusiast
Reviews detailed macronutrient breakdowns, tracks trends over weeks and months, exports or shares progress, and fine-tunes estimates based on personal knowledge.

## What Success Looks Like

### For Individual Users
- You can track a meal in under 10 seconds
- You understand your daily nutrition at a glance
- You feel empowered, not overwhelmed, by your food choices
- The tool fades into the background, supporting without nagging

### For Groups
- Meal discussions include nutritional context naturally
- The bot adds value without dominating conversations

### For Long-Term Use
- You develop better intuition about portion sizes and nutrition
- Historical data reveals patterns you can act on
- The system adapts to your habits and preferences
- You maintain your dietary goals with less effort over time

## What We Deliberately Avoid

### Complexity Creep
No recipe databases, no meal planning, no complex macros calculators. These features exist elsewhere. We focus on the core loop: see food, know nutrition, track progress.

**Rationale**: Feature bloat dilutes the core value proposition. Every "nice to have" feature adds complexity that makes the essential features harder to find and use.

### Judgment and Pressure
No guilt-inducing notifications. Just information and optional goals.

**Rationale**: Negative reinforcement creates anxiety and abandonment. Users should feel supported, not judged. The tool observes and informs without moralizing.

### Privacy Invasion
No selling data, no targeted advertising, no sharing information with third parties. Your nutrition journey is yours alone.

**Rationale**: Monetizing user data destroys trust and violates the core principle of privacy respect. The product's value should come from the service it provides, not from exploiting user information.

### False Precision
We don't pretend AI estimates are perfect. We show confidence ranges and make correction easy because accuracy through collaboration beats false precision.

**Rationale**: Claiming perfect accuracy when it doesn't exist damages credibility. Acknowledging limitations and empowering users to improve estimates creates a partnership model that's more honest and effective.

## The Long-Term Vision

A tool so simple and fast that checking your nutrition becomes as natural as checking the time. A companion that helps you understand your eating patterns without judgment, complexity, or friction. An experience that proves health tracking can be both powerful and effortless when designed with restraint and focus.

## Measuring Our Success

We know we're succeeding when:
- Users track meals consistently without feeling burdened
- People describe the experience as "fast," "easy," and "just works"
- Accuracy meets real-world needs (not perfection, but reliability)
- Feature requests focus on refinement, not expansion
- Long-term retention grows because the tool remains useful without becoming demanding

## Governance

### Amendment Process
This constitution can be amended when:
1. User feedback reveals a fundamental misalignment between principles and experience
2. New usage patterns emerge that require principle clarification or expansion
3. Strategic direction changes require documenting new boundaries

Amendments require:
- Clear articulation of what's changing and why
- Assessment of impact on existing features and roadmap
- Version increment following semantic versioning (MAJOR for principle changes, MINOR for additions, PATCH for clarifications)

### Compliance Review
All feature specifications must reference which principles they serve. Features that don't align with constitutional principles should be rejected unless the constitution is amended first.

### Versioning Policy
- **MAJOR** (X.0.0): Backward-incompatible principle removals or redefinitions that change project philosophy
- **MINOR** (x.Y.0): New principles added or existing principles materially expanded
- **PATCH** (x.y.Z): Clarifications, wording improvements, or non-semantic refinements

---

**Version**: 2.0.0 | **Ratified**: 2025-09-25 | **Last Amended**: 2025-11-01

---

*This constitution guides all decisions about features, design, and user experience. When in doubt, choose simplicity. When users need more, offer depth without complexity. Always respect their time, privacy, and autonomy.*
