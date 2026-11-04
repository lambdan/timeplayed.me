from tpbackend.operations import find_overlapping_groups, merge_overlapping_group
from tpbackend.storage import User
from .admin_command import AdminCommand

PREVIEW_GROUPS = 10


class MergeOverlapsAdminCommand(AdminCommand):
    def __init__(self):
        names = ["merge_overlaps"]
        d = "Merge all overlapping activities (retroactively)"
        h = f"""
Finds activities (same user, game and platform) that overlap each other and merges them into the longest one, spanning from the earliest start to the latest end.

Usage: `!{names[0]} [y]`
Shows what will happen, run it again with `y` at the end to do it.
        """
        super().__init__(names=names, description=d, help=h)

    def execute(self, user: User, msg: str) -> str:
        confirmed = msg.strip().lower() == "y"
        groups = find_overlapping_groups()
        if not groups:
            return "No overlapping activities found."

        removed = sum(len(group) - 1 for group in groups)
        if confirmed:
            for group in groups:
                merge_overlapping_group(group)
            return f"Merged {len(groups)} groups, {removed} activities removed."

        out = f"Found {len(groups)} groups of overlapping activities, {removed} activities would be removed.\n"
        for group in groups[:PREVIEW_GROUPS]:
            keep = max(group, key=lambda a: a.get_seconds())
            others = [f"#{a.get_id()}" for a in group if a.get_id() != keep.get_id()]
            out += f"- keep #{keep.get_id()}, remove {', '.join(others)}\n"
        if len(groups) > PREVIEW_GROUPS:
            out += f"- ...and {len(groups) - PREVIEW_GROUPS} more\n"
        out += "Run the command again with `y` at the end to confirm."
        return out
