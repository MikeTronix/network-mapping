"""Human-readable persistence for network discovery snapshots."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from network_mapper.models import NetworkNode


class SnapshotWriter:
    """Write network snapshots as portable ASCII text files."""

    def __init__(self, output_dir: str | Path = "snapshots") -> None:
        self.output_dir = Path(output_dir)

    @staticmethod
    def _ascii(value: object) -> str:
        """Keep output single-line and represent non-ASCII characters safely."""
        text = str(value).replace("\r", "\\r").replace("\n", "\\n")
        return text.encode("ascii", "backslashreplace").decode("ascii")

    def render(
        self,
        nodes: Iterable[NetworkNode],
        *,
        scanner_ip: str,
        subnet: str,
        scanner_mac: str = "Unknown",
        timestamp: datetime | None = None,
    ) -> str:
        """Render a deterministic, human-readable snapshot."""
        captured_at = timestamp or datetime.now().astimezone()
        node_list = list(nodes)
        lines = [
            "NETWORKMAPPER SNAPSHOT v1",
            f"captured_at: {captured_at.isoformat(timespec='seconds')}",
            f"scanner_ip: {self._ascii(scanner_ip)}",
            f"scanner_mac: {self._ascii(scanner_mac)}",
            f"subnet: {self._ascii(subnet)}",
            f"device_count: {len(node_list)}",
            "",
        ]

        for index, node in enumerate(sorted(node_list, key=lambda item: item.ip), 1):
            lines.extend([
                f"[device {index}]",
                f"ip: {self._ascii(node.ip)}",
                f"mac: {self._ascii(node.mac)}",
                f"hostname: {self._ascii(node.hostname)}",
                f"vendor: {self._ascii(node.vendor)}",
                f"role: {self._ascii(node.role)}",
                f"services: {self._ascii(', '.join(node.services) or 'None')}",
                f"confidence_score: {node.confidence_score}",
                "",
            ])

        return "\n".join(lines)

    def write(
        self,
        nodes: Iterable[NetworkNode],
        *,
        scanner_ip: str,
        subnet: str,
        scanner_mac: str = "Unknown",
        timestamp: datetime | None = None,
    ) -> Path:
        """Write a timestamped snapshot and return its path."""
        captured_at = timestamp or datetime.now().astimezone()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        stem = f"network_map_{captured_at.strftime('%Y%m%d_%H%M%S')}"
        path = self.output_dir / f"{stem}.txt"
        suffix = 1
        while path.exists():
            path = self.output_dir / f"{stem}_{suffix}.txt"
            suffix += 1
        path.write_text(
            self.render(
                nodes,
                scanner_ip=scanner_ip,
                subnet=subnet,
                scanner_mac=scanner_mac,
                timestamp=captured_at,
            ),
            encoding="ascii",
            errors="strict",
        )
        return path
