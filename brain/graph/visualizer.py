"""Visualizer for HanuPlanner Brain conflict graphs."""

from pathlib import Path

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for headless environments
import matplotlib.pyplot as plt
import networkx as nx


def export_png(graph: nx.Graph, path: str | Path) -> None:
    """Visualize the conflict graph and export it as a PNG file.

    Applies premium modern styling (vibrant color palettes, sleek layout).

    Args:
        graph: The networkx.Graph instance.
        path: Filepath to save the PNG image to.
    """
    plt.figure(figsize=(10, 8), dpi=150)
    plt.title("Conflict Graph Visualization", fontsize=16, fontweight="bold", pad=20)

    # Use spring layout for node positioning
    pos = nx.spring_layout(graph, k=0.5, iterations=50, seed=42)

    # Styling attributes
    node_color = "#4f46e5"  # Premium Indigo
    edge_color = "#cbd5e1"  # Slate Light Gray
    node_size = 500
    font_size = 8
    font_color = "#ffffff"

    # Draw nodes, edges, and labels
    nx.draw_networkx_nodes(
        graph,
        pos,
        node_color=node_color,
        node_size=node_size,
        edgecolors="#312e81",
        linewidths=1.5,
    )
    nx.draw_networkx_edges(graph, pos, edge_color=edge_color, width=1.0)
    nx.draw_networkx_labels(
        graph,
        pos,
        font_size=font_size,
        font_color=font_color,
        font_weight="bold",
    )

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(str(path), format="png", bbox_inches="tight")
    plt.close()
