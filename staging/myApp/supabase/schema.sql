begin;

create extension if not exists pgcrypto;
create extension if not exists citext;

create type public.app_role as enum ('student', 'invigilator', 'admin');
create type public.exam_status as enum ('draft', 'scheduled', 'live', 'completed', 'cancelled');
create type public.monitoring_mode as enum ('standard', 'strict', 'minimal');
create type public.session_status as enum ('pending', 'active', 'paused', 'submitted', 'completed', 'terminated');
create type public.analysis_label as enum ('NO_FACE', 'NORMAL', 'CAUTION', 'SUSPICIOUS');
create type public.risk_level as enum ('low', 'medium', 'high', 'critical');
create type public.review_status as enum ('open', 'acknowledged', 'resolved', 'dismissed');
create type public.review_decision as enum ('clear', 'warning', 'flagged', 'confirmed_cheating');

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  email citext unique,
  full_name text not null,
  role public.app_role not null default 'student',
  institutional_id text unique,
  department_name text,
  avatar_url text,
  phone text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table public.courses (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  title text not null,
  department_name text,
  level text,
  term text,
  description text,
  created_by uuid references public.profiles (id) on delete set null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table public.exams (
  id uuid primary key default gen_random_uuid(),
  course_id uuid not null references public.courses (id) on delete cascade,
  title text not null,
  created_by uuid references public.profiles (id) on delete set null,
  academic_session text,
  scheduled_start timestamptz not null,
  duration_minutes integer not null check (duration_minutes > 0),
  scheduled_end timestamptz generated always as (scheduled_start + make_interval(mins => duration_minutes)) stored,
  room_name text,
  instructions text,
  access_code text,
  max_students integer not null default 50 check (max_students > 0),
  monitoring_mode public.monitoring_mode not null default 'standard',
  status public.exam_status not null default 'draft',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table public.exam_invigilators (
  exam_id uuid not null references public.exams (id) on delete cascade,
  invigilator_id uuid not null references public.profiles (id) on delete cascade,
  assigned_by uuid references public.profiles (id) on delete set null,
  assigned_at timestamptz not null default timezone('utc', now()),
  primary key (exam_id, invigilator_id)
);

create table public.exam_registrations (
  id uuid primary key default gen_random_uuid(),
  exam_id uuid not null references public.exams (id) on delete cascade,
  student_id uuid not null references public.profiles (id) on delete cascade,
  candidate_number text,
  seat_number text,
  registration_status text not null default 'registered' check (
    registration_status in ('registered', 'checked_in', 'active', 'submitted', 'completed', 'absent', 'cancelled')
  ),
  registered_at timestamptz not null default timezone('utc', now()),
  submitted_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  unique (exam_id, student_id)
);

create table public.analysis_sessions (
  id uuid primary key default gen_random_uuid(),
  backend_session_id text unique,
  exam_id uuid not null references public.exams (id) on delete cascade,
  registration_id uuid references public.exam_registrations (id) on delete set null,
  student_id uuid not null references public.profiles (id) on delete cascade,
  status public.session_status not null default 'pending',
  started_at timestamptz not null default timezone('utc', now()),
  ended_at timestamptz,
  source text not null default 'mobile',
  device_info jsonb not null default '{}'::jsonb,
  analysis_config jsonb not null default '{}'::jsonb,
  frames_processed integer not null default 0 check (frames_processed >= 0),
  frames_sampled integer not null default 0 check (frames_sampled >= 0),
  detections integer not null default 0 check (detections >= 0),
  max_score integer not null default 0 check (max_score between 0 and 100),
  average_score numeric(6, 2) not null default 0 check (average_score >= 0),
  final_label public.analysis_label not null default 'NO_FACE',
  suspicious_event_count integer not null default 0 check (suspicious_event_count >= 0),
  latest_observation text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (ended_at is null or ended_at >= started_at)
);

create unique index analysis_sessions_active_exam_student_idx
on public.analysis_sessions (exam_id, student_id)
where status in ('pending', 'active', 'paused');

create table public.analysis_frames (
  id bigint generated always as identity primary key,
  analysis_session_id uuid not null references public.analysis_sessions (id) on delete cascade,
  frame_index integer not null check (frame_index >= 0),
  timestamp_seconds numeric(10, 2) not null default 0 check (timestamp_seconds >= 0),
  detected boolean not null default false,
  face_count integer not null default 0 check (face_count >= 0),
  score integer check (score between 0 and 100),
  label public.analysis_label not null default 'NO_FACE',
  label_color jsonb not null default '[]'::jsonb,
  observations jsonb not null default '[]'::jsonb,
  gaze_x numeric(8, 4),
  gaze_y numeric(8, 4),
  blink_rate numeric(8, 4),
  head_yaw numeric(8, 4),
  head_pitch numeric(8, 4),
  head_roll numeric(8, 4),
  ear numeric(8, 4),
  landmarks jsonb,
  captured_at timestamptz not null default timezone('utc', now()),
  unique (analysis_session_id, frame_index)
);

create table public.suspicious_events (
  id uuid primary key default gen_random_uuid(),
  analysis_session_id uuid not null references public.analysis_sessions (id) on delete cascade,
  exam_id uuid not null references public.exams (id) on delete cascade,
  student_id uuid not null references public.profiles (id) on delete cascade,
  label public.analysis_label not null,
  reason text not null,
  risk_level public.risk_level not null default 'medium',
  source text not null default 'ai',
  start_timestamp_seconds numeric(10, 2) not null default 0 check (start_timestamp_seconds >= 0),
  end_timestamp_seconds numeric(10, 2) not null default 0 check (end_timestamp_seconds >= start_timestamp_seconds),
  start_frame_index integer not null default 0 check (start_frame_index >= 0),
  end_frame_index integer not null default 0 check (end_frame_index >= start_frame_index),
  frame_count integer not null default 1 check (frame_count > 0),
  max_score integer check (max_score between 0 and 100),
  review_status public.review_status not null default 'open',
  reviewed_by uuid references public.profiles (id) on delete set null,
  reviewed_at timestamptz,
  notes text,
  created_at timestamptz not null default timezone('utc', now())
);

create table public.session_reviews (
  id uuid primary key default gen_random_uuid(),
  analysis_session_id uuid not null unique references public.analysis_sessions (id) on delete cascade,
  reviewer_id uuid not null references public.profiles (id) on delete restrict,
  integrity_score numeric(5, 2) not null check (integrity_score between 0 and 100),
  final_decision public.review_decision not null,
  summary text,
  action_notes text,
  reviewed_at timestamptz not null default timezone('utc', now()),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table public.notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  title text not null,
  body text not null,
  notification_type text not null,
  data jsonb not null default '{}'::jsonb,
  read_at timestamptz,
  created_at timestamptz not null default timezone('utc', now())
);

create table public.audit_logs (
  id bigint generated always as identity primary key,
  actor_id uuid references public.profiles (id) on delete set null,
  entity_type text not null,
  entity_id text not null,
  action text not null,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now())
);

create index idx_profiles_role on public.profiles (role);
create index idx_courses_department on public.courses (department_name);
create index idx_exams_course_status on public.exams (course_id, status, scheduled_start desc);
create index idx_exam_registrations_student on public.exam_registrations (student_id, exam_id);
create index idx_analysis_sessions_exam on public.analysis_sessions (exam_id, status, started_at desc);
create index idx_analysis_sessions_student on public.analysis_sessions (student_id, started_at desc);
create index idx_analysis_frames_session on public.analysis_frames (analysis_session_id, frame_index);
create index idx_suspicious_events_session on public.suspicious_events (analysis_session_id, created_at desc);
create index idx_suspicious_events_exam on public.suspicious_events (exam_id, review_status, risk_level);
create index idx_notifications_user on public.notifications (user_id, created_at desc);

create or replace function public.current_app_role()
returns public.app_role
language sql
stable
security definer
set search_path = public
as $$
  select role
  from public.profiles
  where id = auth.uid()
$$;

create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select coalesce(public.current_app_role() = 'admin', false)
$$;

create or replace function public.is_invigilator()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select coalesce(public.current_app_role() in ('invigilator', 'admin'), false)
$$;

create or replace function public.is_exam_invigilator(target_exam_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.exam_invigilators ei
    where ei.exam_id = target_exam_id
      and ei.invigilator_id = auth.uid()
  )
  or exists (
    select 1
    from public.exams e
    where e.id = target_exam_id
      and e.created_by = auth.uid()
  )
  or public.is_admin()
$$;

create trigger set_profiles_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

create trigger set_courses_updated_at
before update on public.courses
for each row execute function public.set_updated_at();

create trigger set_exams_updated_at
before update on public.exams
for each row execute function public.set_updated_at();

create trigger set_analysis_sessions_updated_at
before update on public.analysis_sessions
for each row execute function public.set_updated_at();

create trigger set_session_reviews_updated_at
before update on public.session_reviews
for each row execute function public.set_updated_at();

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  requested_role text;
begin
  requested_role := lower(coalesce(new.raw_user_meta_data ->> 'role', 'student'));

  insert into public.profiles (
    id,
    email,
    full_name,
    role,
    institutional_id,
    department_name,
    avatar_url,
    metadata
  )
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data ->> 'full_name', split_part(coalesce(new.email, ''), '@', 1)),
    case
      when requested_role in ('student', 'invigilator', 'admin') then requested_role::public.app_role
      else 'student'::public.app_role
    end,
    new.raw_user_meta_data ->> 'institutional_id',
    new.raw_user_meta_data ->> 'department_name',
    new.raw_user_meta_data ->> 'avatar_url',
    coalesce(new.raw_user_meta_data, '{}'::jsonb)
  )
  on conflict (id) do update
    set email = excluded.email,
        full_name = coalesce(public.profiles.full_name, excluded.full_name);

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_user();

