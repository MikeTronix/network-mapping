from datetime import datetime, timezone

from network_mapper.models import NetworkNode
from network_mapper.persistence import SnapshotWriter


def test_render_is_ascii_and_sorted():
    nodes = [
        NetworkNode(ip="192.168.1.20", mac="aa:bb:cc:00:00:20", hostname="zeta"),
        NetworkNode(ip="192.168.1.2", mac="aa:bb:cc:00:00:02", hostname="cafe-é"),
    ]

    text = SnapshotWriter().render(
        nodes,
        scanner_ip="192.168.1.10",
        scanner_mac="aa:bb:cc:00:00:10",
        subnet="192.168.1.0/24",
        timestamp=datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
    )

    assert text.isascii()
    assert "captured_at: 2025-01-02T03:04:05+00:00" in text
    assert "device_count: 2" in text
    assert text.index("ip: 192.168.1.2") < text.index("ip: 192.168.1.20")
    assert "hostname: cafe-\\xe9" in text


def test_write_creates_timestamped_ascii_file(tmp_path):
    node = NetworkNode(
        ip="192.168.1.2",
        mac="aa:bb:cc:00:00:02",
        services=["HTTP (Web Server)"],
        confidence_score=50,
    )
    timestamp = datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)

    path = SnapshotWriter(tmp_path).write(
        [node],
        scanner_ip="192.168.1.10",
        subnet="192.168.1.0/24",
        timestamp=timestamp,
    )

    assert path.name == "network_map_20250102_030405.txt"
    assert path.parent == tmp_path
    assert path.read_bytes().isascii()
    assert "services: HTTP (Web Server)" in path.read_text(encoding="ascii")


def test_write_does_not_overwrite_same_second(tmp_path):
    writer = SnapshotWriter(tmp_path)
    timestamp = datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    kwargs = {
        "nodes": [],
        "scanner_ip": "192.168.1.10",
        "subnet": "192.168.1.0/24",
        "timestamp": timestamp,
    }

    first = writer.write(**kwargs)
    second = writer.write(**kwargs)

    assert first.name == "network_map_20250102_030405.txt"
    assert second.name == "network_map_20250102_030405_1.txt"
    assert first.read_text(encoding="ascii") == second.read_text(encoding="ascii")
