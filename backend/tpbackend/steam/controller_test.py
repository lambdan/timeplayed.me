from tpbackend.steam.controller import cover_url_from_item


class TestCoverUrlFromItem:
    def test_hashed_path(self):
        # what GetItems returns for a newer app (Duskfade)
        item = {
            "appid": 2542020,
            "assets": {
                "asset_url_format": "steam/apps/2542020/${FILENAME}?t=1786631734",
                "library_capsule": "011f0de80670493c386a324312105f286f204cff/library_capsule.jpg",
            },
        }
        assert (
            cover_url_from_item(item)
            == "https://shared.steamstatic.com/store_item_assets/steam/apps/2542020/011f0de80670493c386a324312105f286f204cff/library_capsule.jpg?t=1786631734"
        )

    def test_plain_path(self):
        # older apps (Counter-Strike 2)
        item = {
            "appid": 730,
            "assets": {
                "asset_url_format": "steam/apps/730/${FILENAME}?t=1793054556",
                "library_capsule": "library_600x900.jpg",
            },
        }
        assert (
            cover_url_from_item(item)
            == "https://shared.steamstatic.com/store_item_assets/steam/apps/730/library_600x900.jpg?t=1793054556"
        )

    def test_without_library_capsule(self):
        item = {"appid": 1, "assets": {"asset_url_format": "steam/apps/1/${FILENAME}"}}
        assert cover_url_from_item(item) is None

    def test_unknown_app(self):
        assert cover_url_from_item({}) is None
