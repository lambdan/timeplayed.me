from pathlib import Path

from tpbackend.evolutions import numbered, to_apply


def make_files(directory: Path, names: list[str]):
    for name in names:
        (directory / name).write_text("SELECT 1;")


class TestEvolutionFiles:
    def test_numbered_skips_other_files(self, tmp_path):
        make_files(tmp_path, ["1.sql", "2.sql", "old-2.sql", "notes.txt"])
        assert sorted(numbered(tmp_path)) == [1, 2]

    def test_fresh_database_gets_everything(self, tmp_path):
        make_files(tmp_path, ["1.sql", "2.sql"])
        assert [n for n, _ in to_apply(numbered(tmp_path), current=0)] == [1, 2]

    def test_to_apply_in_numeric_order(self, tmp_path):
        make_files(tmp_path, ["9.sql", "10.sql", "11.sql", "2.sql"])
        pending = to_apply(numbered(tmp_path), current=9)
        assert [n for n, _ in pending] == [10, 11]

    def test_nothing_to_apply(self, tmp_path):
        make_files(tmp_path, ["1.sql", "2.sql"])
        assert to_apply(numbered(tmp_path), current=2) == []
