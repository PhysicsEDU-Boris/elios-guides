-- ELIOS question analytics, built on the data the app backend already stores in public.guide_progress
-- (ai-backend/guides.js: quiz = {attempts, best, first: {score, answers: [{qid, correct}]}}, qid p1-p3 for the
-- three printed questions, owner_id = Firebase uid). Nothing new is collected from students.
-- Run once in the Supabase SQL editor of the ELIOS project. Additive: no existing table is changed.

-- Who may open the dashboard (Supabase Auth login by email magic link). Only this function reads it.
create table if not exists public.dashboard_users (email text primary key);
alter table public.dashboard_users enable row level security;
revoke all on public.dashboard_users from anon, authenticated;

-- Per question over the last p_days (by last activity of the progress row) with at least p_min first
-- attempts: how often it was missed. chosen_* and top_wrong are filled once the backend also stores the
-- chosen option (answers[].choice); until then they are 0 and null. Returns no student identifiers.
create or replace function public.question_stats(p_days int default 30, p_min int default 20)
returns table (guide_date date, question_id text, attempts bigint, wrong bigint, wrong_rate numeric,
               chosen_a bigint, chosen_b bigint, chosen_c bigint, chosen_d bigint, top_wrong text)
language plpgsql security definer set search_path = public as $$
begin
  if coalesce(auth.role(), '') <> 'service_role'
     and not exists (select 1 from public.dashboard_users u where lower(u.email) = lower(coalesce(auth.jwt() ->> 'email', ''))) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  return query
    with ans as (
      select gp.date as d, a ->> 'qid' as qid, (a ->> 'correct')::boolean as ok, a ->> 'choice' as pick
      from public.guide_progress gp, jsonb_array_elements(gp.quiz -> 'first' -> 'answers') a
      where gp.quiz ? 'first' and gp.updated_at >= now() - make_interval(days => p_days)
    )
    select ans.d, ans.qid, count(*), count(*) filter (where not ans.ok),
           round(count(*) filter (where not ans.ok)::numeric / count(*), 3),
           count(*) filter (where ans.pick = 'a'), count(*) filter (where ans.pick = 'b'),
           count(*) filter (where ans.pick = 'c'), count(*) filter (where ans.pick = 'd'),
           mode() within group (order by ans.pick) filter (where not ans.ok and ans.pick is not null)
    from ans
    group by ans.d, ans.qid
    having count(*) >= p_min
    order by 5 desc, 3 desc;
end $$;

revoke all on function public.question_stats(int, int) from public, anon;
grant execute on function public.question_stats(int, int) to authenticated, service_role;

-- Dashboard access: add each person's login email, e.g.
--   insert into public.dashboard_users values ('you@example.com');

-- Overview numbers for the dashboard: guide reads, quiz/mini-lab stops, streaks, and scan types over the last
-- p_days. Counts only, no student identifiers. Streak = longest run of guide days a student finished a stop on
-- (a gap of up to 3 days is allowed so weekends without a guide do not break it). Scan device null = saved
-- before ELIOS 3 existed (counted as "unknown", never guessed). The robot "which bin" numbers assume the first
-- quiz question of an ELIOS 3 scan is the bin question.
create or replace function public.insights_summary(p_days int default 30)
returns jsonb language plpgsql security definer set search_path = public as $$
declare out jsonb;
begin
  if coalesce(auth.role(), '') <> 'service_role'
     and not exists (select 1 from public.dashboard_users u where lower(u.email) = lower(coalesce(auth.jwt() ->> 'email', ''))) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  with gp as (select * from public.guide_progress where updated_at >= now() - make_interval(days => p_days)),
  active as (select owner_id, date from gp where stops <> '{}'::jsonb),
  marked as (select owner_id, date, case when date - lag(date) over (partition by owner_id order by date) <= 3 then 0 else 1 end as brk from active),
  runs as (select owner_id, sum(brk) over (partition by owner_id order by date) as g from marked),
  best as (select owner_id, max(c) as b from (select owner_id, g, count(*) as c from runs group by 1, 2) y group by 1),
  sc as (select data from public.scan_history where updated_at >= now() - make_interval(days => p_days)),
  robot as (select data -> 'questions' -> 0 ->> 'isCorrect' as ok, data -> 'questions' -> 0 ->> 'rightAnswer' as right_a, data -> 'questions' -> 0 ->> 'yourAnswer' as your_a
            from sc where coalesce(data ->> 'kind', 'scan') = 'scan' and data ->> 'device' = 'elios' and jsonb_array_length(coalesce(data -> 'questions', '[]'::jsonb)) > 0)
  select jsonb_build_object(
    'students', (select count(distinct owner_id) from gp),
    'stops', (select jsonb_build_object('days', count(*), 'story', count(*) filter (where stops ? 'story'), 'physics', count(*) filter (where stops ? 'physics'),
                'quiz', count(*) filter (where stops ? 'quiz'), 'lab', count(*) filter (where stops ? 'lab')) from gp),
    'per_day', (select coalesce(jsonb_agg(jsonb_build_object('date', date, 'story', story, 'physics', physics, 'quiz', quiz, 'lab', lab) order by date), '[]'::jsonb)
                from (select date, count(*) filter (where stops ? 'story') as story, count(*) filter (where stops ? 'physics') as physics,
                      count(*) filter (where stops ? 'quiz') as quiz, count(*) filter (where stops ? 'lab') as lab from gp group by date) d),
    'streaks', jsonb_build_object(
      'none', (select count(distinct owner_id) from gp where owner_id not in (select owner_id from best)),
      'd1', (select count(*) from best where b = 1), 'd2_3', (select count(*) from best where b between 2 and 3),
      'd4_6', (select count(*) from best where b between 4 and 6), 'd7', (select count(*) from best where b >= 7)),
    'scans', jsonb_build_object(
      'total', (select count(*) from sc),
      'phone_quiz', (select count(*) from sc where coalesce(data ->> 'kind', 'scan') = 'scan' and data ->> 'device' = 'phone'),
      'robot', (select count(*) from sc where coalesce(data ->> 'kind', 'scan') = 'scan' and data ->> 'device' = 'elios'),
      'contribute', (select count(*) from sc where data ->> 'kind' = 'contribution'),
      'unknown_device', (select count(*) from sc where coalesce(data ->> 'kind', 'scan') = 'scan' and data ->> 'device' is null),
      'bins', (select coalesce(jsonb_object_agg(k, n), '{}'::jsonb) from (select coalesce(data ->> 'category', 'unknown') as k, count(*) as n from sc group by 1) b2),
      'robot_first', jsonb_build_object('right', (select count(*) from robot where ok = 'true'), 'wrong', (select count(*) from robot where ok = 'false'),
        'top_wrong', (select coalesce(jsonb_agg(jsonb_build_object('right', right_a, 'chosen', your_a, 'n', n)), '[]'::jsonb)
                      from (select right_a, your_a, count(*) as n from robot where ok = 'false' group by 1, 2 order by 3 desc limit 5) t))))
  into out;
  return out;
