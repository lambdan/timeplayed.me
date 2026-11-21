import uuid

import pytest

from tpbackend.files.storage import DiskStorage


class TestDiskStorage:
    def test_save_and_load(self, tmp_path):
        storage = DiskStorage(tmp_path / "files")
        file_id = str(uuid.uuid4())
        assert not storage.exists(file_id)
        assert storage.load(file_id) is None
        storage.save(file_id, b"hello")
        assert storage.exists(file_id)
        assert storage.load(file_id) == b"hello"

    def test_in_subfolder(self, tmp_path):
        storage = DiskStorage(tmp_path)
        file_id = "3fa9c2d1-0000-4000-8000-000000000000"
        storage.save(file_id, b"hello")
        assert (tmp_path / "3f" / file_id).read_bytes() == b"hello"

    def test_no_temporary_file_left(self, tmp_path):
        storage = DiskStorage(tmp_path)
        file_id = str(uuid.uuid4())
        storage.save(file_id, b"hello")
        assert [p.name for p in (tmp_path / file_id[:2]).iterdir()] == [file_id]

    def test_only_uuids(self, tmp_path):
        storage = DiskStorage(tmp_path)
        with pytest.raises(ValueError):
            storage.load("../secret")
