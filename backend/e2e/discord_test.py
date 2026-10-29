"""
Discord isn't running in the e2e env, but the DM handler can be called directly
"""

import logging
import re
from dataclasses import dataclass, field

from conftest import Api
from tpbackend.discord.bot import dm_receive
from tpbackend.storage import DiscordHistory


@dataclass
class FakeAuthor:
    id: int = 1234
    name: str = "discordguy"
    display_name: str = "Discord Guy"


@dataclass
class FakeMessage:
    content: str
    author: FakeAuthor = field(default_factory=FakeAuthor)


class TestSensitiveReplies:
    def test_token_is_not_logged_or_stored(self, caplog):
        with caplog.at_level(logging.INFO):
            reply = dm_receive(FakeMessage("!token"))  # type: ignore

        assert reply is not None
        match = re.search(r"```(.+)```", reply)
        assert match, reply
        token = match.group(1)

        # user gets a working token
        r = Api(token).get("/who_am_i")
        assert r.status_code == 200
        assert r.json()["discord_id"] == "1234"

        # ...that nobody else gets to see
        assert token not in caplog.text
        assert "<REPLY> <redacted>" in caplog.text
        stored = [h.message for h in DiscordHistory.select()]
        assert "<redacted>" in stored
        assert not any(token in m for m in stored)

    def test_regular_reply_is_stored(self):
        reply = dm_receive(FakeMessage("!uptime"))  # type: ignore
        assert reply
        stored = [h.message for h in DiscordHistory.select()]
        assert reply in stored
