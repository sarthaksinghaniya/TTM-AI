"""DSATUR graph coloring presolver for HanuPlanner Brain."""

from typing import ClassVar

import networkx as nx

from brain.constraints.base import ConstraintContext
from brain.graph.builder import ConflictGraphBuilder
from brain.models import Assignment, Day, Timetable


class DSATURSolver:
    """DSATUR solver mapping graph coloring to timetabling."""

    _day_order: ClassVar[dict[Day, int]] = {
        Day.MONDAY: 1,
        Day.TUESDAY: 2,
        Day.WEDNESDAY: 3,
        Day.THURSDAY: 4,
        Day.FRIDAY: 5,
        Day.SATURDAY: 6,
        Day.SUNDAY: 7,
    }

    def compute_saturation_degree(
        self, graph: nx.Graph, colored: dict[str, str]
    ) -> dict[str, int]:
        """Compute the saturation degree for each uncolored node in the graph.

        Args:
            graph: The networkx.Graph representing conflicts.
            colored: Dict mapping node IDs to color/slot IDs.

        Returns:
            Dict mapping uncolored node IDs to their saturation degree.
        """
        saturation_degrees = {}
        for node in graph.nodes:
            if node in colored:
                continue
            neighbor_colors = {
                colored[nbr] for nbr in graph.neighbors(node) if nbr in colored
            }
            saturation_degrees[node] = len(neighbor_colors)
        return saturation_degrees

    def select_vertex(
        self,
        graph: nx.Graph,
        colored: dict[str, str],
        saturation_degrees: dict[str, int],
        static_degrees: dict[str, int],
    ) -> str:
        """Select the next vertex to color based on DSATUR heuristics.

        Selects the uncolored node with:
        1. Highest saturation degree.
        2. Tie-break: Highest static degree in conflict graph.
        3. Tie-break: Lexicographical order of node ID.

        Args:
            graph: The networkx.Graph.
            colored: Dict of currently colored nodes.
            saturation_degrees: Dict of saturation degrees.
            static_degrees: Dict of static degrees.

        Returns:
            The selected vertex (assignment_id) as a string.

        Raises:
            KeyError: If there are no uncolored vertices.
        """
        uncolored = [n for n in graph.nodes if n not in colored]
        if not uncolored:
            raise KeyError("No uncolored vertices remaining.")

        selected = min(
            uncolored,
            key=lambda uid: (
                -saturation_degrees.get(uid, 0),
                -static_degrees.get(uid, 0),
                uid,
            ),
        )
        return str(selected)

    def assign_color(
        self,
        graph: nx.Graph,
        vertex: str,
        colored: dict[str, str],
        context: ConstraintContext,
        room_slot_occupied: set[tuple[str, str]],
        candidate_rooms: list[str],
    ) -> tuple[str | None, str | None]:
        """Find the earliest feasible slot (color) and assign a room.

        Args:
            graph: The networkx.Graph.
            vertex: The vertex to color.
            colored: Dict of currently colored nodes.
            context: ConstraintContext context holding slots/rooms.
            room_slot_occupied: Occupied room slot tracking set.
            candidate_rooms: Rooms matching section strength.

        Returns:
            Tuple of (assigned slot ID, assigned room ID), or (None, None).
        """
        # Find forbidden colors from neighbors
        forbidden_slots = {
            colored[nbr] for nbr in graph.neighbors(vertex) if nbr in colored
        }

        # Filter slots to exclude holidays
        holidays_set = set(context.holidays)
        base_slots = [s for s in context.slots if s.slot_id not in holidays_set]

        # Sort slots by Day order and then Start Time
        sorted_slots = sorted(
            base_slots,
            key=lambda s: (
                self._day_order.get(s.day, 99),
                s.start_time,
            ),
        )

        for slot in sorted_slots:
            s_id = slot.slot_id
            if s_id in forbidden_slots:
                continue

            # Look for an available room in this slot
            for r_id in candidate_rooms:
                if (s_id, r_id) not in room_slot_occupied:
                    # Feasible! Lock room-slot combination
                    room_slot_occupied.add((s_id, r_id))
                    return s_id, r_id

        return None, None

    def partial_schedule(
        self, timetable: Timetable, context: ConstraintContext
    ) -> Timetable:
        """Construct a partial schedule for unlocked assignments using DSATUR.

        Args:
            timetable: The input Timetable template.
            context: The ConstraintContext dataset.

        Returns:
            A Timetable containing successfully scheduled assignments.
        """
        # Group sections for capacity checks
        section_map = {s.section_id: s for s in context.sections}

        # Setup candidate rooms matching section strength
        candidate_rooms_map: dict[str, list[str]] = {}
        for a in timetable.assignments:
            sec = section_map.get(a.section_id)
            strength = sec.strength if sec else 0
            candidate_rooms_map[a.assignment_id] = [
                r.room_id for r in context.rooms if r.capacity >= strength
            ]

        # Build conflict graph (shared faculty/section) using temp timetable
        temp_assignments = [
            Assignment.model_construct(
                assignment_id=a.assignment_id,
                section_id=a.section_id,
                faculty_id=a.faculty_id,
                subject_code=a.subject_code,
                slot_id="TEMP_SLOT",
                room_id=f"TEMP_ROOM_{idx}",
            )
            for idx, a in enumerate(timetable.assignments)
        ]
        temp_timetable = Timetable(assignments=temp_assignments)
        conflict_graph = ConflictGraphBuilder.build_graph(temp_timetable)
        static_degrees = dict(conflict_graph.degree())

        colored: dict[str, str] = {}  # maps assignment_id to slot_id
        colored_rooms: dict[str, str] = {}  # maps assignment_id to room_id
        room_slot_occupied: set[tuple[str, str]] = set()

        uncolored_queue = set(conflict_graph.nodes)

        while uncolored_queue:
            # Saturation degrees calculation
            saturation_degrees = self.compute_saturation_degree(conflict_graph, colored)

            # Vertex selection
            curr_id = self.select_vertex(
                conflict_graph,
                colored,
                saturation_degrees,
                static_degrees,
            )
            uncolored_queue.remove(curr_id)

            # Find feasible slot and room
            assigned_slot, assigned_room = self.assign_color(
                conflict_graph,
                curr_id,
                colored,
                context,
                room_slot_occupied,
                candidate_rooms_map[curr_id],
            )

            if assigned_slot and assigned_room:
                colored[curr_id] = assigned_slot
                colored_rooms[curr_id] = assigned_room

        # Re-build output list of successfully scheduled assignments
        scheduled_assignments = []
        for a in timetable.assignments:
            a_id = a.assignment_id
            if a_id in colored:
                scheduled_assignments.append(
                    Assignment(
                        assignment_id=a_id,
                        section_id=a.section_id,
                        faculty_id=a.faculty_id,
                        subject_code=a.subject_code,
                        slot_id=colored[a_id],
                        room_id=colored_rooms[a_id],
                    )
                )

        return Timetable(assignments=scheduled_assignments)
