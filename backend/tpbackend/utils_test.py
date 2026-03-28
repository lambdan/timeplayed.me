"""Tests for tpbackend.utils."""

import datetime
import pytest
from unittest.mock import patch
import tpbackend.utils as utils


class TestNow:
    def test_is_utc_and_current(self):
        delta = abs((utils.now() - datetime.datetime.now(datetime.UTC)).total_seconds())
        assert delta < 0.1


class TestDatetimeParse:
    def test_absolute_js_format(self):
        result = utils.datetimeParse("2023-10-01T12:00:00Z")
        assert result == datetime.datetime(2023, 10, 1, 12, 0, tzinfo=datetime.UTC)

    @pytest.mark.parametrize(
        "s, delta",
        [
            ("-1h30m5s", datetime.timedelta(hours=1, minutes=30, seconds=5)),
            ("-666s", datetime.timedelta(seconds=666)),
            ("-666h", datetime.timedelta(hours=666)),
            ("-666m", datetime.timedelta(minutes=666)),
            ("-666m666s", datetime.timedelta(minutes=666, seconds=666)),
            ("-666h666s", datetime.timedelta(hours=666, seconds=666)),
            ("-666h666m", datetime.timedelta(hours=666, minutes=666)),
            ("-00:01:01", datetime.timedelta(minutes=1, seconds=1)),
            ("-01:01:01", datetime.timedelta(hours=1, minutes=1, seconds=1)),
            ("-00:00:01", datetime.timedelta(seconds=1)),
        ],
    )
    def test_relative(self, s, delta):
        result = utils.datetimeParse(s)
        expected = datetime.datetime.now(datetime.UTC) - delta
        assert abs((result - expected).total_seconds()) < 0.1


class TestSecsToHHMMSS:
    @pytest.mark.parametrize(
        "secs, expected",
        [
            (0, "00:00:00"),
            (1, "00:00:01"),
            (60, "00:01:00"),
            (3600, "01:00:00"),
            (3661, "01:01:01"),
            (86400, "24:00:00"),
            (-1, "00:00:00"),
            (-3600, "00:00:00"),
        ],
    )
    def test_conversion(self, secs, expected):
        assert utils.secsToHHMMSS(secs) == expected


class TestSecsFromString:
    @pytest.mark.parametrize(
        "s, expected",
        [
            ("01:30:45", 5445),
            ("00:00:00", 0),
            ("01:00:00", 3600),
            ("00:01:00", 60),
            ("00:00:01", 1),
            ("1h30m45s", 5445),
            ("1h30m", 5400),
            ("1h", 3600),
            ("30m", 1800),
            ("45s", 45),
        ],
    )
    def test_parse(self, s, expected):
        assert utils.secsFromString(s) == expected


class TestParseRange:
    @pytest.mark.parametrize(
        "s, expected",
        [
            ("1-10", (1, 10)),
            ("5-15", (5, 15)),
            ("100-200", (100, 200)),
            ("0-0", (0, 0)),
            ("1-1", (1, 1)),
            ("1-10-20", None),
            ("10", None),
            ("1-", None),
            ("-1-", None),
            ("-1", None),
        ],
    )
    def test_parse(self, s, expected):
        assert utils.parseRange(s) == expected


class TestNormalizeQuotes:
    @pytest.mark.parametrize(
        "s, expected",
        [
            ('Hello "World"', 'Hello "World"'),
            ("Hello \u201cWorld\u201d", 'Hello "World"'),
            ("It's a test", "It's a test"),
            ("\u2018Hello\u2019", "'Hello'"),
            ("`Hello`", "'Hello'"),
            ("\u00b4Hello\u00b4", "'Hello'"),
        ],
    )
    def test_normalize(self, s, expected):
        assert utils.normalizeQuotes(s) == expected


class TestValidateDate:
    def test_valid_date(self):
        assert (
            utils.validateDate(datetime.datetime(2025, 1, 20, tzinfo=datetime.UTC))
            == "OK"
        )

    def test_before_launch_date_is_invalid(self):
        result = utils.validateDate(datetime.datetime(2025, 1, 19, tzinfo=datetime.UTC))
        assert result != "OK"

    def test_now_is_valid(self):
        assert utils.validateDate(utils.now()) == "OK"

    def test_ancient_date_is_invalid(self):
        result = utils.validateDate(datetime.datetime(1969, 1, 19, tzinfo=datetime.UTC))
        assert result != "OK"


# class TestGameName:
#    def test_no_year(self, make_game):
#        game = make_game(name="wow")
#        assert utils.game_name(game) == "wow"
#
#    def test_with_year(self, make_game):
#        game = make_game(name="wow")
#        game.release_year = 2004
#        assert utils.game_name(game) == "wow (2004)"
#
#    def test_with_url(self, make_game):
#        game = make_game(name="wow", id=123)
#        game.release_year = 2004
#        with patch("tpbackend.utils.TIMEPLAYED_URL", "http://example.com"):
#            result = utils.game_name(game, as_markdown_link=True)
#        assert result == "[wow (2004)](http://example.com/game/123)"
#
#
# class TestActivityName:
#    def test_basic_name(self, make_activity):
#        activity = make_activity(id=456)
#        assert utils.activity_name(activity) == "Activity 456"
#
#    def test_with_url(self, make_activity):
#        activity = make_activity(id=456)
#        with patch("tpbackend.utils.TIMEPLAYED_URL", "http://example.com"):
#            result = utils.activity_name(activity, as_markdown_link=True)
#        assert result == "[Activity 456](http://example.com/activity/456)"


class TestQueryNormalize:
    def test_strip_and_lower(self):
        assert utils.query_normalize("  Hello World  ") == "hello world"

    def test_replace_nbsp(self):
        assert utils.query_normalize("Hello\u00a0World") == "hello world"
        assert utils.query_normalize("Hello World") == "hello world"

    def test_remove_extra_spaces(self):
        assert utils.query_normalize("Hello   World") == "hello world"

    def test_empty_string(self):
        assert utils.query_normalize("   ") == ""

    def test_pokemon(self):
        assert utils.query_normalize("Pokémon") == "pokemon"
