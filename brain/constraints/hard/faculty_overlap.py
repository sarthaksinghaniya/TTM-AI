"""Faculty overlap hard constraint check."""

from collections import defaultdict

from brain.constraints.base import BaseConstraintEvaluator, ConstraintContext
from brain.models import Conflict, Severity
from brain.models.timetable import Timetable


class FacultyOverlapConstraint(BaseConstraintEvaluator):
    """Checks if a faculty member is double-booked at the same slot."""

    def evaluate(
        self, timetable: Timetable, context: ConstraintContext
    ) -> list[Conflict]:
        """Evaluate faculty overlaps in the timetable.

        Args:
            timetable: The Timetable instance.
            context: The ConstraintContext dataset.

        Returns:
            A list of Conflict instances.
        """
        conflicts: list[Conflict] = []
        # Group assignments by faculty and slot
        faculty_slot_map: dict[tuple[str, str], list[str]] = defaultdict(list)
        for assignment in timetable.assignments:
            key = (assignment.faculty_id, assignment.slot_id)
            faculty_slot_map[key].append(assignment.assignment_id)

        for (fac_id, slot_id), assign_ids in faculty_slot_map.items():
            if len(assign_ids) > 1:
                desc = (
                    f"Faculty '{fac_id}' is double-booked at slot '{slot_id}' "
                    f"in assignments: {', '.join(assign_ids)}."
                )
                conflicts.append(
                    Conflict(
                        conflict_id=f"FACULTY_OVERLAP_{fac_id}_{slot_id}",
                        description=desc,
                        severity=Severity.HARD,
                        suggestion=(
                            f"Move one of the assignments for faculty '{fac_id}' "
                            f"at slot '{slot_id}' to a different slot."
                        ),
                    )
                )
        return conflicts
