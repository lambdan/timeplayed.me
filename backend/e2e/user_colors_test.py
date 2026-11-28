from tpbackend.storage import User


def colors(api, user: User) -> tuple[str | None, str | None]:
    data = api.get(f"/user/{user.get_id()}").json()
    return data["color_primary"], data["color_secondary"]


class TestUserColors:
    def test_none_by_default(self, api, make_user):
        user, _ = make_user()
        assert colors(api, user) == (None, None)

    def test_set_in_settings(self, api, make_user):
        user, client = make_user()
        r = client.put(
            "/settings", json={"color_primary": "#1A2B3C", "color_secondary": "ffffff"}
        )
        assert r.status_code == 200, r.text
        assert r.json()["color_primary"] == "1a2b3c"
        assert colors(api, user) == ("1a2b3c", "ffffff")
        user = User.get_by_id(user.get_id())
        messages = [h.message for h in user.get_history_entries()]
        assert "Primary color changed from 'None' to '1a2b3c'" in messages

    def test_left_out_stays(self, api, make_user):
        user, client = make_user(color_primary="1a2b3c", color_secondary="ffffff")
        client.put("/settings", json={"show_nsfw": True})
        assert colors(api, user) == ("1a2b3c", "ffffff")

    def test_empty_removes(self, api, make_user):
        user, client = make_user(color_primary="1a2b3c", color_secondary="ffffff")
        r = client.put("/settings", json={"color_primary": "", "color_secondary": ""})
        assert r.status_code == 200, r.text
        assert colors(api, user) == (None, None)

    def test_not_a_color_changes_nothing(self, api, make_user):
        user, client = make_user(color_primary="1a2b3c")
        r = client.put("/settings", json={"color_primary": "red", "show_nsfw": True})
        assert r.status_code == 400
        assert colors(api, user) == ("1a2b3c", None)
        assert "show_nsfw" not in User.get_by_id(user.get_id()).get_permissions()

    def test_in_user_lists(self, api, make_user):
        make_user(color_primary="1a2b3c", color_secondary="ffffff")
        users = api.get("/users").json()
        assert [(u["color_primary"], u["color_secondary"]) for u in users] == [
            ("1a2b3c", "ffffff")
        ]
