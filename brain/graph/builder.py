"""Builder for HanuPlanner Brain conflict and constraint graphs."""

from collections import defaultdict

import networkx as nx

from brain.models.exceptions import GraphBuildError
from brain.models.timetable import Timetable


class ConflictGraphBuilder:
    """Builder class to construct conflict graphs from timetables."""

    @staticmethod
    def build_graph(timetable: Timetable) -> nx.Graph:
        """Build a conflict graph from a timetable's assignments.

        Nodes in the graph represent assignment IDs.
        Edges represent conflicts due to shared resources (faculty, room, section).

        Args:
            timetable: The Timetable instance containing assignments.

        Returns:
            A networkx.Graph representing the conflict graph.

        Raises:
            GraphBuildError: If duplicate assignment IDs are found.
        """
        # Validate unique assignment IDs
        assignment_ids = [a.assignment_id for a in timetable.assignments]
        if len(assignment_ids) != len(set(assignment_ids)):
            raise GraphBuildError("Timetable contains duplicate assignment IDs.")

        graph = nx.Graph()

        # Add all assignments as nodes
        for assignment in timetable.assignments:
            graph.add_node(assignment.assignment_id, assignment=assignment)

        # Group assignments by faculty, room, and section
        faculty_groups: dict[str, list[str]] = defaultdict(list)
        room_groups: dict[str, list[str]] = defaultdict(list)
        section_groups: dict[str, list[str]] = defaultdict(list)

        for assignment in timetable.assignments:
            faculty_groups[assignment.faculty_id].append(assignment.assignment_id)
            room_groups[assignment.room_id].append(assignment.assignment_id)
            section_groups[assignment.section_id].append(assignment.assignment_id)

        # Helper to add/update conflict edges
        def add_conflict_edge(u: str, v: str, reason: str) -> None:
            if graph.has_edge(u, v):
                # Update existing edge reason
                graph[u][v]["reason"] += f"; {reason}"
            else:
                graph.add_edge(
                    u,
                    v,
                    reason=reason,
                    constraint_type="hard",
                    weight=1.0,
                )

        # Add faculty conflict edges
        for fac_id, assign_ids in faculty_groups.items():
            n = len(assign_ids)
            for i in range(n):
                for j in range(i + 1, n):
                    add_conflict_edge(
                        assign_ids[i],
                        assign_ids[j],
                        f"Share faculty '{fac_id}'",
                    )

        # Add room conflict edges
        for room_id, assign_ids in room_groups.items():
            n = len(assign_ids)
            for i in range(n):
                for j in range(i + 1, n):
                    add_conflict_edge(
                        assign_ids[i], assign_ids[j], f"Share room '{room_id}'"
                    )

        # Add section conflict edges
        for sec_id, assign_ids in section_groups.items():
            n = len(assign_ids)
            for i in range(n):
                for j in range(i + 1, n):
                    add_conflict_edge(
                        assign_ids[i],
                        assign_ids[j],
                        f"Share section '{sec_id}'",
                    )

        return graph
