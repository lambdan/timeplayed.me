import tpbackend.api.head as head


class TestParseId:
    def test_valid(self):
        assert head.parse_id("123") == 123
        assert head.parse_id(str(head.MAX_ID)) == head.MAX_ID

    def test_invalid(self):
        for value in ["", "abc", "-1", "1.5", "²", "٣", str(head.MAX_ID + 1)]:
            assert head.parse_id(value) is None, value


class TestHeadTags:
    def test_url_tags_when_url_set(self, monkeypatch):
        monkeypatch.setenv("TIMEPLAYED_URL", "https://timeplayed.me")
        tags = head.head_tags("Game", "Desc", "https://timeplayed.me/game/1")
        assert '<link rel="canonical" href="https://timeplayed.me/game/1" />' in tags
        assert '<meta property="og:url"' in tags

    def test_no_url_tags_when_url_not_set(self, monkeypatch):
        monkeypatch.delenv("TIMEPLAYED_URL", raising=False)
        tags = head.head_tags("Game", "Desc", "http://localhost/game/1")
        assert "<title>Game - Timeplayed.me</title>" in tags
        assert "canonical" not in tags
        assert "og:url" not in tags


class TestFormatPlaytime:
    def test_formats(self):
        assert head.format_playtime(7200) == "2.0 hours"
        assert head.format_playtime(600) == "10 minutes"
        assert head.format_playtime(60) == "1 minute"
        assert head.format_playtime(30) == "30 seconds"
