-- ELIOS answer analytics. Run once in the Supabase SQL editor (Project -> SQL).
-- Anonymous: the app may only INSERT answer events. Nobody but the dashboard allow-list and the
-- service role (GitHub Actions) can read, and only through question_stats().

create table if not exists public.answer_events (
  id          bigint generated always as identity primary key,
  created_at  timestamptz not null default now(),
  guide_date  date        not null,
  question_id text        not null check (question_id ~ '^(q[1-3]|p[1-9][0-9]?)$'),  -- q1-q3 printed, p1.. quiz pool
  lang        text        not null check (lang in ('en', 'id')),
  chosen      text        not null check (chosen in ('a', 'b', 'c', 'd')),
  correct     boolean     not null,
  attempt     smallint    not null default 1 check (attempt between 1 and 20),
  client_id   uuid        not null,  -- random per app install, never a person or device id
  unique (client_id, guide_date, question_id, attempt)
);
create index if not exists answer_events_by_question on public.answer_events (guide_date, question_id);

create table if not exists public.dashboard_users (email text primary key);

alter table public.answer_events   enable row level security;
alter table public.dashboard_users enable row level security;

revoke all on public.answer_events, public.dashboard_users from anon, authenticated;
grant insert on public.answer_events to anon, authenticated;
create policy answer_events_insert on public.answer_events for insert to anon, authenticated with check (true);

-- Per question over the last p_days with at least p_min attempts: how often it was missed and which
-- wrong option was picked most. Callable by the allow-list (dashboard login) and the service role.
create or replace function public.question_stats(p_days int default 30, p_min int default 20)
returns table (guide_date date, question_id text, attempts bigint, wrong bigint, wrong_rate numeric,
               chosen_a bigint, chosen_b bigint, chosen_c bigint, chosen_d bigint, top_wrong text)
language plpgsql security definer set search_path = public as $$
begin
  if auth.role() <> 'service_role'
     and not exists (select 1 from public.dashboard_users u where lower(u.email) = lower(auth.jwt() ->> 'email')) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  return query
    select e.guide_date, e.question_id, count(*), count(*) filter (where not e.correct),
           round(count(*) filter (where not e.correct)::numeric / count(*), 3),
           count(*) filter (where e.chosen = 'a'), count(*) filter (where e.chosen = 'b'),
           count(*) filter (where e.chosen = 'c'), count(*) filter (where e.chosen = 'd'),
           mode() within group (order by e.chosen) filter (where not e.correct)
    from public.answer_events e
    where e.created_at >= now() - make_interval(days => p_days)
    group by e.guide_date, e.question_id
    having count(*) >= p_min
    order by 5 desc, 3 desc;
end $$;

revoke all on function public.question_stats(int, int) from public, anon;
grant execute on function public.question_stats(int, int) to authenticated, service_role;

-- Dashboard access: add each person's login email, e.g.
--   insert into public.dashboard_users values ('you@example.com');
