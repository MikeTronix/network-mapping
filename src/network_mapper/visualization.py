"""Network graph construction and interactive HTML rendering."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Iterable

import networkx as nx
from pyvis.network import Network

from network_mapper.models import NetworkNode


class NetworkVisualizer:
    """Build and render a scanner-centric network graph."""

    ROLE_COLORS = {
        "Printer": "#f59e0b",
        "Windows Machine": "#2563eb",
        "Linux/Network Device": "#16a34a",
        "Web-Enabled Device": "#9333ea",
    }
    DEFAULT_COLOR = "#64748b"

    def build_graph(
        self,
        nodes: Iterable[NetworkNode],
        *,
        scanner_ip: str,
        vendors: set[str] | None = None,
        roles: set[str] | None = None,
        include_unknown: bool = True,
    ) -> nx.Graph:
        """Build a graph using known scanner-to-device links.

        Discovery currently establishes device presence, not switch-port topology,
        so edges intentionally represent reachability from the scanning host.
        """
        graph = nx.Graph()
        graph.add_node(scanner_ip, label=f"Scanner\n{scanner_ip}", kind="scanner", color="#dc2626")

        for node in nodes:
            if vendors and node.vendor not in vendors:
                continue
            if roles and node.role not in roles:
                continue
            if not include_unknown and node.hostname == "Unknown" and node.vendor == "Unknown":
                continue

            label = node.hostname if node.hostname != "Unknown" else node.ip
            graph.add_node(
                node.ip,
                label=label,
                title=self._tooltip(node),
                kind="device",
                color=self.ROLE_COLORS.get(node.role, self.DEFAULT_COLOR),
                size=max(12, min(45, 12 + node.confidence_score // 4)),
            )
            graph.add_edge(scanner_ip, node.ip)

        return graph

    @staticmethod
    def _tooltip(node: NetworkNode) -> str:
        """Create an escaped tooltip suitable for insertion into HTML."""
        services = ", ".join(node.services) or "None"
        return (
            f"IP: {escape(node.ip)}<br>"
            f"MAC: {escape(node.mac)}<br>"
            f"Name: {escape(node.hostname)}<br>"
            f"Vendor: {escape(node.vendor)}<br>"
            f"Role: {escape(node.role)}<br>"
            f"Services: {escape(services)}<br>"
            f"Confidence: {node.confidence_score}/100"
        )

    def render(
        self,
        graph: nx.Graph,
        output_path: str | Path,
        *,
        height: str = "900px",
        width: str = "100%",
        physics: bool = True,
    ) -> Path:
        """Render a graph to a self-contained interactive HTML file."""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        network = Network(height=height, width=width, directed=False, notebook=False)
        network.from_nx(graph)
        network.toggle_physics(physics)
        network.set_options(
            '{"interaction":{"hover":true,"navigationButtons":true},'
            '"physics":{"stabilization":{"iterations":300}}}'
        )
        network.write_html(str(output), open_browser=False)
        return output
