import datetime

from tpbackend.permissions import DEFAULT_PERMISSIONS, Permission
from tpbackend.storage import Activity

UTC = datetime.timezone.utc


def add_activity(user, game, platform, seconds=3600):
    Activity.create(
        user=user,
        game=game,
        platform=platform,
        seconds=seconds,
        timestamp=datetime.datetime.now(UTC),
    )


class TestHead:
    def test_game(self, api, make_user, make_game, make_platform):
        user, _ = make_user()
        game = make_game("Escape from Tarkov", release_year=2017)
        add_activity(user, game, make_platform(), seconds=7200)

        r = api.get(f"/head/game/{game.get_id()}")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/html")
        assert (
            "<title>Escape from Tarkov (2017) playtime - Timeplayed.me</title>"
            in r.text
        )
        assert (
            '<meta name="description" content="Escape from Tarkov (2017): '
            "2.0 hours played by 1 player." in r.text
        )
        assert (
            f'<link rel="canonical" href="http://timeplayed.test/game/{game.get_id()}" />'
            in r.text
        )
        assert '<meta property="og:title"' in r.text

    def test_game_indexed(self, api, make_game):
        r = api.get(f"/head/game/{make_game().get_id()}")
        assert "noindex" not in r.text

    def test_nsfw_game_noindex(self, api, make_game):
        parent = make_game("Some Juicy Title", nsfw=True)
        child = make_game("Child", parent=parent)
        for game in (parent, child):
            r = api.get(f"/head/game/{game.get_id()}")
            assert '<meta name="robots" content="noindex" />' in r.text
            # the title isn't censored, only the site does that
            assert "Some Juicy Title" in r.text or "Child" in r.text

    def test_game_includes_children(self, api, make_user, make_game, make_platform):
        user, _ = make_user()
        platform = make_platform()
        game = make_game("GTA V")
        add_activity(user, game, platform, seconds=3600)
        add_activity(user, make_game("FiveM", parent=game), platform, seconds=3600)

        r = api.get(f"/head/game/{game.get_id()}")
        assert "GTA V: 2.0 hours played by 1 player." in r.text

    def test_user(self, api, make_user, make_game, make_platform):
        user, _ = make_user(name="alice", display_name="Alice")
        add_activity(user, make_game(), make_platform(), seconds=600)

        r = api.get(f"/head/user/{user.get_id()}")
        assert "<title>Alice playtime - Timeplayed.me</title>" in r.text
        assert "Alice: 10 minutes played across 1 game." in r.text

    def test_user_name_hidden(self, api, make_user):
        user, _ = make_user(
            name="secret",
            display_name="Secret",
            permissions=[*DEFAULT_PERMISSIONS, Permission.ANONYMOUS],
        )
        r = api.get(f"/head/user/{user.get_id()}")
        assert f"<title>User {user.get_id()} playtime - Timeplayed.me</title>" in r.text
        assert "Secret" not in r.text

    def test_private_user(self, api, make_user, make_game, make_platform):
        user, _ = make_user(
            name="secret", permissions=[*DEFAULT_PERMISSIONS, Permission.PRIVATE]
        )
        add_activity(user, make_game(), make_platform())
        r = api.get(f"/head/user/{user.get_id()}")
        assert "secret" not in r.text
        assert "Private" not in r.text

    def test_platform(self, api, make_user, make_game, make_platform):
        user, _ = make_user()
        platform = make_platform("ps5", name="PlayStation 5")
        add_activity(user, make_game("A"), platform)
        add_activity(user, make_game("B"), platform)

        r = api.get(f"/head/platform/{platform.get_id()}")
        assert "<title>PlayStation 5 playtime - Timeplayed.me</title>" in r.text
        assert "played across 2 games by 1 player." in r.text

    def test_escapes_html(self, api, make_game):
        game = make_game('<script>"x"</script>')
        r = api.get(f"/head/game/{game.get_id()}")
        assert "<script>" not in r.text
        assert "&lt;script&gt;&quot;x&quot;&lt;/script&gt;" in r.text

    def test_empty_for_defaults(self, api, make_game):
        hidden = make_game("Hidden", hidden=True)
        child_of_hidden = make_game("Child", parent=hidden)
        for path in [
            "",
            "help",
            "game/999",
            "game/abc",
            "game/²",
            "game/99999999999999999999",
            f"game/{hidden.get_id()}",
            f"game/{child_of_hidden.get_id()}",
            "user/999",
            "platform/999",
            "user/1/recap/2025",
        ]:
            r = api.get(f"/head/{path}")
            assert r.status_code == 200, path
            assert r.text == "", path
