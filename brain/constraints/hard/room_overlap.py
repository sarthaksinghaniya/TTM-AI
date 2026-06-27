"""Room overlap hard constraint check."""

from collections import defaultdict

from brain.constraints.base import BaseConstraintEvaluator, ConstraintContext
from brain.models import Conflict, Severity
from brain.models.timetable import Timetable


class RoomOverlapConstraint(BaseConstraintEvaluator):
    """Checks if a room is double-booked at the same slot."""

    def evaluate(
        self, timetable: Timetable, context: ConstraintContext
    ) -> list[Conflict]:
        """Evaluate room overlaps in the timetable.

        Args:
            timetable: The Timetable instance.
            context: The ConstraintContext dataset.

        Returns:
            A list of Conflict instances.
        """
        conflicts: list[Conflict] = []
        # Group assignments by room and slot
        room_slot_map: dict[tuple[str, str], list[str]] = defaultdict(list)
        for assignment in timetable.assignments:
            key = (assignment.room_id, assignment.slot_id)
            room_slot_map[key].append(assignment.assignment_id)

        for (room_id, slot_id), assign_ids in room_slot_map.items():
            if len(assign_ids) > 1:
                desc = (
                    f"Room '{room_id}' is double-booked at slot '{slot_id}' "
                    f"in assignments: {', '.join(assign_ids)}."
                )
                conflicts.append(
                    Conflict(
                        conflict_id=f"ROOM_OVERLAP_{room_id}_{slot_id}",
                        description=desc,
                        severity=Severity.HARD,
                        suggestion=(
                            f"Reassign room '{room_id}' or reschedule one of the "
                            f"assignments at slot '{slot_id}'."
                        ),
                    )
                )
        return conflicts
