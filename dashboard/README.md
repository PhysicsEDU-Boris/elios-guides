# ELIOS Question Insights (dashboard)

A static page: no build step, no server code. It shows, for a period you choose, which quiz questions are
missed most, how the answers split across A-D (right answer green, most common wrong answer dark red), and
which concept (formula) is next in line for a remedial guide. Data comes from `question_stats()` in Supabase (built on the quiz results the app already stores; the wrong option chosen is shown once the backend saves it);
question and option texts come from the published guides on GitHub Pages.

## Set up

1. **Supabase**: run [../supabase/schema.sql](../supabase/schema.sql) in the SQL editor of the existing ELIOS project, then allow yourself:
   `insert into public.dashboard_users values ('you@example.com');`
2. **Config**: put the project URL and the **anon** key in [config.js](config.js) (Settings -> API). The anon
   key is public by design; never use the `service_role` key here.
3. **Vercel**: import this repository, set **Root Directory** to `dashboard`, framework preset **Other**, no
   build command, no output directory. [vercel.json](vercel.json) adds `noindex`, no-store and anti-framing headers.
4. **Supabase Auth -> URL configuration**: set the Site URL and a Redirect URL to your Vercel address, so the
   email login link comes back to the dashboard.

Access is by email magic link and the `dashboard_users` allow-list: anyone else who logs in is told they are
not on the list and gets no data (the database refuses `question_stats()` for them).

`supabase.min.js` is `@supabase/supabase-js` 2.117.3 (MIT licence), kept here so the page loads nothing from
third-party CDNs. Guide text is always inserted as text, never as HTML.
