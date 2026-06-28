"""Tests for HanuPlanner Brain conflict graph analysis package."""

from pathlib import Path

import networkx as nx
import pytest

from brain.graph.builder import ConflictGraphBuilder
from brain.graph.metrics import (
    average_degree,
    clustering_coefficient,
    connected_components,
    density,
    export_adjacency_matrix,
    export_graphml,
)
from brain.graph.visualizer import export_png
from brain.models import Assignment, Timetable
from brain.models.exceptions import GraphBuildError

# Output directory for saving graphs and matrices
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def test_builder_empty_timetable() -> None:
    """Test building conflict graph from empty timetable."""
    t = Timetable(assignments=[])
    graph = ConflictGraphBuilder.build_graph(t)
    assert graph.number_of_nodes() == 0
    assert graph.number_of_edges() == 0


def test_builder_single_assignment() -> None:
    """Test building conflict graph with single assignment."""
    a = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S1",
        room_id="R1",
    )
    t = Timetable(assignments=[a])
    graph = ConflictGraphBuilder.build_graph(t)
    assert graph.number_of_nodes() == 1
    assert graph.number_of_edges() == 0
    assert "A1" in graph.nodes
    assert graph.nodes["A1"]["assignment"] == a
    
    # Save graph to output folder
    export_graphml(graph, OUTPUT_DIR / "single_assignment_graph.graphml")
    export_png(graph, OUTPUT_DIR / "single_assignment_graph.png")
    export_adjacency_matrix(graph, OUTPUT_DIR / "single_assignment_matrix.csv")


def test_builder_duplicate_ids_error() -> None:
    """Test building conflict graph with duplicate assignment IDs raises error."""
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S1",
        room_id="R1",
    )
    a2 = Assignment(
        assignment_id="A1",
        section_id="SEC_B",
        faculty_id="F2",
        subject_code="CS102",
        slot_id="S2",
        room_id="R2",
    )
    t = Timetable(assignments=[a1, a2])
    with pytest.raises(GraphBuildError) as exc_info:
        ConflictGraphBuilder.build_graph(t)
    assert "duplicate assignment IDs" in str(exc_info.value)


def test_builder_faculty_clash() -> None:
    """Test conflict detection due to shared faculty."""
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S1",
        room_id="R1",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_B",
        faculty_id="F1",
        subject_code="CS102",
        slot_id="S2",
        room_id="R2",
    )
    t = Timetable(assignments=[a1, a2])
    graph = ConflictGraphBuilder.build_graph(t)
    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 1
    assert graph.has_edge("A1", "A2")
    edge_data = graph["A1"]["A2"]
    assert edge_data["reason"] == "Share faculty 'F1'"
    assert edge_data["constraint_type"] == "hard"
    assert edge_data["weight"] == 1.0
    
    # Save graph to output folder
    export_graphml(graph, OUTPUT_DIR / "faculty_clash_graph.graphml")
    export_png(graph, OUTPUT_DIR / "faculty_clash_graph.png")
    export_adjacency_matrix(graph, OUTPUT_DIR / "faculty_clash_matrix.csv")


def test_builder_room_clash() -> None:
    """Test conflict detection due to shared room."""
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S1",
        room_id="R1",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_B",
        faculty_id="F2",
        subject_code="CS102",
        slot_id="S2",
        room_id="R1",
    )
    t = Timetable(assignments=[a1, a2])
    graph = ConflictGraphBuilder.build_graph(t)
    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 1
    assert graph.has_edge("A1", "A2")
    assert graph["A1"]["A2"]["reason"] == "Share room 'R1'"
    
    # Save graph to output folder
    export_graphml(graph, OUTPUT_DIR / "room_clash_graph.graphml")
    export_png(graph, OUTPUT_DIR / "room_clash_graph.png")
    export_adjacency_matrix(graph, OUTPUT_DIR / "room_clash_matrix.csv")


def test_builder_section_clash() -> None:
    """Test conflict detection due to shared section."""
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S1",
        room_id="R1",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_A",
        faculty_id="F2",
        subject_code="CS102",
        slot_id="S2",
        room_id="R2",
    )
    t = Timetable(assignments=[a1, a2])
    graph = ConflictGraphBuilder.build_graph(t)
    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 1
    assert graph.has_edge("A1", "A2")
    assert graph["A1"]["A2"]["reason"] == "Share section 'SEC_A'"
    
    # Save graph to output folder
    export_graphml(graph, OUTPUT_DIR / "section_clash_graph.graphml")
    export_png(graph, OUTPUT_DIR / "section_clash_graph.png")
    export_adjacency_matrix(graph, OUTPUT_DIR / "section_clash_matrix.csv")


