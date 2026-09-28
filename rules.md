# D Web Studio — Outreach Automation

# Implementation Phases

## 1. Purpose

This document defines the implementation phases for the **D Web Studio Local Outreach Automation Dashboard**.

The system will be built incrementally so that each phase produces a usable and testable result.

The core objective is:

> Import leads → store them safely → process them automatically → send Email/WhatsApp → record results → resume safely → show everything in a local dashboard.

The system should prioritize **reliability and duplicate protection** over unnecessary features.

---

# 2. Phase Overview

```text
PHASE 0
Project Setup
    ↓
PHASE 1
Lead Import & Database
    ↓
PHASE 2
Dashboard UI
    ↓
PHASE 3
Email Integration
    ↓
PHASE 4
WhatsApp Integration
    ↓
PHASE 5
Automation Engine
    ↓
PHASE 6
AI Intelligence Layer
    ↓
PHASE 7
Memory & Resume System
    ↓
PHASE 8
Testing & Safety
    ↓
PHASE 9
Production-Ready Local Release
```

Each phase depends on the previous phases unless explicitly stated otherwise.

---

# 3. Phase 0 — Project Setup

## Goal

Create the base application structure and development environment.

## Tasks

* Create project repository.
* Create application directories.
* Configure Python environment.
* Create `.env`.
* Create `.gitignore`.
* Add dependency management.
* Create configuration system.
* Create logging system.
* Create basic application entry point.
* Create README.
* Establish local `data/` directory.
* Establish `credentials/` directory.

## Initial Structure

```text
d-web-studio-outreach/
├── app/
├── data/
├── credentials/
├── tests/
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## Completion Criteria

* Application starts locally.
* Configuration loads successfully.
* Logging works.
* Secrets are excluded from Git.
* Directory structure is ready for subsequent phases.

---

# 4. Phase 1 — Lead Import & Database

## Goal

Create a reliable local lead-management foundation.

The database becomes the runtime source of truth.

Excel remains the primary input/output format.

## Tasks

### Excel Import

Read:

```text
Name
Email
Phone
Priority
Gender
Age
City/State
Education/Degree
Source
```

The importer must correctly handle the existing Excel structure where the first row may itself be a lead.

### Normalization

Normalize:

* Names.
* Email addresses.
* Phone numbers.
* Priority values.
* Empty fields.
* Whitespace.
* Duplicate records.

### Database

Create SQLite database:

```text
data/outreach.db
```

Core tables:

```text
leads
outreach
runs
events
templates
```

## Lead Identity

Use the following identity hierarchy:

```text
1. Internal lead ID
2. Email
3. Normalized phone
4. Name + contact information
```

Never create duplicate leads simply because formatting differs.

## Completion Criteria

* Excel imports successfully.
* Leads appear in SQLite.
* Priority filtering works.
* Duplicate leads are detected.
* Missing email/phone values are handled.
* Database survives application restart.

---

# 5. Phase 2 — Dashboard UI

## Goal

Build the local control center.

The dashboard should remain intentionally simple.

## Main UI

```text
┌─────────────────────────────────────────────┐
│ D WEB STUDIO                    ● READY      │
├─────────────────────────────────────────────┤
│                                             │
│ Total       Completed       Pending Failed  │
│  70            12              58      0    │
│                                             │
│          [ START AUTOMATION ]               │
│                                             │
│ CURRENT ACTIVITY                            │
│ Rohit Kumar                                 │
│ Sending Email…                              │
│ ████████████░░░░░░░░  12 / 70              │
│                                             │
│ ACTIVITY                                    │
│ ✓ Prachi Lilhare — Email sent              │
│ ✓ Prachi Lilhare — WhatsApp sent           │
│ → Rohit Kumar — Sending email…             │
│ ○ Next lead — Pending                       │
│                                             │
└─────────────────────────────────────────────┘
```

## Dashboard Requirements

Display:

* System status.
* Total leads.
* Completed.
* Pending.
* Failed.
* Current lead.
* Current action.
* Current channel.
* Progress.
* Activity log.
* Start button.
* Completion state.

## States

```text
READY
RUNNING
PAUSED
COMPLETE
ERROR
```

## Completion Criteria

* Dashboard loads locally.
* Lead counts are accurate.
* Start button changes state.
* Current activity updates.
* Progress updates.
* Activity log receives events.
* Dashboard survives refresh/restart.

---

# 6. Phase 3 — Email Integration

## Goal

Connect the system to Gmail through the official Gmail API.

## Authentication

Use Google OAuth.

Required files:

```text
credentials/
└── gmail/
    └── credentials.json
