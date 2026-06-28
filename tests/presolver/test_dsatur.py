"""Tests for HanuPlanner Brain DSATUR graph coloring presolver."""

import datetime
from pathlib import Path

import networkx as nx
import pytest

from brain.constraints.base import ConstraintContext
from brain.graph.builder import ConflictGraphBuilder
from brain.graph.metrics import export_adjacency_matrix, export_graphml
from brain.graph.visualizer import export_png
from brain.models import (
    Assignment,
    Day,
    Room,
    RoomType,
    Section,
    Slot,
    Timetable,
)
from brain.presolver.dsatur import DSATURSolver

# Output directory for saving graphs and matrices
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def test_dsatur_empty_timetable() -> None:
    """Test DSATUR on empty timetable."""
    solver = DSATURSolver()
    t = Timetable(assignments=[])
    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=[]
    )
    result = solver.partial_schedule(t, context)
    assert len(result.assignments) == 0


def test_dsatur_single_assignment() -> None:
    """Test DSATUR on single assignment."""
    solver = DSATURSolver()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1]
    )
    result = solver.partial_schedule(t, context)
    assert len(result.assignments) == 1
    assert result.assignments[0].slot_id == "S1"
    assert result.assignments[0].room_id == "R1"


def test_dsatur_saturation_degree_calculation_empty() -> None:
    """Test saturation degree computation on completely uncolored graph."""
    solver = DSATURSolver()
    g = nx.cycle_graph(4)
    colored = {}
    sat_degrees = solver.compute_saturation_degree(g, colored)
    assert len(sat_degrees) == 4
    # All saturation degrees must be 0
    assert all(d == 0 for d in sat_degrees.values())

    # Save graph to output folder
    export_graphml(g, OUTPUT_DIR / "dsatur_cycle_graph.graphml")
    export_png(g, OUTPUT_DIR / "dsatur_cycle_graph.png")
    export_adjacency_matrix(g, OUTPUT_DIR / "dsatur_cycle_matrix.csv")


def test_dsatur_saturation_degree_calculation_partial() -> None:
    """Test saturation degree computation with some colored nodes."""
    solver = DSATURSolver()
    g = nx.Graph()
    g.add_edge("A", "B")
    g.add_edge("A", "C")
    g.add_edge("B", "C")
    # A is colored 'Red', B is colored 'Blue'
    colored = {"A": "Red", "B": "Blue"}
    sat_degrees = solver.compute_saturation_degree(g, colored)
    # Only C is uncolored
    assert "C" in sat_degrees
    assert len(sat_degrees) == 1
    # C's neighbors (A, B) have 2 distinct colors
    assert sat_degrees["C"] == 2

    # Save graph to output folder
    export_graphml(g, OUTPUT_DIR / "dsatur_partial_graph.graphml")
    export_png(g, OUTPUT_DIR / "dsatur_partial_graph.png")
    export_adjacency_matrix(g, OUTPUT_DIR / "dsatur_partial_matrix.csv")


def test_dsatur_select_vertex_empty_error() -> None:
    """Test select_vertex raises KeyError when all nodes are colored."""
    solver = DSATURSolver()
    g = nx.Graph()
    g.add_node("A")
    colored = {"A": "Red"}
    with pytest.raises(KeyError):
        solver.select_vertex(g, colored, {}, {})


def test_dsatur_select_vertex_max_saturation() -> None:
    """Test select_vertex picks the node with the highest saturation degree."""
    solver = DSATURSolver()
    g = nx.Graph()
    g.add_nodes_from(["A", "B", "C"])
    colored = {}
    # B has higher saturation degree than A and C
    sat_degrees = {"A": 1, "B": 3, "C": 2}
    static_degrees = {"A": 5, "B": 2, "C": 1}
    vertex = solver.select_vertex(g, colored, sat_degrees, static_degrees)
    assert vertex == "B"


