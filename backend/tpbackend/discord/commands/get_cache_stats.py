from tpbackend.cache import get_cache_stats
from tpbackend.storage import User
from .admin_command import AdminCommand


class GetCacheStats(AdminCommand):
    def __init__(self):
        names = ["get_cache_stats", "gcs"]
        super().__init__(names=names, description="Get cache stats")

    def execute(self, user: User, msg: str) -> str:
        return get_cache_stats()
