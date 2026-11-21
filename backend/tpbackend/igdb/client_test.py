import threading
import time

from tpbackend.igdb import client as client_module
from tpbackend.igdb.client import IGDBClient


class FakeTokenResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"access_token": "token", "expires_in": 3600}


class TestAuthenticate:
    def test_threads_log_in_once(self, monkeypatch):
        logins = []

        def fake_post(url, data):
            logins.append(url)
            # slow, so the other threads come in while this one is logging in
            time.sleep(0.05)
            return FakeTokenResponse()

        monkeypatch.setattr(client_module.requests, "post", fake_post)
        igdb = IGDBClient(client_id="id", client_secret="secret")

        threads = [threading.Thread(target=igdb._authenticate) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(logins) == 1
        assert igdb.token == "token"