```

Runtime token:

```text
token.json
```

`credentials.json` and `token.json` must never be committed to Git.

## Email Flow

```text
Lead
 ↓
Check Email Status
 ↓
Validate Email
 ↓
Build Message
 ↓
Gmail API
 ↓
Receive Result
 ↓
Save Message ID
 ↓
Update Status
```

## Email States

```text
PENDING
SENT
FAILED
NOT_AVAILABLE
```

## Duplicate Protection

Before every send:

```text
IF Email Status == SENT
    SKIP
ELSE
    SEND
```

Never send the same campaign email twice because the application restarted.

## Error Handling

Examples:

```text
Invalid address
Authentication failure
API timeout
Rate limit
Network error
Unknown delivery state
```

Each failure must be logged without stopping the entire automation run.

## Completion Criteria

* OAuth works.
* Test email can be sent.
* Email status is recorded.
* Gmail message ID is stored.
* Duplicate sends are prevented.
* Errors are logged.
* Application can resume after interruption.

---

# 7. Phase 4 — WhatsApp Integration

## Goal

Connect the dashboard to the user's configured WhatsApp Business/API provider.

## Important Rule

The system must not assume that a phone number is WhatsApp-enabled.

The provider/API must determine availability whenever possible.

## WhatsApp States

```text
PENDING
SENT
FAILED
NOT_AVAILABLE
UNKNOWN
```

## Flow

```text
Lead
 ↓
Normalize Phone
 ↓
Check Provider Availability
 ↓
Build Message
 ↓
WhatsApp API
 ↓
Receive Result
 ↓
Save Provider Message ID
 ↓
Update Status
```

## Missing Phone

If:

```text
Phone == EMPTY
```

then:

```text
WhatsApp Status = NOT_AVAILABLE
```

## Unknown Availability

If the provider cannot reliably confirm availability:

```text
WhatsApp Status = UNKNOWN
```

Do not automatically treat `UNKNOWN` as available.

## Completion Criteria

* Provider credentials load securely.
* Test message works.
* API result is recorded.
* Provider message ID is stored.
* Missing numbers are handled.
* Unknown availability is represented correctly.
* Duplicate sending is prevented.

---

# 8. Phase 5 — Automation Engine

## Goal

Connect the entire system into one reliable processing loop.

## Main Flow

```text
START
  ↓
Load Configuration
  ↓
Load Database
  ↓
Load Eligible Leads
  ↓
Check Existing Status
  ↓
Process Lead
  ↓
Generate Message
  ↓
Send Email
  ↓
Save Result
  ↓
Send WhatsApp
  ↓
Save Result
  ↓
Update Lead
  ↓
Update Dashboard
  ↓
Next Lead
  ↓
ALL DONE
```

## Processing Rules

For each lead:

```text
1. Check whether lead is eligible.
2. Check existing outreach state.
3. Skip already completed channels.
4. Generate appropriate message.
5. Validate message.
6. Send through configured channel.
7. Save result immediately.
8. Update dashboard.
9. Continue.
```

## Partial Completion

Example:

```text
Email = SENT
WhatsApp = PENDING
```

On restart:

```text
Skip Email
Process WhatsApp
```

Never restart the complete lead unnecessarily.

## Failure Isolation

If one lead fails:

```text
Lead A → FAILED
Lead B → continue
Lead C → continue
```

A single failure must not terminate the entire campaign.

## Completion Criteria

* Multiple leads process sequentially.
* State updates after every action.
* Duplicate protection works.
* Failed leads do not stop the run.
* Dashboard reflects real-time progress.
* Run can resume.

---

# 9. Phase 6 — AI Intelligence Layer

## Goal

Add AI-assisted decision-making without allowing AI to bypass system safety or state controls.

The automation engine remains in control.

## AI Loop

```text
OBSERVE
   ↓
UNDERSTAND
   ↓
DECIDE
   ↓
GENERATE
   ↓
