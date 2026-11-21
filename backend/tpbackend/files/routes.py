import uuid

from fastapi import APIRouter, Response

from tpbackend.api.responses import not_found
from tpbackend.files.storage import storage
from tpbackend.storage import ImageFile

router = APIRouter()

# an id always has the same content, so browsers can keep it forever
CACHE_FOREVER = "public, max-age=31536000, immutable"


@router.get("/{file_id}")
def get_file(file_id: uuid.UUID) -> Response:
    # looked up in the database first, so only files we have can be asked for.
    # images are the only kind of File so far, other kinds get looked up here too
    image = ImageFile.get_or_none(ImageFile.id == file_id)
    if not image:
        return not_found("File not found")

    data = storage.load(image.get_id())
    if data is None:
        return not_found("File not found")

    return Response(
        content=data,
        media_type=image.get_content_type(),
        headers={"Cache-Control": CACHE_FOREVER},
    )
