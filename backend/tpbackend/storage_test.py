from tpbackend.storage import Game, Platform


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
