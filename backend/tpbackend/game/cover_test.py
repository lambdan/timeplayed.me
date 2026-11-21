import threading
import time

import pytest

from tpbackend.game import cover
from tpbackend.igdb.models import IGDB_Cover, IGDB_GameInfo
from tpbackend.storage import Game, GameCover

IGDB_IMAGE = "https://images.igdb.com/igdb/image/upload/t_cover_big/co2lb9.jpg"


class FakeImage:
    def __init__(self, id: str, source: str | None = None):
        self.id = id
        self.source = source

    def get_id(self) -> str:
        return self.id

    def get_source(self) -> str | None:
        return self.source


ALL_VERSIONS = {
    "display": FakeImage("display"),
    "thumbnail": FakeImage("thumbnail"),
    "preview": FakeImage("preview"),
}


class FakeRow:
    """a game_cover row"""

    def __init__(self, source: str, image=None, igdb_id=None):
        self.source = source
        self.image = image or FakeImage("original", IGDB_IMAGE)
        self.igdb_id = igdb_id

    def get_source(self) -> str:
        return self.source

    def get_image(self):
        return self.image

    def get_igdb_id(self):
        return self.igdb_id


class Fakes:
    """
    the game_cover rows by game name, and IGDB: ids over 100 have a cover.
    records what was asked from IGDB and saved
    """

    def __init__(self, monkeypatch):
        self.rows: dict[str, FakeRow] = {}
        self.fetched: list[int] = []
        self.saved: list[tuple[str, int]] = []
        monkeypatch.setattr(cover, "cover_row", lambda game: self.rows.get(game.name))
        monkeypatch.setattr(cover, "fetch_igdb_cover", self.fetch_igdb_cover)
        monkeypatch.setattr(cover, "save_igdb_cover", self.save_igdb_cover)
        monkeypatch.setattr(cover, "get_versions", lambda image: ALL_VERSIONS)

    def fetch_igdb_cover(self, igdb_id: int):
        self.fetched.append(igdb_id)
        if igdb_id > 100:
            return (
                FakeImage("original", IGDB_IMAGE),
                f"https://www.igdb.com/games/{igdb_id}",
            )
        return None

    def save_igdb_cover(self, game, igdb_id, image, igdb_url):
        self.saved.append((game.name, igdb_id))


@pytest.fixture
def fakes(monkeypatch) -> Fakes:
    return Fakes(monkeypatch)