def test_builder_multiple_clashes_reason_concatenation() -> None:
    """Test concatenation of reasons when multiple clashes occur between same nodes."""
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S1",
        room_id="R1",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS102",
        slot_id="S2",
        room_id="R1",
    )
    t = Timetable(assignments=[a1, a2])
    graph = ConflictGraphBuilder.build_graph(t)
    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 1
    reason = graph["A1"]["A2"]["reason"]
    assert "Share faculty 'F1'" in reason
    assert "Share room 'R1'" in reason
    assert "Share section 'SEC_A'" in reason
    
    # Save graph to output folder
    export_graphml(graph, OUTPUT_DIR / "multiple_clashes_graph.graphml")
    export_png(graph, OUTPUT_DIR / "multiple_clashes_graph.png")
    export_adjacency_matrix(graph, OUTPUT_DIR / "multiple_clashes_matrix.csv")


def test_builder_no_clashes() -> None:
    """Test building conflict graph with distinct resources does not create edges."""
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S1",
        room_id="R1",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_B",
        faculty_id="F2",
        subject_code="CS102",
        slot_id="S2",
        room_id="R2",
    )
    t = Timetable(assignments=[a1, a2])
    graph = ConflictGraphBuilder.build_graph(t)
    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 0
    
    # Save graph to output folder
    export_graphml(graph, OUTPUT_DIR / "no_clashes_graph.graphml")
    export_png(graph, OUTPUT_DIR / "no_clashes_graph.png")
    export_adjacency_matrix(graph, OUTPUT_DIR / "no_clashes_matrix.csv")


def test_metrics_connected_components_empty() -> None:
    """Test connected components calculation on empty graph."""
    g = nx.Graph()
    assert connected_components(g) == []


def test_metrics_connected_components_disconnected() -> None:
    """Test connected components on disconnected graph."""
    g = nx.Graph()
    g.add_node("A")
    g.add_node("B")
    comps = connected_components(g)
    assert len(comps) == 2
    assert ["A"] in comps
    assert ["B"] in comps


def test_metrics_connected_components_fully_connected() -> None:
    """Test connected components on fully connected graph."""
    g = nx.Graph()
    g.add_edge("A", "B")
    g.add_edge("B", "C")
    comps = connected_components(g)
    assert len(comps) == 1
    assert sorted(comps[0]) == ["A", "B", "C"]


def test_metrics_density_empty() -> None:
    """Test density on empty graph."""
    g = nx.Graph()
    assert density(g) == 0.0


def test_metrics_density_clique() -> None:
    """Test density on a fully connected clique."""
    g = nx.complete_graph(4)
    assert density(g) == 1.0


def test_metrics_average_degree_empty() -> None:
    """Test average degree on empty graph."""
    g = nx.Graph()
    assert average_degree(g) == 0.0


def test_metrics_average_degree_clique() -> None:
    """Test average degree on a clique."""
    g = nx.Graph()
    g.add_edge("A", "B")
    g.add_edge("B", "C")
    g.add_edge("C", "A")
    # Clique of 3 nodes, each has degree 2. Average degree = 2.0
    assert average_degree(g) == 2.0


def test_metrics_clustering_coefficient_small() -> None:
    """Test clustering coefficient on graphs with less than 3 nodes returns 0.0."""
    g1 = nx.Graph()
    assert clustering_coefficient(g1) == 0.0
    g2 = nx.Graph()
    g2.add_edge("A", "B")
    assert clustering_coefficient(g2) == 0.0


def test_metrics_clustering_coefficient_large() -> None:
    """Test clustering coefficient on larger graph."""
    g = nx.Graph()
    g.add_edge("A", "B")
    g.add_edge("B", "C")
    g.add_edge("C", "A")
    g.add_node("D")
    # Node D has coefficient 0. Clique A-B-C has coefficients 1.0
    assert clustering_coefficient(g) == 0.75


def test_exporter_graphml(tmp_path: Path) -> None:
    """Test exporting conflict graph to GraphML format."""
    a = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S1",
        room_id="R1",
    )
    t = Timetable(assignments=[a])
    graph = ConflictGraphBuilder.build_graph(t)

    file_path = tmp_path / "conflict_graph.graphml"
    export_graphml(graph, file_path)
    assert file_path.is_file()
    assert file_path.stat().st_size > 0


def test_exporter_png(tmp_path: Path) -> None:
    """Test exporting graph visualization to PNG."""
    a1 = Assignment(
        assignment_id="A1",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS101",
        slot_id="S1",
        room_id="R1",
    )
    a2 = Assignment(
        assignment_id="A2",
        section_id="SEC_A",
        faculty_id="F1",
        subject_code="CS102",
        slot_id="S2",
        room_id="R1",
    )
    t = Timetable(assignments=[a1, a2])
    graph = ConflictGraphBuilder.build_graph(t)

    file_path = tmp_path / "visualization.png"
    export_png(graph, file_path)
    assert file_path.is_file()
    assert file_path.stat().st_size > 0
