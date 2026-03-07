# Testing guide

## Running the tests

From the `backend/` directory:

```sh
python3 -m pytest          # run all tests
python3 -m pytest -v       # verbose output (shows each test name)
python3 -m pytest tpbackend/cmds/search_games_test.py   # single file
```

Tests are also run automatically by CI on every push to `master` and on every
pull request (see `.github/workflows/test.yml`).

---

## Repository layout

```
backend/
├── conftest.py                        # shared fixtures — read this first
├── pytest.ini                         # pytest configuration
├── TESTING.md                         # this file
└── tpbackend/
    ├── utils_test.py                  # tests for tpbackend/utils.py
    └── cmds/
        ├── search_games_test.py       # example / reference test file
        └── <command>_test.py          # add one file per command here
```

---

## How tests work without a real database

The `conftest.py` file does two things before any test module is imported:

1. **Sets fake environment variables** (`DB_NAME_TIMEPLAYED`, `DB_USER`, …) so
   Peewee initialises without a live PostgreSQL connection.
2. **Replaces `tpbackend.bot` and `tpbackend.api`** in `sys.modules` with
   `MagicMock` objects so the Discord client and the REST API are never
   actually started.

All fixtures defined in `conftest.py` are automatically available to every
test file — no import needed.

---

## Available fixtures

| Fixture | What it returns |
|---|---|
| `make_user(...)` | Factory — call it to get a mock `User` |
| `make_game(...)` | Factory — call it to get a mock `Game` |
| `make_platform(...)` | Factory — call it to get a mock `Platform` |
| `make_activity(...)` | Factory — call it to get a mock `Activity` |
| `make_live_activity(...)` | Factory — call it to get a mock `LiveActivity` |
| `make_activity_queryset(list)` | Wraps a list in a mock Peewee queryset |
| `make_admin_user()` | Factory — returns a user whose id is in `ADMINS` |
| `mock_api` | The `MagicMock` that replaced `tpbackend.api` |

Every factory returns a `MagicMock` pre-configured with realistic attributes.
You can override any attribute after creation, e.g. `act.seconds = 999`.

---

## Writing a new command test

1. Create `tpbackend/cmds/<command>_test.py`.
2. Import the command class and any Peewee models you need to patch.
3. Use `patch.object(Model, "method", return_value=...)` to control database
   calls, and `patch("tpbackend.cmds.<module>.<function>", ...)` for module-
   level helpers.
4. Call `cmd.execute(user, args)` and assert on the returned string.

### Minimal template

```python
"""Tests for MyCommand (!mycommand)."""

from unittest.mock import patch

import pytest

from tpbackend.cmds.my_command import MyCommand
from tpbackend.storage.storage_v2 import Game  # import models you need


@pytest.fixture
def cmd():
    return MyCommand()


def test_happy_path(cmd, make_user, make_game):
    game = make_game(1, "Hollow Knight")
    with patch.object(Game, "get_or_none", return_value=game):
        result = cmd.execute(make_user(), "1")
    assert "Hollow Knight" in result


def test_not_found(cmd, make_user):
    with patch.object(Game, "get_or_none", return_value=None):
        result = cmd.execute(make_user(), "999")
    assert "Error" in result
```

### Patching tips

- Patch **where the name is used**, not where it is defined.
  If `my_command.py` does `from tpbackend.storage.storage_v2 import search_games`,
  patch `"tpbackend.cmds.my_command.search_games"`, not
  `"tpbackend.storage.storage_v2.search_games"`.
- Use `patch.object(Model, "class_method")` for Peewee model methods such as
  `get_or_none`, `select`, `create`, `get_or_create`, `get_by_id`.
- Use `side_effect=[val1, val2]` when the same mock is called multiple times
  with different return values (e.g. deleting several activities by id).

### Admin commands

Admin commands check `os.environ["ADMINS"]`. `conftest.py` sets that to
`"admin123"`, and `make_admin_user()` returns a user with `id="admin123"`, so
the admin check passes automatically.

---

## Formatting

All Python files in `backend/` must be formatted with
[black](https://black.readthedocs.io/).  Run the formatter before committing:

```sh
cd backend
./format.sh
```

CI will fail if any file is not formatted correctly.
