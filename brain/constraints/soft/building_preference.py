"""Building preference soft constraint check."""

import datetime
import re
from collections import defaultdict

from brain.constraints.base import BaseConstraintEvaluator, ConstraintContext
from brain.models import Conflict, Severity
from brain.models.timetable import Timetable


class BuildingPreferenceConstraint(BaseConstraintEvaluator):
    """Penalizes building changes for consecutive classes."""

    def evaluate(
        self, timetable: Timetable, context: ConstraintContext
    ) -> list[Conflict]:
        """Evaluate building transitions in the timetable.

        Args:
            timetable: The Timetable instance.
            context: The ConstraintContext dataset.

        Returns:
            A list of Conflict instances.
        """
        conflicts: list[Conflict] = []
        slots_map = {s.slot_id: s for s in context.slots}
        rooms_map = {r.room_id: r for r in context.rooms}

        # Helper to extract building from room_id (e.g. prefix character/letters)
        def get_building(room_id: str) -> str:
            match = re.match(r"^([a-zA-Z]+)", room_id)
            if match:
                return match.group(1)
            return room_id[0] if room_id else ""

        # Group assignments by section and day
        section_day_classes: dict[
            tuple[str, str], list[tuple[datetime.time, str, str]]
        ] = defaultdict(list)
        for a in timetable.assignments:
            slot = slots_map.get(a.slot_id)
            room = rooms_map.get(a.room_id)
            if slot and room:
                bldg = get_building(room.room_id)
                section_day_classes[(a.section_id, slot.day)].append(
                    (slot.start_time, bldg, a.assignment_id)
                )

        # Check building changes for consecutive classes
        for (sec_id, day), classes in section_day_classes.items():
            classes.sort(key=lambda x: x[0])
            for i in range(len(classes) - 1):
                bldg_curr = classes[i][1]
                bldg_next = classes[i + 1][1]
                if bldg_curr != bldg_next:
                    desc = (
                        f"Section '{sec_id}' must change buildings from '{bldg_curr}' "
                        f"to '{bldg_next}' on {day}."
                    )
                    conflicts.append(
                        Conflict(
                            conflict_id=f"BUILDING_CHANGE_{sec_id}_{day}_{i}",
                            description=desc,
                            severity=Severity.SOFT,
                            suggestion=(
                                f"Reschedule consecutive classes for "
                                f"section '{sec_id}' in the same building."
                            ),
                        )
                    )
        return conflicts
