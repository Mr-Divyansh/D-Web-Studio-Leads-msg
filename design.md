# D Web Studio — Local Outreach Automation

## Design System & UI Specification

---

## 1. Design Direction

The application should be:

* Simple
* Minimal
* Professional
* Fast to understand
* Local-first
* Operational rather than CRM-like

The dashboard exists only to control and monitor the outreach automation.

The user should be able to open the dashboard and immediately understand:

1. Whether automation is running.
2. Which lead is currently being processed.
3. What action is currently happening.
4. How many leads are completed.
5. How many leads are pending.
6. Whether any actions failed.
7. When everything is finished.

Do not add unnecessary CRM features, analytics, charts, pipelines, or complicated navigation.

---

# 2. Visual Style

### Overall Style

Use a clean modern SaaS/desktop-tool aesthetic.

Characteristics:

* White/light background
* Dark readable text
* Blue primary action
* Subtle borders
* Small rounded corners
* Minimal shadows
* Clear status indicators
* Compact spacing
* No visual clutter

The product should feel like a professional developer tool rather than a marketing website.

---

# 3. Color Palette

## Primary

```text
Primary:        #2563EB
Primary Hover:  #1D4ED8
```

Use for:

* Start button
* Active controls
* Progress bar
* Selected states
* Links
* Active indicators

## Background

```text
Background: #F8FAFC
Surface:    #FFFFFF
```

Use `#F8FAFC` for the application background and `#FFFFFF` for cards/panels.

## Borders

```text
Border: #E2E8F0
```

Use for:

* Cards
* Separators
* Tables
* Input borders

## Text

```text
Text Primary:   #0F172A
Text Secondary: #64748B
```

## Status Colors

```text
Success: #16A34A
Warning: #D97706
Error:   #DC2626
Neutral: #94A3B8
```

### Status Usage

| Status        | Color   |
| ------------- | ------- |
| Pending       | Neutral |
| Processing    | Primary |
| Sent          | Success |
| Completed     | Success |
| Failed        | Error   |
| Not Available | Neutral |
| Unknown       | Warning |
| Skipped       | Neutral |

Do not use color as the only status indicator. Always combine color with text or an icon.

---

# 4. Typography

## Primary Font

Use:

```text
Inter
```

Fallback:

```text
system-ui, -apple-system, Segoe UI, sans-serif
```

## Typography Scale

| Element         |    Size |  Weight |
| --------------- | ------: | ------: |
| Page Title      | 22–26px |     700 |
| Section Heading | 15–18px |     600 |
| Metric Number   | 22–28px |     700 |
| Body            |    14px |     400 |
| Small Text      |    12px | 400–500 |
| Button          | 13–14px |     600 |
| Status Badge    | 12–13px |     600 |

Keep typography compact and readable.

---

# 5. Spacing

Use an 8px spacing system.

```text
4px   — micro spacing
8px   — small spacing
12px  — compact spacing
16px  — standard spacing
24px  — section spacing
32px  — major spacing
```

Recommended:

```text
Card gap:        16px
Section gap:     24px
Page padding:    24px
Compact padding: 16px
```

---

# 6. Border Radius

```text
Cards:      10px
Buttons:     8px
Inputs:      8px
Badges:     999px
Progress:   999px
```

Avoid excessive rounded/pill-shaped UI except for status badges.

---

# 7. Shadows

The application should use very subtle shadows.

Preferred:

```text
0 1px 3px rgba(15, 23, 42, 0.06)
```

Avoid large, dramatic shadows.

The interface should primarily use borders and spacing to create hierarchy.

---

# 8. Dashboard Layout

The main dashboard has four sections:

```text
Header
   ↓
Summary Cards
   ↓
Automation / Current Activity
   ↓
Activity Log
```

No sidebar is required for the MVP.

No complicated navigation is required.

---

# 9. Header

The header contains:

### Left

```text
D WEB STUDIO
Local Outreach
```

### Right

System status:

```text
● READY
```

Possible states:

```text
● READY
● RUNNING
● ERROR
✓ COMPLETE
```

