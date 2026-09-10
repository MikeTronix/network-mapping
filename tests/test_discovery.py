import ipaddress
from unittest.mock import MagicMock, patch

import pytest

from network_mapper.discovery import NetworkDiscovery


@pytest.fixture
def discovery():
    with patch.object(NetworkDiscovery, "_get_local_ip", return_value="192.168.1.10"), \
         patch.object(NetworkDiscovery, "_get_local_network",
                      return_value=ipaddress.ip_network("192.168.1.0/30")):
        yield NetworkDiscovery()


def test_local_network_is_initialized(discovery):
    assert discovery.local_ip == "192.168.1.10"
    assert discovery.local_net == ipaddress.ip_network("192.168.1.0/30")


def test_arp_scan_returns_ip_and_mac(discovery, mocker):
    received = MagicMock(psrc="192.168.1.1", hwsrc="aa:bb:cc:dd:ee:ff")
    mock_srp = mocker.patch(
        "network_mapper.discovery.srp",
        return_value=([(None, received)], []),
    )

    results = discovery.arp_scan()

    assert results == [{
        "ip": "192.168.1.1",
        "mac": "aa:bb:cc:dd:ee:ff",
        "method": "ARP",
    }]
    mock_srp.assert_called_once()


def test_icmp_scan_returns_only_hosts_that_reply(discovery, mocker):
    def reply(packet, timeout, verbose):
        return object() if packet.dst == "192.168.1.1" else None

    mock_sr1 = mocker.patch("network_mapper.discovery.sr1", side_effect=reply)

    results = discovery.icmp_scan()

    assert results == [{"ip": "192.168.1.1", "mac": "Unknown", "method": "ICMP"}]
    assert mock_sr1.call_count == 2  # .1 and .2 in a /30 network


def test_discover_deduplicates_and_prioritizes_arp(discovery, mocker):
    mocker.patch.object(
        discovery, "arp_scan",
        return_value=[{"ip": "192.168.1.1", "mac": "aa:bb:cc", "method": "ARP"}],
    )
    mocker.patch.object(
        discovery, "icmp_scan",
        return_value=[
            {"ip": "192.168.1.1", "mac": "Unknown", "method": "ICMP"},
            {"ip": "192.168.1.2", "mac": "Unknown", "method": "ICMP"},
        ],
    )

    results = discovery.discover()

    assert results == [
        {"ip": "192.168.1.1", "mac": "aa:bb:cc", "method": "ARP"},
        {"ip": "192.168.1.2", "mac": "Unknown", "method": "ICMP"},
    ]
