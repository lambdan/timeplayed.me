-- versions that were copies of an original that's small enough to be that version itself
-- (like IGDB's covers, 264x352, as the 600x900 display version). The original is used for
-- them now, see is_own_version in tpbackend/files/images.py. Their bytes go with them
DELETE FROM imagefile v
USING imagefile o
WHERE v.original = o.id
    AND o.content_type IN ('image/jpeg', 'image/png', 'image/webp')
    AND (
        (v.version = 'display' AND o.width <= 600 AND o.height <= 900)
        OR (v.version = 'thumbnail' AND o.width <= 120 AND o.height <= 180)
        OR (v.version = 'preview' AND o.width <= 8 AND o.height <= 12)
    );
