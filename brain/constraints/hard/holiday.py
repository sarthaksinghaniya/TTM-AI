"""Holiday overlap hard constraint check."""

from brain.constraints.base import BaseConstraintEvaluator, ConstraintContext
from brain.models import Conflict, Severity
from brain.models.timetable import Timetable


class HolidayConstraint(BaseConstraintEvaluator):
    """Checks if any assignment is scheduled on a holiday slot."""

    def evaluate(
        self, timetable: Timetable, context: ConstraintContext
    ) -> list[Conflict]:
        """Evaluate holiday overlaps in the timetable.

        Args:
            timetable: The Timetable instance.
            context: The ConstraintContext dataset.

        Returns:
            A list of Conflict instances.
        """
        conflicts: list[Conflict] = []
        holidays_set = set(context.holidays)

        for assignment in timetable.assignments:
            if assignment.slot_id in holidays_set:
                desc = (
                    f"Assignment '{assignment.assignment_id}' is scheduled "
                    f"on holiday slot '{assignment.slot_id}'."
                )
                conflicts.append(
                    Conflict(
                        conflict_id=f"HOLIDAY_OVERLAP_{assignment.assignment_id}",
                        description=desc,
                        severity=Severity.HARD,
                        suggestion=(
                            f"Reschedule assignment '{assignment.assignment_id}' "
                            f"to a non-holiday slot."
                        ),
                    )
                )
        return conflicts
