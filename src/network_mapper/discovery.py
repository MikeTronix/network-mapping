import socket
import ipaddress
from scapy.all import ARP, Ether, srp, ICMP, IP, sr1

class NetworkDiscovery:
    """Handles the discovery of active devices on the local network."""

    def __init__(self):
        self.local_ip = self._get_local_ip()
        self.local_net = self._get_local_network()
        print(f"[*] Local IP: {self.local_ip}")
        print(f"[*] Local Network: {self.local_net}")

    def _get_local_ip(self):
        """Determine the local IP address of the machine."""
        try:
            # Create a dummy socket to determine the local interface used for external traffic
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            print(f"[-] Error detecting local IP: {e}")
            return "127.0.0.1"

    def _get_local_network(self):
        """Determine the local network address and mask."""
        try:
            # This is a simplified approach. In a real scenario, we'd query the interface mask.
            # We'll assume a /24 network for simplicity if we can't detect it, 
            # but let's try to be more precise.
            import subprocess
            # On Linux, we can use 'ip addr' or 'ifconfig'.
            # For a more portable way, we can use scapy's conf.iface or just assume /24 for Phase 1 discovery logic.
            # To be safe, we'll derive the network from the local IP assuming a common /24 if not otherwise detectable.
            # Better yet, we'll use the ipaddress library on the local_ip and assume /24 for the demo.
            return ipaddress.ip_network(f"{self.local_ip}/24", strict=False)
        except Exception as e:
            print(f"[-] Error detecting local network: {e}")
            return None

    def arp_scan(self):
        """Perform an ARP scan of the local network."""
        if not self.local_net:
            return []

        print(f"[*] Starting ARP scan on {self.local_net}...")
        # Create an ARP request packet
        # Ether(dst="ff:ff:ff:ff:ff:ff") sends it to everyone on the local link
        # ARP(pdst=target_ip) asks "Who has this IP?"
        target_ip = str(self.local_net)
        arp_request = ARP(pdst=target_ip)
        broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
        arp_request_broadcast = broadcast / arp_request

        # Send and receive packets (timeout 2s)
        answered, unanswered = srp(arp_request_broadcast, timeout=2, verbose=False)

        devices = []
        for sent, received in answered:
            devices.append({
                "ip": received.psrc,
                "mac": received.hwsrc,
                "method": "ARP"
            })
        
        print(f"[+] ARP scan found {len(devices)} devices.")
        return devices

    def icmp_scan(self):
        """Perform an ICMP (ping) scan of the local network."""
        if not self.local_net:
            return []

        print(f"[*] Starting ICMP scan on {self.local_net}...")
        devices = []
        # We iterate through the subnet
        for ip in self.local_net.hosts():
            ip_str = str(ip)
            # Send a single ICMP Echo Request
            packet = IP(dst=ip_str)/ICMP()
            reply = sr1(packet, timeout=0.5, verbose=False)
            
            if reply:
                # Since ICMP doesn't give us the MAC, we can try to resolve it 
                # but usually, ARP has already done the heavy lifting.
                devices.append({
                    "ip": ip_str,
                    "mac": "Unknown", # ICMP doesn't provide MAC directly in the response
                    "method": "ICMP"
                })
        
        print(f"[+] ICMP scan found {len(devices)} devices.")
        return devices

    def discover(self):
        """Combine ARP and ICMP scans to find all live devices."""
        arp_results = self.arp_scan()
        icmp_results = self.icmp_scan()

        # Merge results using IP as key
        final_devices = {}
        
        # ARP results are high confidence and provide MACs
        for dev in arp_results:
            final_devices[dev["ip"]] = dev
            
        # Add ICMP results if the IP wasn't already found by ARP
        for dev in icmp_results:
            if dev["ip"] not in final_devices:
                final_devices[dev["ip"]] = dev
        
        return list(final_devices.values())
