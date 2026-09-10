from network_mapper.models import NetworkNode
from network_mapper.visualization import NetworkVisualizer


def make_nodes():
    return [
        NetworkNode(ip="192.168.1.20", mac="aa:20", hostname="printer", vendor="Acme", role="Printer"),
        NetworkNode(ip="192.168.1.30", mac="aa:30", hostname="Unknown", vendor="Unknown", role="Unknown"),
    ]


def test_build_graph_adds_scanner_and_device_edges():
    graph = NetworkVisualizer().build_graph(make_nodes(), scanner_ip="192.168.1.10")

    assert set(graph.nodes) == {"192.168.1.10", "192.168.1.20", "192.168.1.30"}
    assert set(graph.edges) == {
        ("192.168.1.10", "192.168.1.20"),
        ("192.168.1.10", "192.168.1.30"),
    }
    assert graph.nodes["192.168.1.20"]["label"] == "printer"
    assert graph.nodes["192.168.1.20"]["kind"] == "device"


def test_build_graph_filters_by_vendor_and_role():
    graph = NetworkVisualizer().build_graph(
        make_nodes(),
        scanner_ip="192.168.1.10",
        vendors={"Acme"},
        roles={"Printer"},
    )

    assert set(graph.nodes) == {"192.168.1.10", "192.168.1.20"}


def test_build_graph_can_hide_unidentified_devices():
    graph = NetworkVisualizer().build_graph(
        make_nodes(), scanner_ip="192.168.1.10", include_unknown=False
    )

    assert "192.168.1.30" not in graph


def test_tooltip_escapes_device_data():
    node = NetworkNode(
        ip="192.168.1.2", mac="aa", hostname="<router>", vendor="A&B", services=["HTTP"]
    )

    tooltip = NetworkVisualizer._tooltip(node)

    assert "&lt;router&gt;" in tooltip
    assert "A&amp;B" in tooltip


def test_render_writes_html(tmp_path):
    visualizer = NetworkVisualizer()
    graph = visualizer.build_graph([], scanner_ip="192.168.1.10")

    output = visualizer.render(graph, tmp_path / "map.html", physics=False)

    assert output.exists()
    assert "192.168.1.10" in output.read_text(encoding="utf-8")