class TestFindCover:
    def test_nothing(self, fakes):
        assert cover.find_cover(Game(name="A")).source == "None"
        assert fakes.fetched == []

    def test_disabled_wins(self, fakes):
        fakes.rows["A"] = FakeRow(GameCover.UPLOAD)
        game = Game(name="A", cover_disabled=True, igdb_id=123)
        assert cover.find_cover(game).source == "Disabled"
        assert fakes.fetched == []

    def test_uploaded_before_igdb(self, fakes):
        fakes.rows["A"] = FakeRow(GameCover.UPLOAD)
        result = cover.find_cover(Game(name="A", igdb_id=123))
        assert result.source == "Uploaded"
        assert result.versions["original"] is fakes.rows["A"].image
        assert result.versions["display"] is ALL_VERSIONS["display"]
        assert result.credits is None
        assert fakes.fetched == []

    def test_uploaded_gone_falls_through(self, fakes, monkeypatch):
        fakes.rows["A"] = FakeRow(GameCover.UPLOAD, image=FakeImage("gone"))
        monkeypatch.setattr(
            cover,
            "get_versions",
            lambda image: {} if image.id == "gone" else ALL_VERSIONS,
        )
        assert cover.find_cover(Game(name="A", igdb_id=123)).source == "IGDB"

    def test_igdb_first_time(self, fakes):
        result = cover.find_cover(Game(name="A", igdb_id=123))
        assert result.source == "IGDB"
        assert result.versions.keys() == {"original", *ALL_VERSIONS}
        assert result.credits == "IGDB cover image ID: co2lb9"
        assert fakes.fetched == [123]
        assert fakes.saved == [("A", 123)]

    def test_igdb_stored(self, fakes):
        fakes.rows["A"] = FakeRow(GameCover.IGDB, igdb_id=123)
        result = cover.find_cover(Game(name="A", igdb_id=123))
        assert result.source == "IGDB"
        # IGDB isn't asked again
        assert fakes.fetched == []
        assert fakes.saved == []

    def test_igdb_asked_once_at_the_same_time(self, fakes, monkeypatch):
        fetch = fakes.fetch_igdb_cover

        def slow_fetch(igdb_id):
            time.sleep(0.02)
            return fetch(igdb_id)

        def save(game, igdb_id, image, igdb_url):
            fakes.saved.append((game.name, igdb_id))
            fakes.rows[game.name] = FakeRow(GameCover.IGDB, image, igdb_id=igdb_id)

        monkeypatch.setattr(cover, "fetch_igdb_cover", slow_fetch)
        monkeypatch.setattr(cover, "save_igdb_cover", save)
        game = Game(id=1, name="A", igdb_id=123)
        threads = [
            threading.Thread(target=cover.find_cover, args=(game,)) for _ in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert fakes.fetched == [123]
        assert fakes.saved == [("A", 123)]

    def test_igdb_id_changed(self, fakes):
        fakes.rows["A"] = FakeRow(GameCover.IGDB, igdb_id=123)
        cover.find_cover(Game(name="A", igdb_id=456))
        assert fakes.fetched == [456]
        assert fakes.saved == [("A", 456)]

    def test_no_cover_on_igdb(self, fakes):
        assert cover.find_cover(Game(name="A", igdb_id=1)).source == "None"
        assert fakes.saved == []

    def test_igdb_id_0_is_skipped(self, fakes):
        # 0 means "not on IGDB"
        assert cover.find_cover(Game(name="A", igdb_id=0)).source == "None"
        assert fakes.fetched == []

    def test_parent(self, fakes):
        parent = Game(name="Parent", igdb_id=123)
        # IGDB has no cover for the child
        child = Game(name="Child", parent=parent, igdb_id=1)
        assert cover.find_cover(child).source == "IGDB"
        assert fakes.fetched == [1, 123]
        assert fakes.saved == [("Parent", 123)]

    def test_parent_uploaded(self, fakes):
        fakes.rows["Parent"] = FakeRow(GameCover.UPLOAD)
        child = Game(name="Child", parent=Game(name="Parent"))
        assert cover.find_cover(child).source == "Uploaded"

    def test_parent_disabled(self, fakes):
        child = Game(name="Child", parent=Game(name="Parent", cover_disabled=True))
        assert cover.find_cover(child).source == "Disabled"


class TestFetchIGDBCover:
    @pytest.fixture
    def downloads(self, monkeypatch) -> list[str]:
        urls: list[str] = []

        def get_image(url):
            urls.append(url)
            return FakeImage("original", url)

        monkeypatch.setattr(cover, "get_image", get_image)
        return urls

    def test_stores_the_cover(self, downloads, monkeypatch):
        info = IGDB_GameInfo(
            id=123,
            name="X",
            url="https://www.igdb.com/games/x",
            cover=IGDB_Cover(id=1, image_id="co2lb9"),
        )
        monkeypatch.setattr(cover.igdb, "get_cover_info", lambda igdb_id: info)
        image, igdb_url = cover.fetch_igdb_cover(123)
        assert image.get_source() == IGDB_IMAGE
        assert igdb_url == "https://www.igdb.com/games/x"
        assert downloads == [IGDB_IMAGE]

    def test_no_cover_on_igdb(self, downloads, monkeypatch):
        info = IGDB_GameInfo(id=123, name="X", url="https://www.igdb.com/games/x")
        monkeypatch.setattr(cover.igdb, "get_cover_info", lambda igdb_id: info)
        assert cover.fetch_igdb_cover(123) is None
        assert downloads == []
