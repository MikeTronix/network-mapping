import argparse
import ipaddress
import os
import sys

from network_mapper.discovery import NetworkDiscovery
from network_mapper.identification import NetworkIdentifier
from network_mapper.models import NetworkNode
from network_mapper.persistence import SnapshotWriter
from network_mapper.visualization import NetworkVisualizer


def check_root():
    """Check if the script is running with root privileges."""
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        print("[-] Error: This tool requires root/administrative privileges for ARP and ICMP scanning.")
        sys.exit(1)


def build_parser():
    parser = argparse.ArgumentParser(description="Discover and map a local network.")
    parser.add_argument("--subnet", help="CIDR subnet to scan (default: inferred /24)")
    parser.add_argument("--output-dir", default="snapshots", help="Directory for snapshots and maps")
    parser.add_argument("--workers", type=int, default=16, help="Maximum concurrent probes")
    parser.add_argument("--arp-timeout", type=float, default=2.0)
    parser.add_argument("--icmp-timeout", type=float, default=0.5)
    parser.add_argument("--socket-timeout", type=float, default=0.2)
    parser.add_argument("--http-timeout", type=float, default=1.0)
    parser.add_argument("--skip-icmp", action="store_true", help="Use ARP only")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.workers < 1 or min(args.arp_timeout, args.icmp_timeout, args.socket_timeout, args.http_timeout) <= 0:
        print("[-] workers and timeout values must be positive", file=sys.stderr)
        return 2

    subnet = None
    if args.subnet:
        try:
            subnet = ipaddress.ip_network(args.subnet, strict=False)
        except ValueError as error:
            print(f"[-] Invalid subnet: {error}", file=sys.stderr)
            return 2

    print("--- NetworkMapper: Discovery and Identification ---")
    check_root()
    identifier = None
    try:
        discovery = NetworkDiscovery(
            subnet=subnet,
            arp_timeout=args.arp_timeout,
            icmp_timeout=args.icmp_timeout,
            workers=args.workers,
        )
        discovered_devices = discovery.discover(include_icmp=not args.skip_icmp)
        nodes = [
            NetworkNode(
                ip=dev["ip"],
                mac=dev["mac"],
                discovery_method=dev.get("method", "Unknown"),
            )
            for dev in discovered_devices
        ]

        print("\n[*] Identifying devices... This may take a moment.")
        identifier = NetworkIdentifier(
            socket_timeout=args.socket_timeout,
            http_timeout=args.http_timeout,
            workers=args.workers,
        )
        identifier.identify_nodes(nodes)
        print("[+] Identification complete.\n")

        print("=" * 90)
        print(f"{'IP Address':<16} | {'MAC Address':<18} | {'Hostname/Title':<20} | {'Vendor':<15} | {'Role':<20}")
        print("-" * 90)
        for node in nodes:
            print(f"{node.ip:<16} | {node.mac:<18} | {node.hostname[:20]:<20} | {node.vendor[:15]:<15} | {node.role[:20]:<20}")
        print("=" * 90)
        print(f"Total devices identified: {len(nodes)}")

        snapshot_path = SnapshotWriter(args.output_dir).write(
            nodes, scanner_ip=discovery.local_ip, subnet=str(discovery.local_net)
        )
        visualizer = NetworkVisualizer()
        graph = visualizer.build_graph(nodes, scanner_ip=discovery.local_ip)
        map_path = visualizer.render(
            graph, snapshot_path.parent / "maps" / snapshot_path.with_suffix(".html").name
        )
        print(f"[+] Snapshot written to {snapshot_path}")
        print(f"[+] Interactive map written to {map_path}")
        return 0
    except Exception as error:
        print(f"[-] An unexpected error occurred: {error}", file=sys.stderr)
        return 1
    finally:
        if identifier is not None:
            identifier.close()


if __name__ == "__main__":
    raise SystemExit(main())