EXECUTE
   ↓
OBSERVE RESULT
   ↓
EVALUATE
   ↓
IMPROVE
   ↓
NEXT LEAD
```

## AI Responsibilities

AI may:

* Understand lead information.
* Classify lead type.
* Determine personalization level.
* Generate outreach copy.
* Recommend channels.
* Check message quality.
* Classify replies.
* Improve templates using aggregate results.

## AI Must Not

AI must not:

* Change credentials.
* Bypass duplicate protection.
* Delete lead history.
* Ignore opt-outs.
* Send outside the automation workflow.
* Invent business information.
* Override system state.
* Decide that an unavailable channel is available.

## Verification Levels

Every external fact should be treated as:

```text
VERIFIED
UNVERIFIED
UNKNOWN
```

Only verified information should be used as factual personalization.

## Lead Types

```text
BUSINESS_OWNER
PROFESSIONAL
FREELANCER
JOB_SEEKER
STUDENT
UNKNOWN
```

## Completion Criteria

* AI receives structured lead context.
* AI output follows a defined schema.
* Hallucinated personalization is prevented.
* System validates AI recommendations.
* AI failure falls back safely.
* Sending still works without AI.

---

# 10. Phase 7 — Memory & Resume System

## Goal

Make the system persistent and interruption-safe.

## Memory Includes

```text
Lead information
Outreach history
Message IDs
Delivery states
AI decisions
Errors
Replies
Opt-outs
Follow-ups
Campaign configuration
Template versions
Run state
```

## Run State

Example:

```text
Run ID: 2026-09-28-001
Status: RUNNING
Current Lead: 37
Total Leads: 70
```

If the application closes:

```text
Application restarted
        ↓
Load previous run
        ↓
Check database
        ↓
Find unfinished actions
        ↓
Resume safely
```

## Uncertain Delivery

If an API timeout occurs after a request may have been accepted:

```text
Do not blindly retry.
```

Instead:

```text
UNKNOWN
 ↓
Reconcile provider state
 ↓
Determine final result
```

This prevents accidental duplicate messages.

## Opt-Out Memory

If a lead explicitly opts out:

```text
OPT_OUT = TRUE
```

Future automated outreach must be skipped unless the user explicitly changes the campaign policy.

## Completion Criteria

* Restart preserves state.
* Previous runs remain available.
* Partial actions resume correctly.
* Duplicate protection survives restart.
* Opt-outs persist.
* Uncertain API states are handled safely.

---

# 11. Phase 8 — Testing & Safety

## Goal

Test the system before allowing full automation.

Testing should happen progressively rather than waiting until the end.

## Test Categories

### Lead Tests

* Valid lead.
* Missing email.
* Missing phone.
* Duplicate lead.
* Invalid email.
* Invalid phone.
* Priority/non-priority filtering.

### Email Tests

* Successful send.
* Invalid email.
* OAuth failure.
* Network failure.
* Timeout.
* Duplicate protection.
* Resume after partial completion.

### WhatsApp Tests

* Valid number.
* Missing number.
* Provider unavailable.
* Number unavailable.
* API failure.
* Timeout.
* Duplicate protection.

### Automation Tests

```text
0 leads
1 lead
5 leads
Multiple failures
Interrupted run
Restarted run
Partial completion
Complete campaign
```

## Safety Tests

Verify:

```text
No duplicate sends
No secret exposure
No credential logging
No fabricated personalization
No sending to opted-out leads
No processing of ineligible leads
```

## Dry Run

Before live automation:

```text
DRY_RUN = true
```

The system should:

* Load leads.
* Generate messages.
* Show intended actions.
* Record simulated results.
* NOT send real messages.

Only after dry-run validation should live sending be enabled.

## Completion Criteria

All critical tests pass.

---

# 12. Phase 9 — Production-Ready Local Release

## Goal

Turn the tested application into the daily-use version.

## Release Requirements

### Configuration

```text
.env
credentials/
data/
```

must be configured correctly.

### Security

* Secrets outside source code.
* `.gitignore` configured.
* Credentials never appear in logs.
* API keys never appear in dashboard.
* OAuth tokens stored locally and securely.

### Reliability

* SQLite database working.
* Excel import/export working.
* Resume working.
* Duplicate protection working.
* Error handling working.
* Logging working.

### UI

Dashboard must clearly show:

```text
READY
RUNNING
COMPLETE
ERROR
```

and:

```text
Total
Completed
Pending
Failed
Current Lead
Current Action
Progress
Activity
```

## Final Completion State

```text
┌─────────────────────────────────────────────┐
│ D WEB STUDIO                    ✓ ALL DONE   │
│                                             │
│ Total Leads       70                        │
│ Completed         70                        │
│ Pending            0                        │
│ Failed             0                        │
│                                             │
│ Campaign processing complete.               │
└─────────────────────────────────────────────┘
```

---

# 13. Development Order

Implementation should follow this order:

```text
1. Project Setup
       ↓
