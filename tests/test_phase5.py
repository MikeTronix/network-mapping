import ipaddress

from main import build_parser, main
from network_mapper.discovery import NetworkDiscovery
from network_mapper.identification import NetworkIdentifier
from network_mapper.models import NetworkNode


def test_cli_accepts_scan_configuration():
    args = build_parser().parse_args([
        "--subnet", "10.0.0.0/28", "--workers", "4", "--skip-icmp"
    ])

    assert args.subnet == "10.0.0.0/28"
    assert args.workers == 4
    assert args.skip_icmp is True


def test_main_rejects_invalid_subnet(capsys):
    assert main(["--subnet", "not-a-network"]) == 2
    assert "Invalid subnet" in capsys.readouterr().err


def test_main_rejects_nonpositive_workers(capsys):
    assert main(["--workers", "0"]) == 2
    assert "must be positive" in capsys.readouterr().err


def test_discovery_accepts_explicit_subnet():
    discovery = NetworkDiscovery(subnet=ipaddress.ip_network("10.0.0.0/30"), workers=2)

    assert discovery.local_net == ipaddress.ip_network("10.0.0.0/30")
    assert discovery.workers == 2


def test_discovery_can_skip_icmp(mocker):
    discovery = NetworkDiscovery.__new__(NetworkDiscovery)
    mocker.patch.object(discovery, "arp_scan", return_value=[
        {"ip": "10.0.0.1", "mac": "aa", "method": "ARP"}
    ])
    icmp = mocker.patch.object(discovery, "icmp_scan")

    result = discovery.discover(include_icmp=False)

    icmp.assert_not_called()
    assert result[0]["ip"] == "10.0.0.1"


def test_identify_nodes_preserves_order(mocker):
    identifier = mocker.patch("network_mapper.identification.Zeroconf")
    del identifier  # The constructor patch is only needed to avoid mDNS activity.
    worker = NetworkIdentifier(workers=2)
    nodes = [
        NetworkNode(ip="10.0.0.2", mac="b"),
        NetworkNode(ip="10.0.0.1", mac="a"),
    ]
    mocker.patch.object(worker, "identify_node", side_effect=lambda node: setattr(node, "role", "done"))

    result = worker.identify_nodes(nodes)

    assert result is nodes
    assert [node.ip for node in result] == ["10.0.0.2", "10.0.0.1"]
    assert all(node.role == "done" for node in result)
    worker.close()
