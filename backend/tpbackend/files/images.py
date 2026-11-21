"""
Images we keep (like covers), downloaded from elsewhere or uploaded, so they're served
from here. The bytes go to the file storage, the rest to ImageFile.

The original is kept as it is, and smaller versions are made from it, each
its own ImageFile pointing to the original
"""

import hashlib
import io
import logging
import time

import requests
from peewee import IntegrityError
from PIL import Image

from tpbackend.files.storage import storage
from tpbackend.keyed_lock import KeyedLock
from tpbackend.storage import ImageFile

logger = logging.getLogger("images")

MAX_IMAGE_BYTES = 10 * 1024 * 1024
TIMEOUT_SECONDS = 10
# the image types we keep
CONTENT_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"]


class Version:
    def __init__(self, name: str, size: tuple[int, int], format: str):
        self.name = name
        # shrunk to fit, never enlarged
        self.size = size
        self.format = format


# what the site shows
DISPLAY = Version("display", (600, 900), "WEBP")
# small covers in lists, 3x their size on the page so they're sharp on phones too
THUMBNAIL = Version("thumbnail", (120, 180), "WEBP")
# a few pixels, shown blurred while loading (or instead of the image, for NSFW)
PREVIEW = Version("preview", (8, 12), "PNG")
VERSIONS = {v.name: v for v in [DISPLAY, THUMBNAIL, PREVIEW]}
WEBP_QUALITY = 85

# a page asks for many covers at once, often the same one several times. Only one
# request downloads an image or makes its versions, the others wait and use those
downloading = KeyedLock()
making_versions = KeyedLock()


def download(url: str) -> bytes:
    if not url.startswith(("https://", "http://")):
        raise ValueError(f"Not a http(s) URL: {url}")
    started = time.monotonic()
    with requests.get(url, timeout=TIMEOUT_SECONDS, stream=True) as r:
        r.raise_for_status()
        data = r.raw.read(MAX_IMAGE_BYTES + 1, decode_content=True)
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(f"Image is over {MAX_IMAGE_BYTES} bytes: {url}")
    logger.info(
        "Downloaded %s, %d bytes, %.2fs", url, len(data), time.monotonic() - started
    )
    return data


class ImageInfo:
    """what we need to know about image bytes, from what the image actually is
    (a Content-Type header can't be trusted)"""

    def __init__(self, data: bytes):
        with Image.open(io.BytesIO(data)) as image:
            self.content_type = Image.MIME.get(image.format or "")
            self.width, self.height = image.size
        if self.content_type not in CONTENT_TYPES:
            raise ValueError(f"Unsupported image type: {self.content_type}")
        self.size = len(data)
        self.sha256 = hashlib.sha256(data).hexdigest()


def make_version(data: bytes, version: Version) -> bytes:
    with Image.open(io.BytesIO(data)) as image:
        has_alpha = image.mode in ("RGBA", "LA", "PA") or "transparency" in image.info
        if has_alpha:
            small = image.convert("RGBA")
        else:
            small = image.convert("RGB")
        small.thumbnail(version.size)
        out = io.BytesIO()
        if version.format == "WEBP":
            small.save(out, format="WEBP", quality=WEBP_QUALITY)
        else:
            small.save(out, format=version.format)
    return out.getvalue()


def public_url(image: ImageFile) -> str:
    return f"/api/files/{image.get_id()}"


def new_image(data: bytes, **fields) -> ImageFile:
    """stores the bytes and makes an ImageFile for them (not saved yet)"""
    info = ImageInfo(data)
    image = ImageFile(
        content_type=info.content_type,
        size=info.size,
        sha256=info.sha256,
        width=info.width,
        height=info.height,
        **fields,
    )
    storage.save(image.get_id(), data)
    return image


def stored_image(url: str) -> ImageFile | None:
    """the image if we have it already, without downloading it"""
    return ImageFile.get_or_none(ImageFile.source == url)


