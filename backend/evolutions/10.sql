-- the bytes of files, so every backend shares them (they were on disk, in FILES_DIR)
CREATE TABLE imagefile_data (
    id uuid PRIMARY KEY REFERENCES imagefile (id) ON DELETE CASCADE,
    data bytea NOT NULL
);
-- the files on disk are left behind. Covers are fetched from IGDB again, uploads are
-- gone and need to be uploaded again (this removes their game_cover rows too)
DELETE FROM imagefile;
