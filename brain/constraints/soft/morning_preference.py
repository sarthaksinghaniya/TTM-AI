"""Morning preference soft constraint check."""

import datetime

from brain.constraints.base import BaseConstraintEvaluator, ConstraintContext
from brain.models import Conflict, Severity
from brain.models.timetable import Timetable


class MorningPreferenceConstraint(BaseConstraintEvaluator):
    """Penalizes assignments scheduled in the afternoon (start time >= 12:00 PM)."""

    def evaluate(
        self, timetable: Timetable, context: ConstraintContext
    ) -> list[Conflict]:
        """Evaluate morning preferences in the timetable.

        Args:
            timetable: The Timetable instance.
            context: The ConstraintContext dataset.

        Returns:
            A list of Conflict instances.
        """
        conflicts: list[Conflict] = []
        slots_map = {s.slot_id: s for s in context.slots}

        for assignment in timetable.assignments:
            slot = slots_map.get(assignment.slot_id)
            if slot and slot.start_time >= datetime.time(12, 0):
                desc = (
                    f"Assignment '{assignment.assignment_id}' is scheduled in the "
                    f"afternoon at slot '{assignment.slot_id}' "
                    f"(starts at {slot.start_time})."
                )
                conflicts.append(
                    Conflict(
                        conflict_id=f"MORNING_PREF_VIOLATION_{assignment.assignment_id}",
                        description=desc,
                        severity=Severity.SOFT,
                        suggestion=(
                            f"Reschedule assignment '{assignment.assignment_id}' "
                            f"to a morning slot."
                        ),
                    )
                )
        return conflicts