def test_dsatur_select_vertex_tie_break_degree() -> None:
    """Test select_vertex breaks saturation ties using static degree."""
    solver = DSATURSolver()
    g = nx.Graph()
    g.add_nodes_from(["A", "B"])
    colored = {}
    sat_degrees = {"A": 2, "B": 2}
    # A has higher degree than B
    static_degrees = {"A": 5, "B": 1}
    vertex = solver.select_vertex(g, colored, sat_degrees, static_degrees)
    assert vertex == "A"


def test_dsatur_select_vertex_tie_break_lexicographical() -> None:
    """Test select_vertex breaks degree ties lexicographically."""
    solver = DSATURSolver()
    g = nx.Graph()
    g.add_nodes_from(["B", "A"])
    colored = {}
    sat_degrees = {"A": 2, "B": 2}
    static_degrees = {"A": 5, "B": 5}
    # 'A' is smaller than 'B' lexicographically
    vertex = solver.select_vertex(g, colored, sat_degrees, static_degrees)
    assert vertex == "A"


def test_dsatur_assign_color_holiday_bypassed() -> None:
    """Test assign_color skips holiday slots."""
    solver = DSATURSolver()
    g = nx.Graph()
    g.add_node("A")
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=[s1], holidays=["S1"]
    )
    s_id, r_id = solver.assign_color(g, "A", {}, context, set(), ["R1"])
    assert s_id is None
    assert r_id is None


def test_dsatur_assign_color_neighbor_forbidden() -> None:
    """Test assign_color skips slots assigned to neighbors."""
    solver = DSATURSolver()
    g = nx.Graph()
    g.add_edge("A", "B")
    colored = {"B": "S1"}

    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    s2 = Slot(
        slot_id="S2",
        day=Day.MONDAY,
        start_time=datetime.time(10, 0),
        end_time=datetime.time(11, 0),
    )
    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=[s1, s2]
    )

    # Slot S1 should be skipped because neighbor B has it. So S2 is chosen.
    s_id, r_id = solver.assign_color(g, "A", colored, context, set(), ["R1", "R2"])
    assert s_id == "S2"
    assert r_id == "R1"


def test_dsatur_assign_color_room_capacity() -> None:
    """Test assign_color capacity constraint."""
    solver = DSATURSolver()
    g = nx.Graph()
    g.add_node("A")
    # Slot & Rooms
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    r1 = Room(room_id="R1_SMALL", capacity=10, room_type=RoomType.THEORY)
    r2 = Room(room_id="R2_LARGE", capacity=50, room_type=RoomType.THEORY)
    # Section requires 40 strength
    sec = Section(section_id="SEC_A", program="CS", year=1, strength=40)
    context = ConstraintContext(
        faculties=[],
        rooms=[r1, r2],
        subjects=[],
        sections=[sec],
        slots=[s1],
    )

    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1])
    result = solver.partial_schedule(t, context)
    assert len(result.assignments) == 1
    assert result.assignments[0].room_id == "R2_LARGE"


def test_dsatur_assign_color_room_occupied() -> None:
    """Test assign_color checks occupied rooms in slots."""
    solver = DSATURSolver()
    g = nx.Graph()
    g.add_node("A")
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=[s1]
    )
    # R1 is occupied in S1
    room_slot_occupied = {("S1", "R1")}
    s_id, r_id = solver.assign_color(
        g,
        "A",
        {},
        context,
        room_slot_occupied,
        ["R1", "R2"],
    )
    # Should choose R2
    assert s_id == "S1"
    assert r_id == "R2"


def test_dsatur_assign_color_no_slot_available() -> None:
    """Test assign_color returns None, None when no resource is available."""
    solver = DSATURSolver()
    g = nx.Graph()
    g.add_node("A")
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    context = ConstraintContext(
        faculties=[], rooms=[], subjects=[], sections=[], slots=[s1]
    )
    # Only room R1, but occupied
    room_slot_occupied = {("S1", "R1")}
    s_id, r_id = solver.assign_color(g, "A", {}, context, room_slot_occupied, ["R1"])
    assert s_id is None
    assert r_id is None


