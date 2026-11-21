"""
Where the bytes of images are kept, under their id: the imagefile_data table, so every backend
shares them and they're in the database backups. Kept behind this class so something
like S3 can be added without changing the rest
"""

from tpbackend.storage import ImageFileData


class DbStorage:
    def save(self, file_id: str, data: bytes):
        ImageFileData.insert(file=file_id, data=data).on_conflict(
            conflict_target=[ImageFileData.file], update={ImageFileData.data: data}
        ).execute()

    def load(self, file_id: str) -> bytes | None:
        row = (
            ImageFileData.select(ImageFileData.data)
            .where(ImageFileData.file == file_id)
            .first()
        )
        if row is None:
            return None
        return bytes(row.data)


storage = DbStorage()
