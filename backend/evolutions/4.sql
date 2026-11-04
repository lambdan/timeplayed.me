-- name and avatar are hidden unless the user has these, existing users keep showing them
UPDATE "user" SET permissions = array_append(permissions, 'show_avatar')
WHERE NOT ('show_avatar' = ANY(coalesce(permissions, '{}')));
UPDATE "user" SET permissions = array_append(permissions, 'show_name')
WHERE NOT ('show_name' = ANY(coalesce(permissions, '{}')));
