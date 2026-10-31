Timeplayed is a service that tracks playtime. It originally only tracked through Discord (using Oblivionis), but nowadays can also do it through an API.

# Rules

- Never commit automatically
- Code should always be formatted (see `make format`)
- All tests should always pass
- Any new feature should have a test added if possible
- Never make any write requests to production without permission (reads are OK)
- Don't be cute. Timeplayed primary function is numbers and statistics. Think last.fm, but for playtime. 
    - As an example, if you're making a "top played games" list, don't put in any "What kept you busy" paragraph. Just put a title (Top played games) and list the games!
- Avoid custom CSS as much as possible. We don't want to maintain that. Just use plain HTML or Bootstrap or whatever framework we use has to offer. 
- The site is primarily developed for desktop usage. However, it should still be browsable and have no layout issues on mobile.
    - Especially the manual tracking page has to work good on mobile, as that is primarily where it will most likely be used
- In general, try to show as much info as possible, if it makes sense:
    - Eg, on a game page, its redundant to show game cover and game name in the activity rows, because it will be at the top of the page. But on the front page or platform page, we should show game cover/name if there's room for it, as it won't be anywhere else on the page.
    - On mobile (small screens) remove less important stuff
- Always prefer readable, maintainable code over fancy code
    - Python ternaries (`x if cond else y`) are OK when both values are simple and the condition is short, so it reads like a sentence: `state = "hidden" if game.get_hidden() else "visible"`
    - Otherwise use a normal `if` block, e.g. when the values are real expressions (`parts[1].strip().lower() if len(parts) > 1 else ""`), ternaries are chained, or the ternary is inside an f-string or function call
    - JS/TS ternaries (`a ? b : c`) are fine
- Do small concise changes per "commit", don't do 4 things in 1 commit