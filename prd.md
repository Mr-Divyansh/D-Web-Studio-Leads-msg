# Product Requirements Document (PRD)

## D Web Studio — Local Outreach Automation Dashboard

### 1. Product Goal

Build a small, simple **local outreach automation dashboard** for D Web Studio.

The system will process leads from a local Excel file and independently handle:

1. Email outreach through the configured Gmail API.
2. WhatsApp outreach through the configured WhatsApp API.
3. Lead/contact status tracking.
4. Automatic updating of lead status after every action.

The user should only need to open the dashboard and press **Start**.

No complex CRM, analytics platform, public dashboard, or cloud lead database is required.

---

# 2. Core Principle

### Local-first

All lead data, processing state, logs, and automation logic should remain on the user's local machine.

External services are used only where necessary:

* Gmail API → email delivery
* WhatsApp Business/API provider → WhatsApp delivery
* Google OAuth → Gmail authorization

The system must not upload the complete lead database to a separate third-party dashboard.

---

# 3. Dashboard

The dashboard should be extremely simple.

### Main screen

```text
┌─────────────────────────────────────────────┐
│       D WEB STUDIO — OUTREACH               │
│                                             │
│  Status: ● READY                            │
│                                             │
│  Leads       70                             │
│  Completed   12                             │
│  Pending     58                             │
│  Failed       0                             │
│                                             │
│          [ START AUTOMATION ]               │
│                                             │
│  Current Lead: Rohit Kumar                  │
│  Current Task: Sending Email...             │
│                                             │
│  ✓ Prachi Lilhare — Completed               │
│  ✓ Pintu — Completed                        │
│  → Rohit Kumar — Processing                 │
│  ○ Next Lead — Pending                      │
│                                             │
│  Progress: 12 / 70                          │
└─────────────────────────────────────────────┘
```

The dashboard should not contain unnecessary features.

---

# 4. Start Button

When the user presses:

**START AUTOMATION**

the system should:

1. Load the local lead database/Excel.
2. Find eligible Priority leads.
3. Skip leads already completed.
4. Process the next pending lead.
5. Send email if available.
6. Check/process WhatsApp if available.
7. Update statuses.
8. Move to the next lead.
9. Continue until all eligible leads are processed.

---

# 5. Lead Processing

For every lead:

```text
Lead
 ↓
Check Email
 ↓
Check WhatsApp
 ↓
Generate personalized message
 ↓
Send Email
 ↓
Send WhatsApp
 ↓
Save result
 ↓
Next Lead
```

The system must process each channel independently.

Example:

```text
Rohit Kumar

Email: Sent
WhatsApp: Not Available
Lead Status: Completed
```

The WhatsApp failure/absence must not prevent the email from being processed.

---

# 6. Email System

### Provider

Gmail API with OAuth authentication.

The user authorizes their Gmail account once.

The system then sends emails through the authorized Gmail account.

### Email statuses

Allowed states:

```text
PENDING
SENT
FAILED
NOT_AVAILABLE
```

### Email workflow

```text
Email exists?
   │
   ├── NO → NOT_AVAILABLE
   │
   └── YES
        ↓
     Send Email
        ↓
   ┌────┴────┐
   │         │
Success    Failure
   │         │
 SENT      FAILED
```

The system must save the Gmail API response/message ID where available.

---

# 7. WhatsApp System

### Provider

Configured WhatsApp Business/API provider.

The system should use the user's configured WhatsApp API credentials.

### WhatsApp statuses

```text
PENDING
SENT
FAILED
NOT_AVAILABLE
UNKNOWN
```

If the API supports recipient/WhatsApp-number validation, the system may use that response.

The system must not falsely mark a number as WhatsApp available when the API has not confirmed it.

---

# 8. Lead Status

Each lead has an overall status:

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
Email       = SENT
WhatsApp    = NOT_AVAILABLE
Lead Status = COMPLETED
```

The lead is considered completed when all applicable channels have been processed.

---

# 9. Local Lead Data

Existing Excel data should remain compatible.

Existing fields include:

```text
Name
Email
Phone
Priority
Gender
Age
City/State
Degree
Source
```

Additional fields:

```text
Email Status
WhatsApp Status
Lead Status
Last Contacted At
Email Message ID
WhatsApp Message ID
Error
```

The automation must preserve existing lead information.

---

# 10. Duplicate Protection

The system must never repeatedly send the same message to a completed lead.

Example:

```text
Email Status = SENT
```

means the email automation skips that email on the next run.

Likewise:

```text
WhatsApp Status = SENT
```

means WhatsApp is skipped.

This allows the user to safely restart the automation after interruption.

---

# 11. Resume After Interruption

If the application closes or the computer restarts:

```text
Start
 ↓