end $$;

revoke all on function public.insights_summary(int) from public, anon;
grant execute on function public.insights_summary(int) to authenticated, service_role;

-- Per guide day: how many students started the issue (any progress row) and finished each stop. Counts only.
create or replace function public.magazine_stats(p_days int default 365)
returns table (guide_date date, started bigint, story bigint, physics bigint, quiz bigint, lab bigint)
language plpgsql security definer set search_path = public as $$
begin
  if coalesce(auth.role(), '') <> 'service_role'
     and not exists (select 1 from public.dashboard_users u where lower(u.email) = lower(coalesce(auth.jwt() ->> 'email', ''))) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  return query select gp.date, count(*), count(*) filter (where gp.stops ? 'story'), count(*) filter (where gp.stops ? 'physics'),
    count(*) filter (where gp.stops ? 'quiz'), count(*) filter (where gp.stops ? 'lab')
    from public.guide_progress gp where gp.updated_at >= now() - make_interval(days => p_days) group by gp.date order by gp.date desc;
end $$;
revoke all on function public.magazine_stats(int) from public, anon;
grant execute on function public.magazine_stats(int) to authenticated, service_role;

-- Videos and clovers from the app's learning snapshots (elios-clean migration 202611210001_learning_snapshots:
-- one row per student, the latest snapshot wins). Students whose snapshot changed in the last p_days. Counts only.
create or replace function public.learning_stats(p_days int default 30)
returns jsonb language plpgsql security definer set search_path = public as $$
declare out jsonb;
begin
  if coalesce(auth.role(), '') <> 'service_role'
     and not exists (select 1 from public.dashboard_users u where lower(u.email) = lower(coalesce(auth.jwt() ->> 'email', ''))) then
    raise exception 'not allowed' using errcode = '42501';
  end if;
  with s as (select *, case when clovers_possible > 0 then clovers_earned * 100.0 / clovers_possible else 0 end as pct
             from public.learning_snapshots where updated_at >= now() - make_interval(days => p_days)),
  v as (select id, count(*) as started, count(*) filter (where id = any(s.watched_video_ids)) as watched
        from s, unnest(s.started_video_ids) id group by id)
  select jsonb_build_object(
    'students', (select count(*) from s),
    'clovers', (select jsonb_build_object('earned', coalesce(sum(clovers_earned), 0), 'possible', coalesce(sum(clovers_possible), 0),
      'b0', count(*) filter (where clovers_earned = 0), 'b1', count(*) filter (where clovers_earned > 0 and pct <= 25),
      'b2', count(*) filter (where pct > 25 and pct <= 50), 'b3', count(*) filter (where pct > 50 and pct <= 75),
      'b4', count(*) filter (where pct > 75)) from s),
    'videos', jsonb_build_object('started', (select coalesce(sum(started), 0) from v), 'watched', (select coalesce(sum(watched), 0) from v),
      'top', (select coalesce(jsonb_agg(jsonb_build_object('id', id, 'started', started, 'watched', watched) order by started desc, id), '[]'::jsonb)
              from (select * from v order by started desc, id limit 8) t)))
  into out;
  return out;
end $$;
revoke all on function public.learning_stats(int) from public, anon;
grant execute on function public.learning_stats(int) to authenticated, service_role;