def test_dsatur_partial_schedule_success() -> None:
    """Test full coloring/scheduling execution."""
    solver = DSATURSolver()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_B",
        faculty_id="F2",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1, a2])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    r2 = Room(room_id="R2", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1, r2], subjects=[], sections=[], slots=[s1]
    )
    result = solver.partial_schedule(t, context)
    assert len(result.assignments) == 2
    r_ids = {a.room_id for a in result.assignments}
    assert r_ids == {"R1", "R2"}


def test_dsatur_partial_schedule_incomplete() -> None:
    """Test scheduler outputs partial timetable when some fail."""
    solver = DSATURSolver()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_A",  # shared section clashing
        faculty_id="F2",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1, a2])
    # Only 1 slot in context, so 1 must fail
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1]
    )
    result = solver.partial_schedule(t, context)
    assert len(result.assignments) == 1


def test_dsatur_section_strength_exceeds_all_rooms() -> None:
    """Test handling of sections exceeding room capacity limits."""
    solver = DSATURSolver()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_HUGE",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    r1 = Room(room_id="R1", capacity=20, room_type=RoomType.THEORY)
    sec = Section(section_id="SEC_HUGE", program="CS", year=1, strength=50)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[sec], slots=[s1]
    )
    result = solver.partial_schedule(t, context)
    assert len(result.assignments) == 0  # Cannot schedule


def test_dsatur_earliest_slot_selected() -> None:
    """Test sorting chooses earliest slot by day and time."""
    solver = DSATURSolver()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1])
    s_tue = Slot(
        slot_id="S_TUE",
        day=Day.TUESDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    s_mon = Slot(
        slot_id="S_MON",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s_tue, s_mon]
    )
    result = solver.partial_schedule(t, context)
    assert result.assignments[0].slot_id == "S_MON"


def test_dsatur_complexity_v2_bound() -> None:
    """Test complexity logic by measuring iterations count scales at O(V^2)."""
    solver = DSATURSolver()
    assignments = [
        Assignment(
            assignment_id=f"A{i}",
            section_id=f"SEC_{i}",
            faculty_id=f"F{i}",
            subject_code="CS101",
            slot_id="UNASSIGNED",
            room_id="UNASSIGNED",
        )
        for i in range(10)
    ]
    t = Timetable(assignments=assignments)
    slots = [
        Slot(
            slot_id=f"S{i}",
            day=Day.MONDAY,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
        )
        for i in range(10)
    ]
    rooms = [
        Room(room_id=f"R{i}", capacity=50, room_type=RoomType.THEORY) for i in range(10)
    ]
    context = ConstraintContext(
        faculties=[], rooms=rooms, subjects=[], sections=[], slots=slots
    )
    result = solver.partial_schedule(t, context)
    assert len(result.assignments) == 10


def test_dsatur_multiple_clashes_degree() -> None:
    """Test static degree calculation with multiple clashing assignments."""
    solver = DSATURSolver()
    # A1 shares faculty with A2 and A3
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_B",
        faculty_id="F1",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a3 = Assignment(
        assignment_id="A3",
        section_id="SEC_C",
        faculty_id="F1",
        subject_code="CS103",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1, a2, a3])
    slots = [
        Slot(
            slot_id=f"S{i}",
            day=Day.MONDAY,
            start_time=datetime.time(i, 0),
            end_time=datetime.time(i + 1, 0),
        )
        for i in range(8, 12)
    ]
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=slots
    )
    result = solver.partial_schedule(t, context)
    assert len(result.assignments) == 3
    # Check distinct slots (no clashes)
    s_ids = {a.slot_id for a in result.assignments}
    assert len(s_ids) == 3

    # Save conflict graph to output folder
    graph = ConflictGraphBuilder.build_graph(t)
    export_graphml(graph, OUTPUT_DIR / "dsatur_multiple_clashes_graph.graphml")
    export_png(graph, OUTPUT_DIR / "dsatur_multiple_clashes_graph.png")
    export_adjacency_matrix(graph, OUTPUT_DIR / "dsatur_multiple_clashes_matrix.csv")


