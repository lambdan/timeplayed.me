from tpbackend.operations import merge_aliases
from tpbackend.storage import Game


class TestMergeAliases:
    def test_new_name_becomes_alias(self):
        assert merge_aliases(Game(name="Bla™"), Game(name="Bla")) == ["Bla™"]

    def test_same_name_is_skipped(self):
        assert merge_aliases(Game(name="Bla"), Game(name="Bla")) == []

    def test_existing_alias_is_skipped(self):
        target = Game(name="Bla", aliases=["Bla™"])
        assert merge_aliases(Game(name="Bla™"), target) == []

    def test_source_aliases_without_duplicates(self):
        source = Game(name="Bla™", aliases=["Bla", "Bla (beta)", "Bla™"])
        assert merge_aliases(source, Game(name="Bla")) == ["Bla™", "Bla (beta)"]
