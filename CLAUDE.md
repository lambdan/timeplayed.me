Timeplayed is a service that tracks playtime. It originally only tracked through Discord (using Oblivionis), but nowadays can also do it through an API.

# Rules

- Never commit automatically
- Code should always be formatted (see Commands below)
- All tests should always pass
- Any new feature should have a test added if possible
- Never make any write requests to production without permission (reads are OK)
- Don't be cute. Timeplayed primary function is numbers and statistics. Think last.fm, but for playtime.
    - As an example, if you're making a "top played games" list, don't put in any "What kept you busy" paragraph. Just put a title (Top played games) and list the games!
- Avoid custom CSS as much as possible. We don't want to maintain that. Just use plain HTML or Bootstrap or whatever framework we use has to offer.
- The site is primarily developed for desktop usage. However, it should still be browsable and have no layout issues on mobile.
    - Especially the manual tracking page has to work well on mobile, as that is where it will most likely be used
- Site should be 100% compatible and look correct on Chromium based browsers, Safari (WebKit) and Firefox
    - Safari is particularly important on mobile
- In general, try to show as much info as possible, if it makes sense:
    - Eg, on a game page, it's redundant to show game cover and game name in the activity rows, because it will be at the top of the page. But on the front page or platform page, we should show game cover/name if there's room for it, as it won't be anywhere else on the page.
    - On mobile (small screens) remove less important stuff
- Always prefer readable, maintainable code over fancy code
    - Python ternaries (`x if cond else y`) are OK when both values are simple and the condition is short, so it reads like a sentence: `state = "hidden" if game.get_hidden() else "visible"`
    - Otherwise use a normal `if` block, e.g. when the values are real expressions (`parts[1].strip().lower() if len(parts) > 1 else ""`), ternaries are chained, or the ternary is inside an f-string or function call
    - JS/TS ternaries (`a ? b : c`) are fine
- Do small concise changes per "commit", don't do 4 things in 1 commit

# Workflow

- When a task needs several commits, work in chunks: finish one chunk (a fix plus its small follow-ups, or one feature end to end), format and test it, stage exactly its files with `git add`, then stop and let the user review and commit. Don't build everything first and suggest a split afterwards, and don't stop after every one-line change either.
- The user commits between turns. Check `git status` and `git log` before resetting, switching branches or amending.
- When the user asks for a tweak to a commit that was just made and isn't pushed, amend it instead of adding a "fix" commit.
- Never commit database backups (`storage_v2_*.sql`) or `backend/docker-compose.yml` (it holds the Discord token). Both are gitignored, keep it that way.

# Layout

- `backend/`: Python, FastAPI + peewee + PostgreSQL, plus the Discord bot. See `backend/README.md` for env variables, evolutions and restoring backups.
    - `tpbackend/main.py`: starts everything (API, Discord bot, Oblivionis sync)
    - `tpbackend/storage.py`: the database models
    - `tpbackend/operations.py`: shared logic. `add_session` is the single path for creating activities (API, live tracking, Oblivionis sync), with overlap checks
    - `tpbackend/api/`: public API routes. `tpbackend/admin/`: admin API routes (hidden from Swagger)
    - `tpbackend/discord/`: the bot. `tpbackend/oblivionis/`: syncs activity from the Oblivionis database
    - `evolutions/<n>.sql`: database migrations, applied in order at startup. To change the schema add the next number; never edit one that exists
    - `e2e/`: e2e tests against the API in docker
- `frontend/`: Vue 3 + TypeScript + Bootstrap 5 (+ Bootstrap Icons), built with Vite
    - `src/views/`: one component per page, routes in `src/router/index.ts`
    - `src/components/`: shared components, grouped by area (Games, Users, Admin, Recap...)
    - `src/api.client.ts` / `src/admin.client.ts`: API clients. `src/api.schema.d.ts` is generated from the backend's OpenAPI, don't edit it by hand

# Commands

Python lives in `.venv` at the repo root. direnv sets it up (`.envrc`); without direnv, run `export PATH="$PWD/.venv/bin:$PATH"` from the repo root first.

- Repo root: `make format` formats both backend and frontend
- `backend/`:
    - `make format` / `make format-check` (black)
    - `make test`: unit tests (`tpbackend/**/*_test.py`), no dependencies
    - `make e2e`: e2e tests, needs docker. `make e2e-up`, `pytest e2e`, `make e2e-down` to iterate
- `frontend/`:
    - `npm run format` / `npm run format-check` (prettier)
    - `npm run build`: type checks and builds
    - `npm run generate-schema`: regenerates `src/api.schema.d.ts` after API changes (needs the backend running on localhost:8000)

CI runs format-check, `make test`, `make e2e` and `npm run build`. If those pass locally, CI passes.

# Background

- The website is the interface for everything. Don't add Discord commands: only `!help`, `!token` (how users get the token they log in with on the website) and `!revoke_tokens` are left. The `AdminCommand` base class is kept on purpose for later, even though nothing uses it.
- `/admin` on the website is the only admin tool. Its most used part is the Covers tab, mostly used on a phone. IGDB ID 0 means "not on IGDB".
- User permissions are abuse switches, added after real misuse, so check them in the backend on every path, not just in the frontend:
    - `commands`: the remaining Discord commands
    - `manual_activity`: adding activity (manual tracking, API) and changing an activity's game or platform. Deleting your own activity needs no permission
    - `oblivionis_sync`: whether the user's Oblivionis activity is synced
- Public routes only let users change their own activity. Admins edit other users' through the admin routes.
- Activity data from 2025 is messy: manual backfills with hand-typed timestamps and duplicates. Overlap detection only exists since 2025-12-21. Odd rows from that time are usually manual entries, not bugs.
