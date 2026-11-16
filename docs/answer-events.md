# Answer events (for the ELIOS app)

The app sends **one event per quiz answer** to Supabase. Nothing else leaves the device: no name, no
email, no device id.

```
POST {SUPABASE_URL}/rest/v1/answer_events
apikey: {SUPABASE_ANON_KEY}
Authorization: Bearer {SUPABASE_ANON_KEY}
Content-Type: application/json
Prefer: return=minimal

{"guide_date":"2026-11-08","question_id":"q2","lang":"en","chosen":"b","correct":false,"attempt":1,"client_id":"<uuid>"}
```

| Field | Meaning |
|---|---|
| `guide_date` | the guide's `date` in the catalogue (`YYYY-MM-DD`) |
| `question_id` | `q1`-`q3` for the printed quiz, `p1`, `p2`, ... for `_quiz_pool` in order |
| `lang` | `en` or `id` |
| `chosen` | the option picked, `a`-`d` (pool answers are indexes 0-3: 0 = `a`) |
| `correct` | whether it was right |
| `attempt` | 1 for the first try of that question on this install, 2 for "Try the quiz again", ... |
| `client_id` | random UUID created at first launch and kept on the device; delete it with the app data |

Rules: send the event when the student confirms an answer; skip it silently when offline (do not
queue personal data, and a lost event is fine); never send free text. A duplicate
(`client_id`, `guide_date`, `question_id`, `attempt`) is rejected by the database, so retrying is safe.

The anon key may only insert. Reading goes through `question_stats()` for the dashboard login and the
`service_role` key used by GitHub Actions (see [supabase/schema.sql](../supabase/schema.sql)).

Privacy: the audience is 12-15. Show a short notice that answers are counted anonymously to improve the
guides, and check the rules that apply to you (Indonesian PDP law; GDPR/COPPA if the app is used abroad).
