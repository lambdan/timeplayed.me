-- platforms can have a parent, the parent's stats include its children (like games)
ALTER TABLE platform ADD COLUMN IF NOT EXISTS parent_id integer REFERENCES platform(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS platform_parent_id ON platform (parent_id);

-- PC operating systems and PC handhelds go under PC
CREATE TEMP TABLE moved ON COMMIT DROP AS
SELECT child.id AS child_id, parent.id AS parent_id
FROM platform child, platform parent
WHERE child.abbreviation IN ('win', 'mac', 'linux', 'steamdeck')
    AND parent.abbreviation = 'pc'
    AND child.parent_id IS NULL;

UPDATE platform p SET parent_id = m.parent_id
FROM moved m WHERE p.id = m.child_id;

INSERT INTO history (platform_id, message)
SELECT m.child_id, 'Parent changed from None to ''pc'' (' || m.parent_id || ') by evolution 14'
FROM moved m;