The status indicator should use both icon and text.

---

# 10. Summary Cards

Show four cards:

```text
Total Leads
Completed
Pending
Failed
```

Example:

```text
┌──────────────┐
│ Total Leads  │
│      70      │
└──────────────┘

┌──────────────┐
│ Completed    │
│      12      │
└──────────────┘

┌──────────────┐
│ Pending      │
│      58      │
└──────────────┘

┌──────────────┐
│ Failed       │
│       0      │
└──────────────┘
```

Desktop:

```text
4 cards in one row
```

Smaller window:

```text
2 × 2
```

Very narrow window:

```text
1 × 4
```

---

# 11. Start Automation Button

The Start button is the most important action in the interface.

Default:

```text
[ START AUTOMATION ]
```

Style:

```text
Background: #2563EB
Text:       #FFFFFF
Height:     40–44px
Radius:      8px
Weight:      600
```

When running:

```text
[ RUNNING... ]
```

The button must be disabled while the automation is already running.

This prevents accidental duplicate runs.

---

# 12. Current Activity

Show the currently processed lead.

Example:

```text
CURRENT ACTIVITY

Rohit Kumar

Sending Email...

Email
```

Then:

```text
████████████░░░░░░░░

12 / 70
```

The current activity section should always remain visible while automation is running.

---

# 13. Progress Bar

Height:

```text
6–8px
```

Track:

```text
#E2E8F0
```

Progress:

```text
#2563EB
```

Rounded ends.

Example:

```text
████████████░░░░░░░░

12 / 70
```

The progress bar represents **leads processed**, not individual API calls.

---

# 14. Activity Log

The activity log shows what the automation is doing.

Example:

```text
ACTIVITY

✓ Prachi Lilhare — Email sent
✓ Prachi Lilhare — WhatsApp sent
✓ Pintu — Email sent
• Pintu — WhatsApp unavailable
→ Rohit Kumar — Sending email...
○ Next lead — Pending
```

Icons:

```text
✓ Success
→ Processing
○ Pending
! Failed
— Not Available
? Unknown
× Skipped
```

The activity log should be scrollable if it becomes long.

Do not display raw API responses.

---

# 15. Lead Status

Every lead can have:

```text
PENDING
PROCESSING
COMPLETED
FAILED
SKIPPED
NOT_MATCH
```

Example:

```text
Rohit Kumar

Email:     SENT
WhatsApp:  NOT AVAILABLE
Lead:      COMPLETED
```

---

# 16. Email Status

Email status values:

```text
PENDING
SENT
FAILED
NOT_AVAILABLE
```

Example:

```text
Email: ✓ SENT
```

or:

```text
Email: ! FAILED
```

or:

```text
Email: — NOT AVAILABLE
```

---

# 17. WhatsApp Status

WhatsApp status values:

```text
PENDING
SENT
FAILED
NOT_AVAILABLE
UNKNOWN
```

Example:

```text
WhatsApp: ✓ SENT
```

or:

```text
WhatsApp: — NOT AVAILABLE
```

or:

```text
WhatsApp: ? UNKNOWN
```

Do not claim that a phone number has WhatsApp unless the configured provider/API confirms it.

---

# 18. Lead Row

The MVP does not require a large CRM table.

If leads are displayed, use compact rows.

Example:

```text
Rohit Kumar
Email ✓
WhatsApp —
Completed
```

Alternative single-line format:

```text
Rohit Kumar | Email ✓ | WhatsApp — | Completed
```

Optional information:

```text
City
Last Contacted
```

Do not overload the interface with every Excel column.

---

# 19. Completion State

When all eligible leads have been processed, show:

```text
┌───────────────────────────────────┐
│                                   │
│            ALL DONE ✓             │
│                                   │
│        70 / 70 processed          │
│                                   │
│   Email sent:       65            │
│   WhatsApp sent:    51            │
│   Not available:    19            │
│   Failed:            2            │
│                                   │
└───────────────────────────────────┘
```

The completion screen should be calm and professional.

Do not use excessive animations or celebration effects.

---

# 20. Error State

