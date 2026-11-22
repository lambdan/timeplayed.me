Timeplayed is a service that tracks playtime. It originally only tracked through Discord (using Oblivionis), but nowadays can also do it through an API.

# Rules

- Code should always be formatted (see Commands below)
- All tests should always pass
- Any new feature should have a test added if possible
- For every change, ask what happens to existing data and existing users (rows already in prod, stored permission arrays, API clients). New defaults only apply to new rows, so existing ones may need an evolution. Tests that only create fresh users won't catch this
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
- API routes should be intuitive and easy to use from code: a plain resource route returns JSON of what's there, and sub-resources get their own path instead of query flags
    - Example: `GET /game/{id}/cover` lists the cover's source, credits and versions; `GET /game/{id}/cover/{version}` redirects to that image, so it can go straight into an `<img src>`

# Git rules/workflow

- Never commit database backups (`storage_v2_*.sql`) or `backend/docker-compose.yml` (it holds the Discord token). Both are gitignored, keep it that way.
- Never push, tag or make releases (`make release`, `make-release.sh`). The user does that
- Commit messages start with the area, then what was done: `frontend: show child platforms on the platform page`, `backend: ...`, `e2e: ...`
- You may commit when all of these hold:
    - Formatting passes and all tests pass
    - The change does exactly what was asked, nothing more
    - It involved no judgment calls the user hasn't seen (design choices, behavior changes, schema changes, anything you'd want to ask about)
    - Otherwise only stage the edits and ask the user for approval
- The user commits between turns sometimes. Check `git status` and `git log` before resetting, switching branches or amending.
- When a task needs several commits, work in chunks: finish one chunk (a fix plus its small follow-ups, or one feature end to end), format and test it, stage exactly its files with `git add`, then commit it or stop for review, per the rule above. Don't build everything first and suggest a split afterwards, and don't stop after every one-line change either.
- When the user asks for a tweak to a commit that was just made and isn't pushed, amend it instead of adding a "fix" commit.

# Workflow

- Keep `NOTES.md` at the repo root up to date, so several agents (some with small context windows) can hand work over to each other. It's gitignored, don't commit it.
    - Read it before starting work. Create it if it's missing
    - Update it whenever you finish a chunk, make a decision, or stop partway
    - Always rewrite the whole file, never append to it. It has exactly these sections, each once, in this order:
        - `## Current task`: what is being worked on, and what's done so far
        - `## Decisions`: decisions for the current task, and why
        - `## Next`: the next steps
        - `## Gotchas`: surprises found along the way that the next agent should know
    - Don't track what git already knows (uncommitted files, recent commits). Run `git status` and `git log` instead
    - Keep it short and current: point to files (`path:line`) instead of pasting code, and remove things that are finished and committed. Anything that stays true for the whole project belongs in this file instead
    - Never write secrets (tokens, `backend/docker-compose.yml` contents) or prod user data in it

# Layout

- `backend/`: Python, FastAPI + peewee + PostgreSQL, plus the Discord bot. See `backend/README.md` for env variables, evolutions and restoring backups.
    - `tpbackend/main.py`: starts everything (API, Discord bot, Oblivionis sync)
    - `tpbackend/storage.py`: the database models
    - `tpbackend/operations.py`: shared logic. `add_session` is the single path for creating activities (API, live tracking, Oblivionis sync), with overlap checks
    - `tpbackend/api/`: public API routes. `tpbackend/admin/`: admin API routes (hidden from Swagger)
    - `tpbackend/discord/`: the bot. `tpbackend/oblivionis/`: syncs activity from the Oblivionis database
    - `evolutions/<n>.sql`: database migrations, applied in order at startup. To change the schema add the next number; never edit one that has been released (run in prod). Ones that aren't released yet can be edited or squashed, then restore a backup into the dev environment (see Commands) so they're applied again from the released state
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
        - Docker Desktop on macOS hides file ownership, so anything shared on disk between the e2e containers and the tests can pass locally and fail on Linux in CI. Prefer sharing through the database
    - `make dev`: the dev environment (formats, runs unit tests, builds the image, `docker compose up -d` with `backend/docker-compose.yml`, follows the logs). Postgres data is in `backend/psql_volume`
        - Since it never exits, agents run it as a background task. It needs the venv on PATH (`black`), so without direnv: `PATH="$PWD/../.venv/bin:$PATH" make dev` from `backend/`
        - It's up within seconds. Check the log for "Database is up to date" instead of writing wait loops
        - The dev environment is disposable: do whatever you need in it (reset data, run write requests, apply evolutions). A prod backup restores it (below)
    - Restoring a prod backup into the dev environment (`backend/storage_v2_*.sql`, newest by date in the name), with the dev compose down:
        1. `docker compose up -d postgres --wait`, copy the backup into the container with `docker cp`
        2. In the container, as `$POSTGRES_USER`: `DROP DATABASE IF EXISTS storage_v2 WITH (FORCE)`, `CREATE DATABASE storage_v2 OWNER "$POSTGRES_USER"`, then `psql -d storage_v2 -f <backup>`
        3. `docker compose down`. The next `make dev` applies the newer evolutions
- `frontend/`:
    - `npm run format` / `npm run format-check` (prettier)
    - `npm run build`: type checks and builds
    - `npm run generate-schema`: regenerates `src/api.schema.d.ts` after API changes (needs the backend running on localhost:8000). Or against the e2e backend, after `make e2e-up`: `npx openapi-typescript http://localhost:58000/openapi.json -o src/api.schema.d.ts`, then `npm run format`

CI runs format-check, `make test`, `make e2e` and `npm run build`. If those pass locally, CI passes.

# Background

- The website is the interface for everything. Don't add Discord commands: only `!help`, `!token` (how users get the token they log in with on the website) and `!revoke_tokens` are left. The `AdminCommand` base class is kept on purpose for later, even though nothing uses it.
- The bot never posts in the Discord server's channels; they stay completely silent. All of its communication is through DMs with a single user. Never add code that sends anything to a channel (announcements, notifications, error reports, replies), not even behind a flag.
- `/admin` on the website is the only admin tool. Its most used part is the Covers tab, mostly used on a phone. IGDB ID 0 means "not on IGDB".
- User permissions are abuse switches, added after real misuse, so check them in the backend on every path, not just in the frontend:
    - `commands`: the remaining Discord commands
    - `manual_activity`: adding activity (manual tracking, API) and changing an activity's game or platform. Deleting your own activity needs no permission
    - `oblivionis_sync`: whether the user's Oblivionis activity is synced
- Public routes only let users change their own activity. Admins edit other users' through the admin routes.
- NSFW is decided in the frontend: the backend gives NSFW names and covers to everyone, and `useNsfw` hides them from viewers who haven't opted in (the `show_nsfw` permission, set in settings). Names are jumbled, covers stay on the blurred preview
- The backend is one process, but sync routes run in a thread pool, so shared things (like the IGDB client) must be thread-safe. For "only do this once" work (like fetching a cover), use `KeyedLock` (`tpbackend/keyed_lock.py`): a unique constraint alone still lets every request do the work before one insert wins
- Activity data from 2025 is messy: manual backfills with hand-typed timestamps and duplicates. Overlap detection only exists since 2025-12-21. Odd rows from that time are usually manual entries, not bugs.
