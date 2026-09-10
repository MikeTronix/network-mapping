# NetworkMapper

NetworkMapper is a Python tool for discovering and identifying devices on an authorized local home or business network. It prioritizes useful device names and identification confidence over merely producing a fast IP list, then saves a human-readable snapshot and interactive HTML map.

## Features

- ARP discovery for local-link devices
- Optional concurrent ICMP fallback scanning
- Reverse DNS and MAC-vendor identification
- Common-service probing and HTTP title detection
- Confidence-scored `NetworkNode` records
- Timestamped ASCII snapshots
- Interactive PyVis/NetworkX maps
- Filtering and concurrency controls through the Python API and CLI
- Unit tests with `pytest`

## Requirements

- Python 3.10 or newer
- `uv` recommended for dependency and environment management
- Root/administrator privileges for Scapy ARP/ICMP operations
- Permission to scan the network being tested

## Installation with uv

```bash
uv sync
```

This creates or updates `.venv` from `pyproject.toml` and `uv.lock`.

## Quick Start

Run a scan using the inferred local `/24` subnet:

```bash
sudo .venv/bin/python main.py
```

Or use uv's runner:

```bash
sudo uv run python main.py
```

Specify a subnet and output directory:

```bash
sudo .venv/bin/python main.py \
  --subnet 192.168.1.0/24 \
  --output-dir ./network-data \
  --workers 24
```

For ARP-only discovery:

```bash
sudo .venv/bin/python main.py --skip-icmp
```

Use `--help` for all options:

```bash
.venv/bin/python main.py --help
```

## Output

A normal run creates:

```text
snapshots/network_map_YYYYMMDD_HHMMSS.txt
snapshots/maps/network_map_YYYYMMDD_HHMMSS.html
```

The ASCII snapshot contains the capture time, scanner and subnet metadata, and each device's IP, MAC, hostname, vendor, role, services, and confidence score. Open the HTML file in a browser to view the interactive map.

The current topology is intentionally scanner-centric: discovery confirms that devices are reachable from the scanner but does not yet determine physical switch-port or router-forwarding topology.

## Development

Run the complete test suite:

```bash
uv run pytest
```

The tests mock network activity and do not scan a live network. Generated virtual environments, snapshots, maps, caches, and PyVis assets are excluded by `.gitignore`.

## Project Layout

```text
main.py                         CLI entry point
src/network_mapper/
  discovery.py                  ARP and ICMP discovery
  identification.py             DNS, vendor, port, and HTTP identification
  models.py                     NetworkNode data model
  persistence.py                ASCII snapshot writer
  visualization.py              NetworkX/PyVis graph rendering
tests/                          pytest unit tests
DESIGN_DOC.md                   Project design and feasibility assessment
USER_GUIDE.md                   Operational user guide
```

## Safety and Privacy

Only scan networks you own or are explicitly authorized to administer. Port probing can trigger security monitoring. Vendor lookup currently uses an external MAC-vendor service when available; avoid that mode if MAC addresses must remain private.
