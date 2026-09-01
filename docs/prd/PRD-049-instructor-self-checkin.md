# PRD-049: Instructor self check-in

## Summary of the implementation

A `Registrar presença` (`Record attendance`) button on the instructor's dashboard for each class/open class of the day. On click, it records the instructor's explicit attendance with no need for approval. The instructor's attendance is now derived from that record (not from students' approvals).

## Demand type

New feature with a schema change + new UI + new endpoints.

## Current problem

- The instructor's attendance does not exist as an entity of its own in the system.
- The instructor's attendance history (`attendance_history`) showed students' check-ins — the wrong data to represent the instructor's attendance.
- There is no mechanism for the instructor to record that they themselves taught the class.

## Goal

Give the instructor explicit control over recording their own attendance, conceptually separating "instructor attendance" from "student attendance".

## Context Ledger

### Files read in full

- `system/models/calendar.py`
- `system/services/class_calendar.py`
- `system/views/calendar_views.py`
- `system/urls.py`
- `templates/home/dashboard.html`
- `system/tests/test_calendar.py`
- `system/views/home_views.py`

### Limitations found

- A schema change is mandatory: `ClassSession.instructor_present`, `ClassSession.instructor_checked_in_at`, `SpecialClass.instructor_present`, `SpecialClass.instructor_checked_in_at`
- It requires the destructive cycle to be run by the user

## Business rule

- The instructor was present if they themselves clicked `Registrar presença` (`Record attendance`) for that session/open class
- The record is idempotent (clicking twice does not duplicate it)
- The record can only be made on the day of the class (`date == today`)
- A cancelled class does not allow a record
- Only the instructor responsible for the class may record attendance for it

## Scope

1. `system/models/calendar.py` — 4 new fields in `ClassSession` and `SpecialClass`
2. `system/services/class_calendar.py` — 3 new functions + updates to `get_today_classes_for_instructor` and `get_instructor_checkin_history`
3. `system/views/calendar_views.py` — 2 new JSON views
4. `system/urls.py` — 2 new routes
5. `templates/home/dashboard.html` — a button per class + an update to the home-config JSON
6. `static/system/js/dashboard.js` — a JavaScript handler for the self check-in
7. `system/tests/test_calendar.py` — tests of the new functions and views

## Out of scope

- Editing or undoing the attendance record by the instructor
- A consolidated attendance report
- Automatic integration with the payout calculation

## Impacted files

| File | Change |
|---|---|
| `system/models/calendar.py` | `instructor_present`, `instructor_checked_in_at` in `ClassSession` and `SpecialClass` |
| `system/services/class_calendar.py` | `register_instructor_self_checkin`, `register_instructor_self_special_checkin`, `get_instructor_attendance_history` + updates |
| `system/views/calendar_views.py` | `InstructorSelfCheckinView`, `InstructorSelfSpecialCheckinView` |
| `system/urls.py` | 2 new routes |
| `templates/home/dashboard.html` | a button per class item + the URLs in the config JSON |
| `static/system/js/dashboard.js` | the self check-in handler |
| `system/tests/test_calendar.py` | new tests |

## Risks and edge cases

- The session does not exist when the instructor tries to record attendance → the service creates the session (`get_or_create`)
- The instructor tries to record attendance for another class → a `PermissionError`
- An open class on a date other than today → a `ValueError`

## Visual hierarchy

- Reading pattern: F Pattern
- The `Registrar presença` (`Record attendance`) button: `btn--sm`, `--border` border, weight 500
- The `Presente` (`Present`) badge: `status-pill--success`, green, weight 600
- Clear separation from the student approval button

## Wireframe

```
[09:00]  Adult Class · Adult          [3 students]
         3 confirmed
         [Record attendance]   ← new

[09:00]  Adult Class · Adult          [3 students]
         3 confirmed
         ✓ Present at 09:02   ← after recording
```

## State machines

### The attendance button per class

- `not_present`: the session exists or not, `instructor_present = False` → a `Registrar presença` (`Record attendance`) button
- `present`: `instructor_present = True` → a `Presente` (`Present`) badge + the time
- `cancelled`: the class is cancelled → no button (not applicable)

## Acceptance criteria

- [ ] The `Registrar presença` (`Record attendance`) button appears for each non-cancelled class of the day (verifiable: visual)
- [ ] After clicking, the button disappears and a `Presente` (`Present`) badge appears with the time (verifiable: visual + DOM)
- [ ] A second attempt returns `created: false` with no error (verifiable: network)
- [ ] An instructor of another class gets a 403 (verifiable: terminal)
- [ ] The instructor's history shows their own attendance days (verifiable: visual)
- [ ] `manage.py test --verbosity 2` passes (verifiable: terminal)
- [ ] `manage.py check` passes (verifiable: terminal)

## Plan

- [x] 1. Full reading
- [ ] 2. Models (the schema change)
- [ ] 3. Services
- [ ] 4. Views + URLs
- [ ] 5. Template + JavaScript
- [ ] 6. Tests
- [ ] 7. The destructive cycle (the user)
- [ ] 8. Visual validation

## Implemented

(fill in after implementation)

## Deviations from plan

(fill in when there are any)

## Pending

- The destructive cycle to be run by the user after the schema changes
