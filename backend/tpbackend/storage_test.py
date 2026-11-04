from tpbackend.permissions import DEFAULT_PERMISSIONS
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
        # creating a User needs the db (default platform), so check the field default
        permissions = User.permissions.default()  # type: ignore
        assert permissions == DEFAULT_PERMISSIONS
        permissions.append("admin")
        assert "admin" not in DEFAULT_PERMISSIONS


class TestGameLabel:
    def test_with_year(self):
        assert (
            Game(name="Vice City", release_year=2002).get_label() == "Vice City (2002)"
        )

    def test_without_year(self):
        assert Game(name="Vice City").get_label() == "Vice City"
