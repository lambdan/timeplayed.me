from tpbackend.igdb.models import IGDB_SearchResult


class TestSearchResult:
    def test_with_cover(self):
        # what igdb returns for `fields ...,cover.image_id`
        r = IGDB_SearchResult.model_validate(
            {
                "id": 732,
                "name": "Grand Theft Auto: San Andreas",
                "url": "https://www.igdb.com/games/grand-theft-auto-san-andreas",
                "cover": {"id": 123, "image_id": "co2lb9"},
            }
        )
        assert r.cover and r.cover.image_id == "co2lb9"

    def test_without_cover(self):
        r = IGDB_SearchResult.model_validate(
            {"id": 1, "name": "No cover", "url": "https://www.igdb.com/games/x"}
        )
        assert r.cover is None
