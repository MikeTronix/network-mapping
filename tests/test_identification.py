import pytest
from unittest.mock import MagicMock, patch
from network_mapper.identification import NetworkIdentifier
from network_mapper.models import NetworkNode

@pytest.fixture
def identifier():
    with patch('network_mapper.identification.Zeroconf'):
        yield NetworkIdentifier()

def test_resolve_vendor_success(identifier, mocker):
    mock_resp = mocker.Mock()
    mock_resp.status_code = 200
    mock_resp.text = "Apple, Inc."
    mocker.patch('requests.get', return_value=mock_resp)
    
    vendor = identifier.resolve_vendor("aa:bb:cc:dd:ee:ff")
    assert vendor == "Apple, Inc."

def test_resolve_vendor_fail(identifier, mocker):
    mock_resp = mocker.Mock()
    mock_resp.status_code = 404
    mocker.patch('requests.get', return_value=mock_resp)
    
    vendor = identifier.resolve_vendor("aa:bb:cc:dd:ee:ff")
    assert vendor == "Unknown"

def test_resolve_dns_success(identifier, mocker):
    mocker.patch('socket.gethostbyaddr', return_value=("my-laptop.local", "...", []))
    hostname = identifier.resolve_dns("192.168.1.10")
    assert hostname == "my-laptop.local"

def test_resolve_dns_fail(identifier, mocker):
    mocker.patch('socket.gethostbyaddr', side_effect=OSError("DNS error"))
    hostname = identifier.resolve_dns("192.168.1.10")
    assert hostname == "Unknown"


def test_unknown_mac_does_not_make_request(identifier, mocker):
    get = mocker.patch('requests.get')

    assert identifier.resolve_vendor("Unknown") == "Unknown"
    get.assert_not_called()

def test_probe_services(identifier, mocker):
    # Mock socket connect_ex to return 0 (success) for port 80
    mock_socket = mocker.patch('socket.socket')
    mock_socket.return_value.__enter__.return_value.connect_ex.side_effect = lambda addr: 0 if addr[1] == 80 else 1
    
    # Mock HTTP scraping to return a specific title
    mock_resp = mocker.Mock()
    mock_resp.text = "<html><title>HomeRouter</title></html>"
    mocker.patch('requests.get', return_value=mock_resp)
    
    role, services = identifier.probe_services("192.168.1.1")
    assert "HTTP (Web Server)" in services
    assert "Web Server: HomeRouter" in role

def test_identify_node(identifier, mocker):
    node = NetworkNode(ip="192.168.1.1", mac="aa:bb:cc:dd:ee:ff")
    
    mocker.patch.object(identifier, 'resolve_vendor', return_value="Cisco")
    mocker.patch.object(identifier, 'resolve_dns', return_value="switch-01")
    mocker.patch.object(identifier, 'probe_services', return_value=("Switch", ["SSH (Linux/Unix/Switch)"]))
    
    identifier.identify_node(node)
    
    assert node.vendor == "Cisco"
    assert node.hostname == "switch-01"
    assert node.role == "Switch"
    assert "SSH (Linux/Unix/Switch)" in node.services
    assert node.confidence_score > 0
