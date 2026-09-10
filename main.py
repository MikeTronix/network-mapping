import os
import sys
from network_mapper.discovery import NetworkDiscovery
from network_mapper.models import NetworkNode
from network_mapper.identification import NetworkIdentifier
from network_mapper.persistence import SnapshotWriter

def check_root():
    """Check if the script is running with root privileges."""
    if os.geteuid() != 0:
        print("[-] Error: This tool requires root/administrative privileges for ARP and ICMP scanning.")
        sys.exit(1)

def main():
    print("--- NetworkMapper Phase 2: Identification Suite ---")
    
    # Root check is essential for scapy raw sockets
    check_root()

    try:
        # Phase 1: Discovery
        discovery = NetworkDiscovery()
        discovered_devices = discovery.discover()

        # Convert discovered devices to NetworkNode objects
        nodes = [
            NetworkNode(
                ip=dev["ip"],
                mac=dev["mac"],
                discovery_method=dev.get("method", "Unknown"),
            )
            for dev in discovered_devices
        ]

        # Phase 2: Identification
        print("\n[*] Identifying devices... This may take a moment.")
        identifier = NetworkIdentifier()
        for node in nodes:
            print(f"  Probing {node.ip}...", end="\r")
            identifier.identify_node(node)
        
        identifier.close()
        print("\n[+] Identification complete.\n")

        print("\n" + "="*90)
        print(f"{'IP Address':<16} | {'MAC Address':<18} | {'Hostname/Title':<20} | {'Vendor':<15} | {'Role':<20}")
        print("-" * 90)
        for node in nodes:
            print(f"{node.ip:<16} | {node.mac:<18} | {node.hostname[:20]:<20} | {node.vendor[:15]:<15} | {node.role[:20]:<20}")
        print("="*90)
        print(f"Total devices identified: {len(nodes)}")

        snapshot_path = SnapshotWriter().write(
            nodes,
            scanner_ip=discovery.local_ip,
            subnet=str(discovery.local_net),
        )
        print(f"[+] Snapshot written to {snapshot_path}")

    except Exception as e:
        print(f"[-] An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
