from network_mapper.models import NetworkNode


def test_network_node_defaults():
    node = NetworkNode(ip="192.168.1.5", mac="aa:bb:cc:dd:ee:ff")

    assert node.hostname == "Unknown"
    assert node.vendor == "Unknown"
    assert node.role == "Unknown"
    assert node.services == []
    assert node.confidence_score == 0


def test_network_nodes_do_not_share_service_lists():
    first = NetworkNode(ip="192.168.1.1", mac="aa:bb:cc:00:00:01")
    second = NetworkNode(ip="192.168.1.2", mac="aa:bb:cc:00:00:02")

    first.services.append("HTTP")

    assert second.services == []