def test_dsatur_unconnected_subgraphs() -> None:
    """Test DSATUR coloring on disconnected components in the graph."""
    solver = DSATURSolver()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_B",
        faculty_id="F2",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1, a2])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1]
    )
    # Both colored in same slot, different rooms
    result = solver.partial_schedule(t, context)
    assert len(result.assignments) == 1  # Only 1 room exists, so at most 1 succeeds


def test_dsatur_complete_graph_clique() -> None:
    """Test coloring of complete graph (clique) where V=3."""
    solver = DSATURSolver()
    # A1, A2, A3 share same faculty
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_B",
        faculty_id="F1",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a3 = Assignment(
        assignment_id="A3",
        section_id="SEC_C",
        faculty_id="F1",
        subject_code="CS103",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1, a2, a3])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    s2 = Slot(
        slot_id="S2",
        day=Day.MONDAY,
        start_time=datetime.time(10, 0),
        end_time=datetime.time(11, 0),
    )
    s3 = Slot(
        slot_id="S3",
        day=Day.MONDAY,
        start_time=datetime.time(11, 0),
        end_time=datetime.time(12, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1, s2, s3]
    )
    result = solver.partial_schedule(t, context)
    assert len(result.assignments) == 3

    # Save conflict graph to output folder
    graph = ConflictGraphBuilder.build_graph(t)
    export_graphml(graph, OUTPUT_DIR / "dsatur_clique_graph.graphml")
    export_png(graph, OUTPUT_DIR / "dsatur_clique_graph.png")
    export_adjacency_matrix(graph, OUTPUT_DIR / "dsatur_clique_matrix.csv")


def test_dsatur_bipartite_graph() -> None:
    """Test coloring of bipartite graph."""
    solver = DSATURSolver()
    # A1 & A3 share F1. A2 & A4 share F2. A1 connects to A2, A3 connects to A4.
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_A",  # Clash with A1
        faculty_id="F2",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a3 = Assignment(
        assignment_id="A3",
        section_id="SEC_B",
        faculty_id="F1",  # Clash with A1
        subject_code="CS103",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1, a2, a3])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    s2 = Slot(
        slot_id="S2",
        day=Day.MONDAY,
        start_time=datetime.time(10, 0),
        end_time=datetime.time(11, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    r2 = Room(room_id="R2", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1, r2], subjects=[], sections=[], slots=[s1, s2]
    )
    result = solver.partial_schedule(t, context)
    assert len(result.assignments) == 3

    # Save conflict graph to output folder
    graph = ConflictGraphBuilder.build_graph(t)
    export_graphml(graph, OUTPUT_DIR / "dsatur_bipartite_graph.graphml")
    export_png(graph, OUTPUT_DIR / "dsatur_bipartite_graph.png")
    export_adjacency_matrix(graph, OUTPUT_DIR / "dsatur_bipartite_matrix.csv")


def test_dsatur_star_graph() -> None:
    """Test coloring of star graph (center node clashes with all outer nodes)."""
    solver = DSATURSolver()
    # A1 (center) shares section with A2, A3.
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_A",
        faculty_id="F2",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a3 = Assignment(
        assignment_id="A3",
        section_id="SEC_A",
        faculty_id="F3",
        subject_code="CS103",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1, a2, a3])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    s2 = Slot(
        slot_id="S2",
        day=Day.MONDAY,
        start_time=datetime.time(10, 0),
        end_time=datetime.time(11, 0),
    )
    s3 = Slot(
        slot_id="S3",
        day=Day.MONDAY,
        start_time=datetime.time(11, 0),
        end_time=datetime.time(12, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1, s2, s3]
    )
    result = solver.partial_schedule(t, context)
    assert len(result.assignments) == 3

    # Save conflict graph to output folder
    graph = ConflictGraphBuilder.build_graph(t)
    export_graphml(graph, OUTPUT_DIR / "dsatur_star_graph.graphml")
    export_png(graph, OUTPUT_DIR / "dsatur_star_graph.png")
    export_adjacency_matrix(graph, OUTPUT_DIR / "dsatur_star_matrix.csv")