alter table public.profiles enable row level security;
alter table public.courses enable row level security;
alter table public.exams enable row level security;
alter table public.exam_invigilators enable row level security;
alter table public.exam_registrations enable row level security;
alter table public.analysis_sessions enable row level security;
alter table public.analysis_frames enable row level security;
alter table public.suspicious_events enable row level security;
alter table public.session_reviews enable row level security;
alter table public.notifications enable row level security;
alter table public.audit_logs enable row level security;

create policy "profiles_select_self_or_staff"
on public.profiles
for select
to authenticated
using (id = auth.uid() or public.is_invigilator());

create policy "profiles_insert_self"
on public.profiles
for insert
to authenticated
with check (id = auth.uid());

create policy "profiles_update_self_or_admin"
on public.profiles
for update
to authenticated
using (id = auth.uid() or public.is_admin())
with check (id = auth.uid() or public.is_admin());

create policy "courses_read_authenticated"
on public.courses
for select
to authenticated
using (true);

create policy "courses_manage_staff"
on public.courses
for all
to authenticated
using (public.is_invigilator())
with check (public.is_invigilator());

create policy "exams_select_relevant"
on public.exams
for select
to authenticated
using (
  public.is_invigilator()
  or exists (
    select 1
    from public.exam_registrations er
    where er.exam_id = exams.id
      and er.student_id = auth.uid()
  )
);

