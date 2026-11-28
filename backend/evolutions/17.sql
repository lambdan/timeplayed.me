-- show_name and show_avatar are replaced by the anonymous setting. They were only ever
-- removed by admins, so users missing either are forced anonymous
UPDATE "user" SET permissions = array_append(permissions, 'force_anonymous')
WHERE NOT ('show_name' = ANY(coalesce(permissions, '{}')) AND 'show_avatar' = ANY(coalesce(permissions, '{}')));
UPDATE "user" SET permissions = array_remove(array_remove(permissions, 'show_name'), 'show_avatar');