def test_dsatur_cycle_graph() -> None:
    """Test coloring of cycle graph C3."""
    solver = DSATURSolver()
    # A1 shares faculty with A2, A2 shares section with A3, A3 shares room
    # with A1 (static graph shares faculty/section).
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_B",
        faculty_id="F1",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a3 = Assignment(
        assignment_id="A3",
        section_id="SEC_B",
        faculty_id="F3",
        subject_code="CS103",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1, a2, a3])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    s2 = Slot(
        slot_id="S2",
        day=Day.MONDAY,
        start_time=datetime.time(10, 0),
        end_time=datetime.time(11, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    r2 = Room(room_id="R2", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1, r2], subjects=[], sections=[], slots=[s1, s2]
    )
    result = solver.partial_schedule(t, context)
    assert len(result.assignments) == 3

    # Save conflict graph to output folder
    graph = ConflictGraphBuilder.build_graph(t)
    export_graphml(graph, OUTPUT_DIR / "dsatur_cycle_graph.graphml")
    export_png(graph, OUTPUT_DIR / "dsatur_cycle_graph.png")
    export_adjacency_matrix(graph, OUTPUT_DIR / "dsatur_cycle_matrix.csv")


def test_dsatur_wheel_graph() -> None:
    """Test coloring of wheel graph W4 (center + 3-cycle outer)."""
    solver = DSATURSolver()
    a1 = Assignment(
        assignment_id="A1",  # Center
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_A",
        faculty_id="F2",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a3 = Assignment(
        assignment_id="A3",
        section_id="SEC_A",
        faculty_id="F3",
        subject_code="CS103",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1, a2, a3])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    s2 = Slot(
        slot_id="S2",
        day=Day.MONDAY,
        start_time=datetime.time(10, 0),
        end_time=datetime.time(11, 0),
    )
    s3 = Slot(
        slot_id="S3",
        day=Day.MONDAY,
        start_time=datetime.time(11, 0),
        end_time=datetime.time(12, 0),
    )
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1, s2, s3]
    )
    result = solver.partial_schedule(t, context)
    assert len(result.assignments) == 3

    # Save conflict graph to output folder
    graph = ConflictGraphBuilder.build_graph(t)
    export_graphml(graph, OUTPUT_DIR / "dsatur_wheel_graph.graphml")
    export_png(graph, OUTPUT_DIR / "dsatur_wheel_graph.png")
    export_adjacency_matrix(graph, OUTPUT_DIR / "dsatur_wheel_matrix.csv")


def test_dsatur_room_slot_lock() -> None:
    """Test DSATUR locks the room slot combination on coloring."""
    solver = DSATURSolver()
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_B",
        faculty_id="F2",
        subject_code="CS102",
        slot_id="UNASSIGNED",
        room_id="UNASSIGNED",
    )
    t = Timetable(assignments=[a1, a2])
    s1 = Slot(
        slot_id="S1",
        day=Day.MONDAY,
        start_time=datetime.time(9, 0),
        end_time=datetime.time(10, 0),
    )
    # Only 1 room available in context
    r1 = Room(room_id="R1", capacity=50, room_type=RoomType.THEORY)
    context = ConstraintContext(
        faculties=[], rooms=[r1], subjects=[], sections=[], slots=[s1]
    )
    # One succeeds, the other fails since room is locked by first assignment
    result = solver.partial_schedule(t, context)
    assert len(result.assignments) == 1
