from tpbackend.game.select import GameSelect
from tpbackend.storage import User, Game, Activity
from .admin_command import AdminCommand
from typing import cast


class HideGameCommand(AdminCommand):
    def __init__(self):
        names = ["hide_game", "hg"]
        d = "Toggle hidden state of game"
        h = "Toggles hidden state of game"
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        game = GameSelect.by_id(int(msg))
        if not game:
            return f"Error: Game with id {msg} not found."
        game.set_hidden(not game.get_hidden())
        game.save()
        state = "hidden" if game.get_hidden() else "visible"
        affected_activities = self.updateActivities(game)
        return f"Game '{game.name}' is now {state}. {affected_activities} activities updated hidden state."

    def updateActivities(self, game: Game) -> int:
        """
        Update hidden state of activities for game
        """
        activities = Activity.select().where(Activity.game == game)
        changed = 0
        for activity in activities:
            activity = cast(Activity, activity)
            if activity.get_hidden() == game.get_hidden():
                continue
            activity.set_hidden(game.get_hidden())
            activity.save()
            changed += 1
        return changed