create policy "exams_manage_staff"
on public.exams
for all
to authenticated
using (public.is_invigilator())
with check (public.is_invigilator());

create policy "exam_invigilators_select_relevant"
on public.exam_invigilators
for select
to authenticated
using (
  invigilator_id = auth.uid()
  or public.is_exam_invigilator(exam_id)
  or exists (
    select 1
    from public.exam_registrations er
    where er.exam_id = exam_invigilators.exam_id
      and er.student_id = auth.uid()
  )
);

create policy "exam_invigilators_manage_staff"
on public.exam_invigilators
for all
to authenticated
using (public.is_invigilator())
with check (public.is_invigilator());

create policy "exam_registrations_select_relevant"
on public.exam_registrations
for select
to authenticated
using (
  student_id = auth.uid()
  or public.is_exam_invigilator(exam_id)
);

create policy "exam_registrations_manage_staff"
on public.exam_registrations
for all
to authenticated
using (public.is_invigilator())
with check (public.is_invigilator());

create policy "analysis_sessions_select_relevant"
on public.analysis_sessions
for select
to authenticated
using (
  student_id = auth.uid()
  or public.is_exam_invigilator(exam_id)
);

create policy "analysis_sessions_insert_student_or_staff"
on public.analysis_sessions
for insert
to authenticated
with check (
  student_id = auth.uid()
  or public.is_exam_invigilator(exam_id)
);

create policy "analysis_sessions_update_student_or_staff"
on public.analysis_sessions
for update
to authenticated
using (
  student_id = auth.uid()
  or public.is_exam_invigilator(exam_id)
)
with check (
  student_id = auth.uid()
  or public.is_exam_invigilator(exam_id)
);

create policy "analysis_frames_select_relevant"
on public.analysis_frames
for select
to authenticated
using (
  exists (
    select 1
    from public.analysis_sessions s
    where s.id = analysis_frames.analysis_session_id
      and (s.student_id = auth.uid() or public.is_exam_invigilator(s.exam_id))
  )
);

create policy "analysis_frames_insert_relevant"
on public.analysis_frames
for insert
to authenticated
with check (
  exists (
    select 1
    from public.analysis_sessions s
    where s.id = analysis_frames.analysis_session_id
      and (s.student_id = auth.uid() or public.is_exam_invigilator(s.exam_id))
  )
);