Read saved statuses
 ↓
Skip completed actions
 ↓
Continue from pending actions
```

Example:

```text
Rohit

Email      = SENT
WhatsApp   = PENDING
```

On the next run, the system must **not send the email again**.

It should continue with WhatsApp.

---

# 12. Message Personalization

Messages should be generated from templates.

Example:

```text
Hi {{name}},

I'm Divyansh from D Web Studio...
```

The system replaces:

```text
{{name}}
```

with the lead's actual name.

Example:

```text
Hi Rohit,
```

Business-specific information must only be inserted when that information has been verified.

The system must not invent a company, job, business, or other personal information.

---

# 13. Processing Log

The dashboard should show a simple live activity feed.

Example:

```text
✓ Prachi Lilhare — Email sent
✓ Prachi Lilhare — WhatsApp sent

✓ Pintu — Email sent
• Pintu — WhatsApp unavailable

→ Rohit Kumar — Sending email...

○ Next lead — Pending
```

No complicated analytics are required.

---

# 14. Progress

Dashboard should show:

```text
Completed: 12
Pending: 58
Failed: 0
```

And:

```text
12 / 70
```

with a simple progress indicator.

---

# 15. Completion State

When all eligible leads are processed:

```text
┌─────────────────────────────────────┐
│                                     │
│          ALL DONE ✓                 │
│                                     │
│     70 / 70 leads processed         │
│                                     │
│     Email: 65 sent                  │
│     WhatsApp: 51 sent               │
│     Unavailable: 19                 │
│     Failed: 2                       │
│                                     │
└─────────────────────────────────────┘
```

The automation should stop automatically.

---

# 16. Error Handling

Errors must not crash the entire automation.

Example:

```text
Lead 1 → Success
Lead 2 → Success
Lead 3 → Email Failed
Lead 4 → Continue
```

The failed action should be saved:

```text
Lead Status = FAILED
Error = <short error description>
```

The system should continue processing other eligible leads.

---

# 17. Security

Sensitive credentials must never be stored inside Excel.

Do not store:

* Gmail password
* Gmail OAuth secrets
* WhatsApp API keys
* API access tokens

inside the lead spreadsheet.

Use local environment/configuration files with appropriate protection.

Credentials must never be committed to GitHub.

---

# 18. No Cloud CRM

The product does NOT require:

* Salesforce
* HubSpot
* Airtable
* Supabase
* Firebase
* Online CRM
* Public lead dashboard

The lead database and automation state should remain local.

---

# 19. UI Requirements

The UI should have only the essentials:

### Required

* Start button
* Current status
* Total leads
* Completed count
* Pending count
* Failed count
* Current lead
* Current action
* Progress
* Activity log
* Completion message

### Not required

* Complex charts
* Sales pipeline
* User management
* Team accounts
* Billing
* CRM features
* Complex settings
* Social analytics

---

# 20. Architecture

```text
                 LOCAL MACHINE
                      │
                      ▼
             ┌─────────────────┐
             │    Dashboard    │
             └────────┬────────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Outreach Engine │
             └───────┬─────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   ┌─────────────┐       ┌──────────────┐
   │ Email Module│       │WhatsApp Module│
   └──────┬──────┘       └───────┬──────┘
          │                      │
          ▼                      ▼
      Gmail API             WhatsApp API
          │                      │
          └──────────┬───────────┘
                     ▼
             Local Status Store
                     │
                     ▼
                 Excel / DB
```

---

# 21. MVP

The first version should only implement:

### Phase 1

* Local dashboard
* Excel import/read
* Priority lead filtering
* Gmail OAuth
* Gmail email sending
* WhatsApp API connection
* WhatsApp sending
* Email status
* WhatsApp status
* Lead status
* Progress counter
* Activity log
* Resume after interruption
* Completion screen

### Phase 2

Later we can add:

* Better message templates
* Multiple campaigns
* Scheduling
* Advanced filtering
* Search
* Retry controls
* More detailed logs

These are NOT required for the first version.

---

# 22. Success Criteria

The MVP is successful when the user can:

1. Open the local dashboard.
2. Load/use the existing lead file.
3. Press **START AUTOMATION**.
4. Have eligible leads processed automatically.
5. Send email through Gmail API.
6. Send WhatsApp through the configured WhatsApp API.
7. See live progress.
8. See Sent / Failed / Not Available statuses.
9. Close/reopen the application and safely resume.
10. Reach an **ALL DONE** state when everything eligible is processed.

The user should not need to manually process individual leads during normal operation.
