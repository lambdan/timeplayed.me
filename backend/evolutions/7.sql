-- nsfw games have their title and cover censored on the site, unless the viewer opted in
ALTER TABLE game ADD COLUMN nsfw boolean NOT NULL DEFAULT false;
