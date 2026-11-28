import pytest

from tpbackend.common.colors import parse_color


class TestParseColor:
    def test_hash_and_case(self):
        assert parse_color(" #1A2B3C ") == "1a2b3c"

    def test_empty(self):
        assert parse_color(None) is None
        assert parse_color("") is None
        assert parse_color("#") is None

    def test_not_a_color(self):
        for color in ("red", "#12345", "1234567", "#gggggg"):
            with pytest.raises(ValueError):
                parse_color(color)
