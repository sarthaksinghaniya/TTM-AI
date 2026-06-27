"""Minimum gap / window period soft constraint check."""

from collections import defaultdict

from brain.constraints.base import BaseConstraintEvaluator, ConstraintContext
from brain.models import Conflict, Severity
from brain.models.timetable import Timetable


class MinimumGapConstraint(BaseConstraintEvaluator):
    """Penalizes isolated idle slots between classes on the same day."""

    def evaluate(
        self, timetable: Timetable, context: ConstraintContext
    ) -> list[Conflict]:
        """Evaluate if there are window periods (idle slots) in the section schedules.

        Args:
            timetable: The Timetable instance.
            context: The ConstraintContext dataset.

        Returns:
            A list of Conflict instances.
        """
        conflicts: list[Conflict] = []
        slots_map = {s.slot_id: s for s in context.slots}

        # Find all scheduled slots for each section
        section_scheduled_slots = defaultdict(set)
        # Group assignments by section and day
        section_day_slots = defaultdict(list)

        for a in timetable.assignments:
            slot = slots_map.get(a.slot_id)
            if slot:
                section_scheduled_slots[a.section_id].add(a.slot_id)
                section_day_slots[(a.section_id, slot.day)].append(
                    (slot.start_time, slot.end_time, a.assignment_id)
                )

        # Check for window periods
        for (sec_id, day), assigned in section_day_slots.items():
            # Sort slots by start time
            assigned.sort(key=lambda x: x[0])
            scheduled_ids = section_scheduled_slots[sec_id]

            for i in range(len(assigned) - 1):
                curr_start = assigned[i][0]
                next_start = assigned[i + 1][0]

                # Find slots on this day strictly between current and next class
                day_slots = [s for s in context.slots if s.day == day]
                idle_slots = [
                    s
                    for s in day_slots
                    if curr_start < s.start_time < next_start
                    and s.slot_id not in scheduled_ids
                ]

                # If there are idle slots in the middle, penalize it
                if idle_slots:
                    desc = (
                        f"Section '{sec_id}' has an idle gap of "
                        f"{len(idle_slots)} slots on {day} between classes."
                    )
                    conflicts.append(
                        Conflict(
                            conflict_id=f"GAP_VIOLATION_{sec_id}_{day}_{i}",
                            description=desc,
                            severity=Severity.SOFT,
                            suggestion=(
                                f"Reschedule classes for section '{sec_id}' on {day} "
                                f"to be consecutive."
                            ),
                        )
                    )
        return conflicts
