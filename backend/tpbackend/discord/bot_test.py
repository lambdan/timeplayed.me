import asyncio
from unittest.mock import AsyncMock, MagicMock

from discord.errors import Forbidden

from tpbackend.discord.bot import channel_command, point_to_dms


def forbidden() -> Forbidden:
    return Forbidden(MagicMock(status=403, reason="Forbidden"), "nope")


def message() -> MagicMock:
    msg = MagicMock()
    msg.add_reaction = AsyncMock()
    msg.author.send = AsyncMock()
    return msg


class TestChannelCommand:
    def test_our_commands(self):
        assert channel_command("!help") == "help"
        assert channel_command("!token") == "token"
        assert channel_command("!HELP token") == "help"

    def test_everything_else_is_ignored(self):
        assert channel_command("hello") is None
        assert channel_command("help") is None
        assert channel_command("!play some song") is None
        assert channel_command("!") is None
        assert channel_command("") is None

    def test_dev_prefix_is_ignored_in_prod(self):
        assert channel_command(".help") is None


class TestPointToDms:
    def test_reacts_and_dms(self):
        msg = message()
        asyncio.run(point_to_dms(msg))
        msg.add_reaction.assert_awaited_once_with("👀")
        msg.author.send.assert_awaited_once()
        assert "`!help`" in msg.author.send.await_args.args[0]

    def test_dms_turned_off(self):
        msg = message()
        msg.author.send.side_effect = forbidden()
        asyncio.run(point_to_dms(msg))
        msg.add_reaction.assert_awaited_once_with("👀")

    def test_no_permission_to_react_still_dms(self):
        msg = message()
        msg.add_reaction.side_effect = forbidden()
        asyncio.run(point_to_dms(msg))
        msg.author.send.assert_awaited_once()

    def test_never_writes_in_the_channel(self):
        msg = message()
        asyncio.run(point_to_dms(msg))
        msg.channel.send.assert_not_called()
        msg.reply.assert_not_called()
