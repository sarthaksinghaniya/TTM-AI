"""Balanced workload soft constraint check."""

from collections import defaultdict

from brain.constraints.base import BaseConstraintEvaluator, ConstraintContext
from brain.models import Conflict, Severity
from brain.models.timetable import Timetable


class BalancedWorkloadConstraint(BaseConstraintEvaluator):
    """Penalizes sections with excess daily classes."""

    def evaluate(
        self, timetable: Timetable, context: ConstraintContext
    ) -> list[Conflict]:
        """Evaluate workload balance in the timetable.

        Args:
            timetable: The Timetable instance.
            context: The ConstraintContext dataset.

        Returns:
            A list of Conflict instances.
        """
        conflicts: list[Conflict] = []
        slots_map = {s.slot_id: s for s in context.slots}

        # Count assignments per section and day
        section_day_count: dict[tuple[str, str], int] = defaultdict(int)
        for a in timetable.assignments:
            slot = slots_map.get(a.slot_id)
            if slot:
                section_day_count[(a.section_id, slot.day)] += 1

        # Max classes per day threshold = 4
        limit = 4
        for (sec_id, day), count in section_day_count.items():
            if count > limit:
                excess = count - limit
                desc = (
                    f"Section '{sec_id}' has {count} classes on {day}, "
                    f"which exceeds the balance limit of {limit} by {excess}."
                )
                conflicts.append(
                    Conflict(
                        conflict_id=f"WORKLOAD_VIOLATION_{sec_id}_{day}",
                        description=desc,
                        severity=Severity.SOFT,
                        suggestion=(
                            f"Move some classes for section '{sec_id}' from {day} "
                            f"to other days."
                        ),
                    )
                )
        return conflicts
