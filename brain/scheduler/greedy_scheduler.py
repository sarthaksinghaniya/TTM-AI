"""Greedy scheduler implementing Brelaz heuristics and MRV constraints."""

import time
from collections import defaultdict
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from brain.constraints.base import ConstraintContext
from brain.graph.builder import ConflictGraphBuilder
from brain.models import Assignment, Day, Timetable


class SchedulerStatistics(BaseModel):
    """Execution statistics for a scheduling run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    runtime_ms: float
    failed_count: int
    success_rate: float


class SchedulerResult(BaseModel):
    """The output result of a scheduling run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    partial_timetable: Timetable
    locked_assignments: list[Assignment]
    unscheduled_assignments: list[Assignment]
    statistics: SchedulerStatistics


class GreedyScheduler:
    """Greedy scheduler utilizing MRV and highest-degree first heuristics."""

    _day_order: ClassVar[dict[Day, int]] = {
        Day.MONDAY: 1,
        Day.TUESDAY: 2,
        Day.WEDNESDAY: 3,
        Day.THURSDAY: 4,
        Day.FRIDAY: 5,
        Day.SATURDAY: 6,
        Day.SUNDAY: 7,
    }

    def schedule(
        self,
        timetable: Timetable,
        context: ConstraintContext,
        locked_assignment_ids: set[str] | None = None,
    ) -> SchedulerResult:
        """Schedule unlocked assignments in the timetable.

        Args:
            timetable: The Timetable containing assignments.
            context: The ConstraintContext containing available resources.
            locked_assignment_ids: Set of assignment IDs that must not be changed.

        Returns:
            A SchedulerResult instance.

        Raises:
            SchedulingError: If resources or constraints are in an invalid state.
        """
        start_time = time.perf_counter()
        locked_ids = locked_assignment_ids or set()

        # Split locked and unlocked assignments
        locked_assignments: list[Assignment] = []
        unlocked_assignments: list[Assignment] = []
        for a in timetable.assignments:
            if a.assignment_id in locked_ids:
                locked_assignments.append(a)
            else:
                unlocked_assignments.append(a)

        # Track busy/occupied resources in slots
        faculty_busy: dict[str, set[str]] = defaultdict(set)
        section_busy: dict[str, set[str]] = defaultdict(set)
        room_slot_occupied: set[tuple[str, str]] = set()

        for la in locked_assignments:
            faculty_busy[la.faculty_id].add(la.slot_id)
            section_busy[la.section_id].add(la.slot_id)
            room_slot_occupied.add((la.slot_id, la.room_id))

        # Build map for section strengths
        section_map = {s.section_id: s for s in context.sections}

        # Build candidate rooms for each unlocked assignment based on section strength
        candidate_rooms_map: dict[str, list[str]] = {}
        for a in unlocked_assignments:
            sec = section_map.get(a.section_id)
            strength = sec.strength if sec else 0
            # Rooms must fit the section strength
            fitting_rooms = [r.room_id for r in context.rooms if r.capacity >= strength]
            candidate_rooms_map[a.assignment_id] = fitting_rooms

        # Build a temporary timetable to construct the static conflict graph
        # (shared faculty/section)
        temp_assignments = [
            Assignment.model_construct(
                assignment_id=a.assignment_id,
                section_id=a.section_id,
                faculty_id=a.faculty_id,
                subject_code=a.subject_code,
                slot_id="TEMP_SLOT",
                room_id=f"TEMP_ROOM_{idx}",
            )
            for idx, a in enumerate(unlocked_assignments)
        ]
        temp_timetable = Timetable(assignments=temp_assignments)
        conflict_graph = ConflictGraphBuilder.build_graph(temp_timetable)
        static_degrees = dict(conflict_graph.degree())

        # Initialize domains: all slots in context except holidays
        holidays_set = set(context.holidays)
        base_slots = [s for s in context.slots if s.slot_id not in holidays_set]

        # Initial domains for each unlocked assignment
        domains: dict[str, set[str]] = {}
        for a in unlocked_assignments:
            domains[a.assignment_id] = {s.slot_id for s in base_slots}
            # Remove slots occupied by locked assignments sharing faculty or section
            for locked in locked_assignments:
                if (
                    locked.faculty_id == a.faculty_id
                    or locked.section_id == a.section_id
                ):
                    domains[a.assignment_id].discard(locked.slot_id)

        # Mapping for easy lookup
        assignment_map = {a.assignment_id: a for a in unlocked_assignments}
        unscheduled_queue = set(assignment_map.keys())

        scheduled_assignments: list[Assignment] = []
        unscheduled_assignments: list[Assignment] = []

        slots_lookup = {s.slot_id: s for s in context.slots}

        # Main greedy assignment loop
        while unscheduled_queue:
            # For each remaining assignment, count currently feasible slots
            feasible_slots_count: dict[str, int] = {}
            for a_id in unscheduled_queue:
                a = assignment_map[a_id]
                count = 0
                for s_id in domains[a_id]:
                    # Slot is feasible only if there is a candidate room unoccupied
                    # in that slot
                    has_room = any(
                        (s_id, r_id) not in room_slot_occupied
                        for r_id in candidate_rooms_map[a_id]
                    )
                    if has_room:
                        count += 1
                feasible_slots_count[a_id] = count

            # Select the assignment with the fewest feasible slots (MRV)
            # Tie break 1: highest static degree in conflict graph
            # Tie break 2: lexicographical order of assignment_id
            curr_id = min(
                unscheduled_queue,
                key=lambda uid: (
                    feasible_slots_count[uid],
                    -static_degrees.get(uid, 0),
                    uid,
                ),
            )

            unscheduled_queue.remove(curr_id)
            curr_assign = assignment_map[curr_id]

            if feasible_slots_count[curr_id] == 0:
                unscheduled_assignments.append(curr_assign)
                continue

            # Sort available slots by Day order and then Start Time
            # (Earliest feasible slot)
            available_slots = []
            for s_id in domains[curr_id]:
                slot = slots_lookup.get(s_id)
                if slot:
                    # Check if there is an unoccupied candidate room
                    valid_rooms = [
                        r_id
                        for r_id in candidate_rooms_map[curr_id]
                        if (s_id, r_id) not in room_slot_occupied
                    ]
                    if valid_rooms:
                        available_slots.append((slot, valid_rooms))

            available_slots.sort(
                key=lambda x: (
                    self._day_order.get(x[0].day, 99),
                    x[0].start_time,
                )
            )

            chosen_slot, chosen_rooms = available_slots[0]
            chosen_room_id = chosen_rooms[0]  # First available room

            # Lock assignment
            new_assign = Assignment(
                assignment_id=curr_assign.assignment_id,
                section_id=curr_assign.section_id,
                faculty_id=curr_assign.faculty_id,
                subject_code=curr_assign.subject_code,
                slot_id=chosen_slot.slot_id,
                room_id=chosen_room_id,
            )
            scheduled_assignments.append(new_assign)

            # Update occupied resources
            faculty_busy[curr_assign.faculty_id].add(chosen_slot.slot_id)
            section_busy[curr_assign.section_id].add(chosen_slot.slot_id)
            room_slot_occupied.add((chosen_slot.slot_id, chosen_room_id))

            # Forward-checking: remove the chosen slot from domain of
            # conflicting variables
            for other_id in unscheduled_queue:
                other = assignment_map[other_id]
                if (
                    other.faculty_id == curr_assign.faculty_id
                    or other.section_id == curr_assign.section_id
                ):
                    domains[other_id].discard(chosen_slot.slot_id)

        # Compute execution statistics
        end_time = time.perf_counter()
        runtime_ms = (end_time - start_time) * 1000.0

        total_to_schedule = len(unlocked_assignments)
        failed_count = len(unscheduled_assignments)

        if total_to_schedule > 0:
            success_rate = (total_to_schedule - failed_count) / total_to_schedule
        else:
            success_rate = 1.0

        stats = SchedulerStatistics(
            runtime_ms=runtime_ms,
            failed_count=failed_count,
            success_rate=success_rate,
        )

        partial_timetable = Timetable(
            assignments=scheduled_assignments + locked_assignments
        )

        return SchedulerResult(
            partial_timetable=partial_timetable,
            locked_assignments=locked_assignments,
            unscheduled_assignments=unscheduled_assignments,
            statistics=stats,
        )