create policy "suspicious_events_select_relevant"
on public.suspicious_events
for select
to authenticated
using (
  student_id = auth.uid()
  or public.is_exam_invigilator(exam_id)
);

create policy "suspicious_events_insert_relevant"
on public.suspicious_events
for insert
to authenticated
with check (
  student_id = auth.uid()
  or public.is_exam_invigilator(exam_id)
);

create policy "suspicious_events_update_staff"
on public.suspicious_events
for update
to authenticated
using (public.is_exam_invigilator(exam_id))
with check (public.is_exam_invigilator(exam_id));

create policy "session_reviews_select_relevant"
on public.session_reviews
for select
to authenticated
using (
  reviewer_id = auth.uid()
  or exists (
    select 1
    from public.analysis_sessions s
    where s.id = session_reviews.analysis_session_id
      and (s.student_id = auth.uid() or public.is_exam_invigilator(s.exam_id))
  )
);

create policy "session_reviews_manage_staff"
on public.session_reviews
for all
to authenticated
using (
  exists (
    select 1
    from public.analysis_sessions s
    where s.id = session_reviews.analysis_session_id
      and public.is_exam_invigilator(s.exam_id)
  )
)
with check (
  exists (
    select 1
    from public.analysis_sessions s
    where s.id = session_reviews.analysis_session_id
      and public.is_exam_invigilator(s.exam_id)
  )
);

create policy "notifications_select_own"
on public.notifications
for select
to authenticated
using (user_id = auth.uid() or public.is_admin());

create policy "notifications_manage_staff"
on public.notifications
for all
to authenticated
using (public.is_invigilator())
with check (public.is_invigilator());

create policy "audit_logs_select_admin"
on public.audit_logs
for select
to authenticated
using (public.is_admin());

create policy "audit_logs_insert_staff"
on public.audit_logs
for insert
to authenticated
with check (public.is_invigilator());

create or replace view public.session_report_view as
select
  s.id as analysis_session_id,
  s.backend_session_id,
  s.exam_id,
  e.title as exam_title,
  e.status as exam_status,
  e.scheduled_start,
  c.code as course_code,
  c.title as course_title,
  s.student_id,
  p.full_name as student_name,
  p.institutional_id as student_number,
  s.status as session_status,
  s.started_at,
  s.ended_at,
  s.frames_sampled,
  s.detections,
  s.max_score,
  s.average_score,
  s.final_label,
  s.suspicious_event_count,
  greatest(0, 100 - s.max_score) as calculated_integrity_score,
  sr.integrity_score as reviewed_integrity_score,
  sr.final_decision,
  sr.reviewed_at
from public.analysis_sessions s
join public.exams e on e.id = s.exam_id
join public.courses c on c.id = e.course_id
join public.profiles p on p.id = s.student_id
left join public.session_reviews sr on sr.analysis_session_id = s.id;

create or replace view public.invigilator_live_overview as
select
  e.id as exam_id,
  c.code as course_code,
  c.title as course_title,
  e.title as exam_title,
  e.status,
  e.monitoring_mode,
  e.scheduled_start,
  count(distinct er.student_id) as registered_students,
  count(distinct s.id) filter (where s.status in ('pending', 'active', 'paused')) as live_sessions,
  count(distinct s.id) filter (where s.max_score >= 75 or s.suspicious_event_count > 0) as flagged_sessions,
  coalesce(max(s.max_score), 0) as highest_score
from public.exams e
join public.courses c on c.id = e.course_id
left join public.exam_registrations er on er.exam_id = e.id
left join public.analysis_sessions s on s.exam_id = e.id
group by e.id, c.code, c.title, e.title, e.status, e.monitoring_mode, e.scheduled_start;

create or replace view public.student_exam_schedule as
select
  er.student_id,
  e.id as exam_id,
  c.code as course_code,
  c.title as course_title,
  e.title as exam_title,
  e.scheduled_start,
  e.scheduled_end,
  e.room_name,
  e.status,
  e.monitoring_mode,
  er.registration_status,
  s.id as latest_session_id,
  s.status as latest_session_status,
  s.final_label as latest_final_label,
  s.max_score as latest_max_score
from public.exam_registrations er
join public.exams e on e.id = er.exam_id
join public.courses c on c.id = e.course_id
left join lateral (
  select s1.*
  from public.analysis_sessions s1
  where s1.exam_id = e.id
    and s1.student_id = er.student_id
  order by s1.started_at desc
  limit 1
) s on true;

commit;
