-- images downloaded from elsewhere (covers), or uploaded. The bytes are in the file storage
-- (FILES_DIR) under the id, this is what we know about them. See tpbackend/files/
CREATE TABLE imagefile (
    id uuid PRIMARY KEY,
    content_type varchar(255) NOT NULL,
    size integer NOT NULL,
    sha256 varchar(64) NOT NULL,
    created timestamp with time zone NOT NULL DEFAULT now(),
    width integer NOT NULL,
    height integer NOT NULL,
    -- where it was downloaded from, empty for uploads and versions
    source text UNIQUE,
    -- smaller versions of an image (display, thumbnail, preview) point to the original
    original uuid REFERENCES imagefile (id) ON DELETE CASCADE,
    version varchar(255),
    UNIQUE (original, version)
);
