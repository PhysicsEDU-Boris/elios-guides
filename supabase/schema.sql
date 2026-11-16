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
