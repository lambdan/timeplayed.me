import datetime
import xml.etree.ElementTree as ET

from tpbackend.storage import Activity

UTC = datetime.timezone.utc
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def sitemap_urls(api) -> dict[str, str | None]:
    """
    loc -> lastmod for every url in the sitemap
    """
    r = api.get("/sitemap.xml")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/xml")
    root = ET.fromstring(r.content)
    return {
        url.findtext("sm:loc", namespaces=NS): url.findtext("sm:lastmod", namespaces=NS)
        for url in root.findall("sm:url", NS)
    }  # type: ignore


class TestSitemap:
    def test_static_pages(self, api):
        urls = sitemap_urls(api)
        assert "http://timeplayed.test/" in urls
        assert "http://timeplayed.test/help" in urls
        # removed page
        assert "http://timeplayed.test/news" not in urls

    def test_pages_with_playtime(self, api, make_user, make_game, make_platform):
        user, _ = make_user()
        game = make_game()
        platform = make_platform()
        make_game("No playtime")
        Activity.create(
            user=user,
            game=game,
            platform=platform,
            seconds=3600,
            timestamp=datetime.datetime(2026, 3, 4, 12, 0, tzinfo=UTC),
        )

        urls = sitemap_urls(api)
        assert urls[f"http://timeplayed.test/game/{game.get_id()}"] == "2026-03-04"
        assert urls[f"http://timeplayed.test/user/{user.get_id()}"] == "2026-03-04"
        assert (
            urls[f"http://timeplayed.test/platform/{platform.get_id()}"] == "2026-03-04"
        )
        game_urls = [u for u in urls if "/game/" in u]
        assert game_urls == [f"http://timeplayed.test/game/{game.get_id()}"]

    def test_hidden_excluded(self, api, make_user, make_game, make_platform):
        user, _ = make_user()
        platform = make_platform()
        hidden_game = make_game("Hidden", hidden=True)
        hidden_parent = make_game("Hidden parent", hidden=True)
        child = make_game("Child", parent=hidden_parent)
        for game in (hidden_game, child):
            Activity.create(
                user=user,
                game=game,
                platform=platform,
                seconds=3600,
                timestamp=datetime.datetime.now(UTC),
            )
        Activity.create(
            user=user,
            game=make_game("Only hidden activity"),
            platform=platform,
            seconds=3600,
            timestamp=datetime.datetime.now(UTC),
            hidden=True,
        )

        urls = sitemap_urls(api)
        assert [u for u in urls if "/game/" in u] == []

    def test_nsfw_excluded(self, api, make_user, make_game, make_platform):
        user, _ = make_user()
        platform = make_platform()
        nsfw_parent = make_game("NSFW", nsfw=True)
        child = make_game("Child", parent=nsfw_parent)
        for game in (nsfw_parent, child):
            Activity.create(
                user=user,
                game=game,
                platform=platform,
                seconds=3600,
                timestamp=datetime.datetime.now(UTC),
            )

        urls = sitemap_urls(api)
        assert [u for u in urls if "/game/" in u] == []
