import socket
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from zeroconf import Zeroconf
from network_mapper.models import NetworkNode

class NetworkIdentifier:
    """Handles the identification and fingerprinting of discovered network nodes."""

    def __init__(self, *, socket_timeout=0.2, http_timeout=1.0, workers=16):
        self.zc = Zeroconf()
        self.socket_timeout = socket_timeout
        self.http_timeout = http_timeout
        self.workers = max(1, workers)
        self.common_ports = {
            22: "SSH (Linux/Unix/Switch)",
            80: "HTTP (Web Server)",
            443: "HTTPS (Web Server)",
            445: "SMB (Windows/Samba)",
            53: "DNS Server",
            631: "IPP (Printer)",
            8080: "HTTP-Proxy/Alt",
        }

    def resolve_vendor(self, mac: str) -> str:
        """Look up the MAC address vendor using a public API."""
        if mac == "Unknown":
            return "Unknown"
        try:
            # Using macvendors.com API
            response = requests.get(f"https://api.macvendors.com/{mac}", timeout=2)
            if response.status_code == 200:
                return response.text
        except Exception:
            pass
        return "Unknown"

    def resolve_dns(self, ip: str) -> str:
        """Perform a reverse DNS lookup."""
        try:
            return socket.gethostbyaddr(ip)[0]
        except (socket.herror, socket.gaierror, socket.timeout, OSError):
            return "Unknown"

    def resolve_mdns(self, ip: str) -> str:
        """Attempt to find a hostname using mDNS."""
        # zeroconf doesn't easily allow reverse IP lookup for specific addresses
        # but we can browse for services and map them back.
        # For this implementation, we'll keep it simple:
        # mDNS usually broadcasts. We can check if the IP is associated with a known service.
        return "Unknown" # Placeholder for a more complex mDNS mapping logic

    def probe_services(self, ip: str) -> tuple[str, list[str]]:
        """Scan common ports to determine the device role and services."""
        found_services = []
        role = "Generic Device"

        for port, name in self.common_ports.items():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.socket_timeout)
                if s.connect_ex((ip, port)) == 0:
                    found_services.append(name)
                    # Refine role based on key services
                    if port == 445: role = "Windows Machine"
                    elif port == 22: role = "Linux/Network Device"
                    elif port == 631: role = "Printer"
                    elif port == 80 or port == 443: 
                        role = "Web-Enabled Device"
                        # Try to scrape title for more precision
                        title = self._scrape_http_title(ip, port)
                        if title:
                            role = f"Web Server: {title}"

        return role, found_services

    def _scrape_http_title(self, ip: str, port: int) -> str:
        """Scrape the HTML title from a web server to identify it."""
        try:
            protocol = "https" if port == 443 else "http"
            url = f"{protocol}://{ip}:{port}"
            response = requests.get(url, timeout=self.http_timeout, verify=False)
            soup = BeautifulSoup(response.text, 'html.parser')
            if soup.title and soup.title.string:
                return soup.title.string.strip()
        except Exception:
            pass
        return ""

    def identify_node(self, node: NetworkNode):
        """Orchestrate the identification process for a single node."""
        # 1. Vendor Lookup
        node.vendor = self.resolve_vendor(node.mac)
        
        # 2. DNS Lookup
        dns_name = self.resolve_dns(node.ip)
        if dns_name != "Unknown":
            node.hostname = dns_name
            node.confidence_score += 30

        # 3. Service Probe
        role, services = self.probe_services(node.ip)
        node.role = role
        node.services = services
        
        if services:
            node.confidence_score += 20

        # Final Hostname Refinement: if we found a web title, use it as hostname
        if "Web Server:" in node.role:
            node.hostname = node.role.replace("Web Server: ", "")
            node.confidence_score += 40

    def identify_nodes(self, nodes):
        """Identify nodes concurrently while preserving input order."""
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            list(executor.map(self.identify_node, nodes))
        return nodes

    def close(self):
        """Close the zeroconf instance."""
        self.zc.close()
