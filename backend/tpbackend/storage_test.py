from tpbackend import history_actor
from tpbackend.permissions import DEFAULT_PERMISSIONS, DESCRIPTIONS, Permission
from tpbackend.storage import Game, Platform, User


class TestPendingHistory:
    def test_not_shared_between_instances(self):
        a = Game(name="A")
        b = Game(name="B")
        a.add_history("only for a")
        assert len(a.pending_history) == 1
        assert b.pending_history == []

    def test_not_shared_between_models(self):
        g = Game(name="A")
        p = Platform(abbreviation="x")
        g.add_history("only for game")
        assert p.pending_history == []


class TestDefaultPermissions:
    def test_not_shared_with_defaults(self):
        # check the field default, without creating a User
        permissions = User.permissions.default()  # type: ignore
        assert permissions == DEFAULT_PERMISSIONS
        permissions.append("admin")
        assert "admin" not in DEFAULT_PERMISSIONS


class TestPermissions:
    def test_all_have_descriptions(self):
        assert set(DESCRIPTIONS.keys()) == set(Permission)

    def test_matches_stored_strings(self):
        # stored as plain strings, has_permission checks the enum is in that list
        stored = ["admin"]
        assert Permission.ADMIN in stored
        assert Permission.COMMANDS not in stored


class TestGameLabel:
    def test_with_year(self):
        assert (
            Game(name="Vice City", release_year=2002).get_label() == "Vice City (2002)"
        )

    def test_without_year(self):
        assert Game(name="Vice City").get_label() == "Vice City"


class TestHistoryActor:
    def test_none_outside_requests(self):
        g = Game(name="A")
        g.add_history("synced")
        assert g.pending_history[0]["actor"] is None

    def test_from_request(self):
        holder_token = history_actor._holder.set(history_actor._Holder())
        try:
            actor = User(name="admin")
            history_actor.set_history_actor(actor)
            g = Game(name="A")
            g.add_history("edited")
            assert g.pending_history[0]["actor"] is actor
        finally:
            history_actor._holder.reset(holder_token)

    def test_set_outside_requests_does_nothing(self):
        history_actor.set_history_actor(User(name="admin"))
        assert history_actor.get_history_actor() is None