def get_image(url: str) -> ImageFile | None:
    """the image, downloaded and stored first if we don't have it. None if that fails"""
    image = stored_image(url)
    if image and storage.exists(image.get_id()):
        return image
    with downloading.hold(url):
        return __download_image(url)


def __download_image(url: str) -> ImageFile | None:
    # it may have been downloaded while we waited
    image = stored_image(url)
    if image and storage.exists(image.get_id()):
        return image

    try:
        data = download(url)
        if image:
            # we had it, but the storage lost the file (cleared folder, new server)
            ImageInfo(data)
            storage.save(image.get_id(), data)
            logger.info("Restored %s from %s", image.get_id(), url)
            return image
        image = new_image(data, source=url)
    except Exception as e:
        logger.error("Could not download image %s: %s", url, e)
        return None

    try:
        image.save(force_insert=True)
    except IntegrityError:
        # downloaded at the same time somewhere else, theirs is the same image
        storage.delete(image.get_id())
        return stored_image(url)
    logger.info(
        "Stored %s: %s %dx%d, %d bytes, from %s",
        image.get_id(),
        image.get_content_type(),
        image.get_width(),
        image.get_height(),
        image.get_size(),
        url,
    )
    return image


def stored_versions(image: ImageFile) -> dict[str, ImageFile]:
    """the versions that are made already, by name"""
    versions = ImageFile.select().where(ImageFile.original == image.get_id())
    return {v.get_version(): v for v in versions}


def get_version(image: ImageFile, version: Version) -> ImageFile | None:
    """the version, made first if needed. None if the original is gone"""
    stored = stored_versions(image).get(version.name)
    if stored:
        return stored
    data = load_image(image)
    if data is None:
        return None
    started = time.monotonic()
    made = new_image(
        make_version(data, version), original=image.get_id(), version=version.name
    )
    try:
        made.save(force_insert=True)
        logger.info(
            "Stored %s: %s of %s, %s %dx%d, %d bytes, %.2fs",
            made.get_id(),
            version.name,
            image.get_id(),
            made.get_content_type(),
            made.get_width(),
            made.get_height(),
            made.get_size(),
            time.monotonic() - started,
        )
        return made
    except IntegrityError:
        # made at the same time somewhere else
        storage.delete(made.get_id())
        return stored_versions(image).get(version.name)


def get_versions(image: ImageFile) -> dict[str, ImageFile]:
    """all versions of the image by name, the missing ones are made first"""
    stored = stored_versions(image)
    if all(name in stored for name in VERSIONS):
        return stored
    with making_versions.hold(image.get_id()):
        versions = {}
        for version in VERSIONS.values():
            made = get_version(image, version)
            if made:
                versions[version.name] = made
        return versions


def store_upload(data: bytes) -> ImageFile:
    """an uploaded image, stored with all its versions. Raises if it's not an image we take"""
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError(f"Image is over {MAX_IMAGE_BYTES} bytes")
    image = new_image(data)
    image.save(force_insert=True)
    logger.info(
        "Stored %s: %s %dx%d, %d bytes, uploaded",
        image.get_id(),
        image.get_content_type(),
        image.get_width(),
        image.get_height(),
        image.get_size(),
    )
    get_versions(image)
    return image


def load_image(image: ImageFile) -> bytes | None:
    """the bytes, made again if the storage lost them (from the source, or the original)"""
    data = storage.load(image.get_id())
    if data is not None:
        return data

    source = image.get_source()
    if source:
        if get_image(source) is None:
            return None
        return storage.load(image.get_id())

    original = image.get_original()
    version = VERSIONS.get(image.get_version() or "")
    if original and version:
        logger.info(
            "Remaking %s (%s of %s), it's missing from storage",
            image.get_id(),
            version.name,
            original.get_id(),
        )
        original_data = load_image(original)
        if original_data is None:
            return None
        data = make_version(original_data, version)
        storage.save(image.get_id(), data)
        return data

    # an upload that's gone, nothing to make it from
    logger.error("%s is missing from storage, and can't be made again", image.get_id())
    return None
