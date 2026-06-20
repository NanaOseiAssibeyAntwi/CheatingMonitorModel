# Supabase Architecture For Chetect

## What the current app already needs

From the existing student, invigilator, exam-session, monitor, and reports flows, the app needs these data domains:

- Authentication and role-aware profiles for students and invigilators.
- Courses and scheduled exams.
- Student registrations for each exam.
- Invigilator assignments to exams.
- Live proctoring sessions per student per exam.
- Frame-by-frame analysis results from the Python detector.
- Suspicious events grouped from sampled frames.
- Reviewed reports and integrity decisions.
- Notifications for alerts and exam updates.

## Table mapping

- `profiles`: app user profile linked to `auth.users`.
- `courses`: reusable course catalog such as `CS 450`.
- `exams`: actual sittings of a course with date, duration, room, and monitoring mode.
- `exam_invigilators`: which invigilators oversee each exam.
- `exam_registrations`: which students are registered for each exam.
- `analysis_sessions`: one live or completed proctoring attempt for a student in an exam.
- `analysis_frames`: sampled frame outputs, metrics, and observations.
- `suspicious_events`: grouped incidents such as gaze deviation, no-face periods, or multiple-face detection.
- `session_reviews`: invigilator-reviewed integrity result for a completed session.
- `notifications`: in-app alerts.
- `audit_logs`: admin/staff trace of sensitive actions.

## Views included in the SQL

- `session_report_view`: report-ready join for the results/report screens.
- `invigilator_live_overview`: dashboard summary of live sessions and flagged counts.
- `student_exam_schedule`: student-facing exam list with latest session status.

## Security notes

- Use the Supabase anon key in the Expo app.
- Do not put the Supabase `service_role` key in any `EXPO_PUBLIC_*` variable.
- Keep service-role usage on a trusted backend, Edge Function, or server process only.
- The SQL enables RLS so students can only see their own records, while invigilators can see the exams they supervise.

## Recommended next app-side pieces

- `lib/supabase.ts` client setup for Expo.
- Auth flow wired to `auth.users` plus the `profiles` trigger.
- A backend or Edge Function that receives uploads and writes `analysis_sessions`, `analysis_frames`, and `suspicious_events`.
- Private Supabase Storage buckets for uploaded exam media and generated report exports.

## File to run

Run this in the Supabase SQL editor:

- `supabase/schema.sql`
