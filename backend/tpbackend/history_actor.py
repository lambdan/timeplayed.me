"""
Who made a change, so history can say it without every route passing it along.

Each API request gets its own holder (HistoryActorMiddleware), and authenticating
puts the user in it. History written during that request gets them as actor.
Outside requests (Oblivionis sync, the Discord bot) there is no holder, so the actor
is None.

The holder is a mutable object on purpose: sync dependencies and routes run in a
thread pool with a copy of the request's context, so a value set there wouldn't
reach the route. The copy still points to the same holder.
"""

from contextvars import ContextVar

from starlette.types import ASGIApp, Receive, Scope, Send


class _Holder:
    def __init__(self):
        self.actor = None


_holder: ContextVar[_Holder | None] = ContextVar("history_actor", default=None)


def set_history_actor(user):
    holder = _holder.get()
    if holder:
        holder.actor = user


def get_history_actor():
    holder = _holder.get()
    if holder:
        return holder.actor
    return None


class HistoryActorMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        token = _holder.set(_Holder())
        try:
            await self.app(scope, receive, send)
        finally:
            _holder.reset(token)
