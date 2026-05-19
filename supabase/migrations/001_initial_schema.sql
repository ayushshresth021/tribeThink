-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Jobs table
create table public.jobs (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references auth.users(id) on delete cascade,
  video_storage_path text not null,
  status text not null default 'pending' check (status in ('pending', 'running', 'complete', 'failed')),
  error_message text,
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

-- Emotion reports table
create table public.emotion_reports (
  id uuid primary key default uuid_generate_v4(),
  job_id uuid not null references public.jobs(id) on delete cascade,
  chunks jsonb not null,
  summary text not null,
  disclaimer text not null,
  created_at timestamptz not null default now()
);

-- Row-level security
alter table public.jobs enable row level security;
alter table public.emotion_reports enable row level security;

create policy "Users can manage their own jobs"
  on public.jobs for all
  using (auth.uid() = user_id);

create policy "Users can read their own emotion reports"
  on public.emotion_reports for all
  using (
    exists (
      select 1 from public.jobs
      where jobs.id = emotion_reports.job_id
        and jobs.user_id = auth.uid()
    )
  );

-- Indexes
create index jobs_user_id_idx on public.jobs(user_id);
create index jobs_status_idx on public.jobs(status);
create index emotion_reports_job_id_idx on public.emotion_reports(job_id);