Errors should never crash the entire dashboard.

Example:

```text
! Rohit Kumar — Email failed

Reason:
Temporary API error
```

The automation should continue with other eligible leads whenever safe.

Do not show:

* API secrets
* OAuth tokens
* Passwords
* Raw stack traces

to the normal user interface.

---

# 21. Responsive Behavior

### Large

```text
≥ 900px
```

Use:

```text
4 summary cards in one row
```

### Medium

```text
760–899px
```

Use:

```text
2 summary cards per row
```

### Small

```text
< 760px
```

Use:

```text
1 column
```

The Start button and current automation status must remain easy to access.

---

# 22. Accessibility

The dashboard must:

* Use readable text sizes.
* Have visible keyboard focus.
* Have accessible button labels.
* Maintain sufficient contrast.
* Never rely on color alone.
* Avoid information that depends on animation.
* Keep important status text readable.

---

# 23. Motion

Use minimal motion.

Allowed:

```text
100–150ms hover transition
```

Optional:

```text
Short activity-item appearance animation
```

Progress updates may animate smoothly.

Avoid:

* Large animations
* Continuous decorative motion
* Auto-playing effects
* Distracting transitions

---

# 24. Do / Don't

| DO                            | DON'T                                 |
| ----------------------------- | ------------------------------------- |
| Keep one obvious Start button | Add multiple competing buttons        |
| Show live progress            | Add complicated analytics             |
| Use text + icons for statuses | Use color alone                       |
| Keep lead data local          | Build an unnecessary public CRM       |
| Use restrained branding       | Make it look like a marketing website |
| Show useful errors            | Show raw technical errors             |
| Keep the dashboard compact    | Add unnecessary pages                 |
| Make automation state obvious | Hide processing information           |

---

# 25. Wireframe

```text
┌──────────────────────────────────────────────────────┐
│ D WEB STUDIO                           ● READY        │
├──────────────────────────────────────────────────────┤
│                                                      │
│  TOTAL       COMPLETED       PENDING       FAILED    │
│   70             12             58            0       │
│                                                      │
│              [ START AUTOMATION ]                    │
│                                                      │
│  CURRENT ACTIVITY                                    │
│                                                      │
│  Rohit Kumar                                         │
│  Sending Email...                                    │
│                                                      │
│  ████████████░░░░░░░░  12 / 70                      │
│                                                      │
│  ACTIVITY                                            │
│                                                      │
│  ✓ Prachi Lilhare — Email sent                     │
│  ✓ Prachi Lilhare — WhatsApp sent                  │
│  ✓ Pintu — Email sent                               │
│  — Pintu — WhatsApp unavailable                     │
│  → Rohit Kumar — Sending email...                   │
│  ○ Next lead — Pending                               │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

# 26. Design Tokens

The implementation should define reusable tokens rather than hard-coding values throughout the application.

```text
--color-primary: #2563EB
--color-primary-hover: #1D4ED8

--color-background: #F8FAFC
--color-surface: #FFFFFF
--color-border: #E2E8F0

--color-text-primary: #0F172A
--color-text-secondary: #64748B

--color-success: #16A34A
--color-warning: #D97706
--color-error: #DC2626
--color-neutral: #94A3B8

--radius-card: 10px
--radius-button: 8px
--radius-badge: 999px

--space-1: 4px
--space-2: 8px
--space-3: 12px
--space-4: 16px
--space-6: 24px
--space-8: 32px
```

---

# 27. Product Feel

The final product should feel like:

> **A small professional local automation control center.**

It should NOT feel like:

* A CRM
* A social media dashboard
* A marketing website
* An analytics platform
* A complicated enterprise application

The user should be able to open it, press **START AUTOMATION**, watch the progress, and see **ALL DONE** when the queue finishes.

---

# 28. Relationship With PRD

`prd.md` defines:

> **What the product does.**

`design.md` defines:

> **How the product looks and behaves visually.**

The implementation must follow both documents.

When PRD and design conflict, the behavior defined in `prd.md` takes priority, while the visual presentation should follow this document wherever possible.
