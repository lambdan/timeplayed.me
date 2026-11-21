import json

from tpbackend.igdb import controller


def game(igdb_id: int, name: str) -> dict:
    return {"id": igdb_id, "name": name, "url": f"https://www.igdb.com/games/{igdb_id}"}


class FakeIGDB:
    """IGDB with game 1942 (The Witcher 3) and games named 1942, records the queries"""

    def __init__(self):
        self.queries: list[str] = []

    def request(self, url: str, query: str):
        self.queries.append(query)
        if "where id = 1942" in query:
            return json.dumps([game(1942, "The Witcher 3")])
        if 'search "1942"' in query:
            return json.dumps([game(6075, "1942"), game(1942, "The Witcher 3")])
        return json.dumps([])


class TestSearchGame:
    def test_by_name(self, monkeypatch):
        fake = FakeIGDB()
        monkeypatch.setattr(controller, "igdb", fake)
        assert controller.search_game("zelda") == []
        # not looked up by id
        assert len(fake.queries) == 1

    def test_number_is_an_id_and_a_name(self, monkeypatch):
        monkeypatch.setattr(controller, "igdb", FakeIGDB())
        results = controller.search_game(" 1942 ")
        # the game with the id first, and only once
        assert [r.id for r in results] == [1942, 6075]

    def test_quotes_are_removed(self, monkeypatch):
        fake = FakeIGDB()
        monkeypatch.setattr(controller, "igdb", fake)
        controller.search_game('say "hi"')
        assert fake.queries == [
            f'search "say hi"; {controller.SEARCH_FIELDS} limit 10;'
        ]