2. SQLite + Lead Import
       ↓
3. Dashboard
       ↓
4. Gmail Integration
       ↓
5. WhatsApp Integration
       ↓
6. Automation Engine
       ↓
7. Memory/Resume
       ↓
8. AI Layer
       ↓
9. Testing
       ↓
10. Live Automation
```

Do not build the AI layer first.

The underlying deterministic system must work before AI is allowed to make recommendations.

---

# 14. MVP Definition

The minimum viable system is:

```text
✓ Import Excel
✓ Store leads in SQLite
✓ Filter Priority leads
✓ Dashboard
✓ Start button
✓ Gmail API
✓ WhatsApp API
✓ Email status
✓ WhatsApp status
✓ Duplicate protection
✓ Resume after restart
✓ Activity log
✓ Progress tracking
✓ Error handling
✓ Local-only dashboard
```

AI personalization can initially be disabled and added afterward.

---

# 15. V1 Definition

V1 adds:

```text
✓ AI lead classification
✓ AI message personalization
✓ Verified-information handling
✓ Reply classification
✓ Template versions
✓ Follow-up support
✓ Campaign memory
✓ Learning signals
✓ Better error recovery
```

---

# 16. Future Features

These are intentionally outside the initial scope:

```text
- Public SaaS dashboard
- Multi-user accounts
- Billing
- Complex CRM
- Advanced analytics
- Large-scale campaign management
- Cloud lead database
- Team permissions
- Complex reporting
```

These should not delay the local automation system.

---

# 17. Phase Dependencies

```text
Project Setup
     │
     ▼
Lead Database
     │
     ├──────────────► Dashboard
     │
     ▼
Email Integration
     │
     ▼
WhatsApp Integration
     │
     ▼
Automation Engine
     │
     ├──────────────► Memory
     │
     ▼
AI Layer
     │
     ▼
Testing
     │
     ▼
Live System
```

---

# 18. Definition of Done

The project is considered operational when all of the following are true:

```text
[✓] Excel leads can be imported
[✓] Leads are stored locally
[✓] Priority filtering works
[✓] Dashboard displays accurate state
[✓] Gmail OAuth works
[✓] Email can be sent
[✓] WhatsApp API works
[✓] WhatsApp availability is handled correctly
[✓] Every send produces a recorded state
[✓] Duplicate sends are prevented
[✓] Interrupted runs can resume
[✓] Failed leads do not stop the campaign
[✓] Activity logs are persisted
[✓] Credentials are protected
[✓] AI cannot bypass system controls
[✓] Dry-run mode works
[✓] Full test campaign succeeds
[✓] Live automation can be started safely
```

---

# 19. Core Development Principle

The system should be developed in this order:

```text
RELIABILITY
    ↓
STATE MANAGEMENT
    ↓
INTEGRATIONS
    ↓
AUTOMATION
    ↓
AI INTELLIGENCE
    ↓
OPTIMIZATION
```

The AI is not the foundation.

The foundation is a deterministic system that knows:

```text
WHO
    ↓
WHAT
    ↓
WHEN
    ↓
WHICH CHANNEL
    ↓
WHAT HAPPENED
    ↓
WHAT TO DO NEXT
```

The final architecture should therefore follow:

```text
AI THINKS
    ↓
SYSTEM VALIDATES
    ↓
AUTOMATION EXECUTES
    ↓
SYSTEM RECORDS
    ↓
MEMORY PERSISTS
    ↓
AI LEARNS
    ↓
NEXT LEAD
```

This loop should remain the central operating principle of the entire D Web Studio outreach system.
