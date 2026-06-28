"""Metrics and exporters for HanuPlanner Brain conflict graphs."""

from pathlib import Path

import networkx as nx
import numpy as np


def connected_components(graph: nx.Graph) -> list[list[str]]:
    """Get the connected components of the conflict graph.

    Args:
        graph: The networkx.Graph instance.

    Returns:
        A list of lists, where each inner list contains the assignment IDs
        belonging to a connected component.
    """
    return [list(comp) for comp in nx.connected_components(graph)]


def density(graph: nx.Graph) -> float:
    """Calculate the density of the conflict graph.

    Args:
        graph: The networkx.Graph instance.

    Returns:
        The density of the graph as a float.
    """
    return float(nx.density(graph))


def average_degree(graph: nx.Graph) -> float:
    """Calculate the average degree of nodes in the conflict graph.

    Args:
        graph: The networkx.Graph instance.

    Returns:
        The average degree as a float.
    """
    num_nodes = graph.number_of_nodes()
    if num_nodes == 0:
        return 0.0
    total_degree = sum(dict(graph.degree()).values())
    return float(total_degree / num_nodes)


def clustering_coefficient(graph: nx.Graph) -> float:
    """Calculate the average clustering coefficient of the conflict graph.

    Args:
        graph: The networkx.Graph instance.

    Returns:
        The average clustering coefficient as a float.
    """
    if graph.number_of_nodes() < 3:
        return 0.0
    return float(nx.average_clustering(graph))


def export_graphml(graph: nx.Graph, path: str | Path) -> None:
    """Export the conflict graph in GraphML format.

    Bypasses complex Pydantic model serialization issues by stripping
    complex attributes before writing.

    Args:
        graph: The networkx.Graph instance.
        path: Filepath to write the GraphML file to.
    """
    # Create a copy of the graph and strip complex attributes to prevent XML
    # writer crash.
    temp_graph = graph.copy()
    for node in temp_graph.nodes:
        if "assignment" in temp_graph.nodes[node]:
            del temp_graph.nodes[node]["assignment"]
    nx.write_graphml(temp_graph, str(path))


def export_adjacency_matrix(graph: nx.Graph, path: str | Path) -> None:
    """Export the adjacency matrix of the conflict graph to a file.

    Args:
        graph: The networkx.Graph instance.
        path: Filepath to write the adjacency matrix to (supports .npy, .csv, .txt).
    """
    adjacency_matrix = nx.to_numpy_array(graph)
    path_str = str(path)

    if path_str.endswith(".npy"):
        np.save(path_str, adjacency_matrix)
    elif path_str.endswith(".csv"):
        import pandas as pd

        node_names = list(graph.nodes())
        df = pd.DataFrame(adjacency_matrix, index=node_names, columns=node_names)
        df.to_csv(path_str)
    else:
        np.savetxt(path_str, adjacency_matrix, fmt="%d")
