# Project Design Document: NetworkMapper

## 1. Project Overview
`NetworkMapper` is a Python-based utility designed to discover, identify, and visualize devices within a local home or business network. Unlike basic IP scanners that only list active addresses, this tool focuses on **high-quality node detection and identification**, attempting to provide meaningful names and roles for every device found. The final state of the network is persisted to a timestamped ASCII file and rendered as an interactive graphical map.

## 2. Goals & Objectives
- **Comprehensive Discovery**: Identify all active devices on the local subnet.
- **High-Fidelity Naming**: Use multiple identification vectors (DNS, mDNS, NetBIOS, MAC OUI, Service Probing) to assign the most accurate name possible to each node.
- **Persistence**: Save the detected network state to a timestamped, human-readable ASCII file for auditing and history.
- **Visual Representation**: Generate a graphical map showing the relationship between the scanner and detected devices, supporting filtering and scaling.
- **Standard Library First**: Prioritize standard Python libraries, utilizing specialized networking libraries only where necessary for low-level packet manipulation.

## 3. System Architecture

### 3.1 Node Detection (Discovery Phase)
The tool will use a multi-stage discovery process to ensure maximum coverage:
1. **ARP Scanning**: Use ARP requests to find all active MAC addresses on the local link (most reliable for local networks).
2. **ICMP Echo (Ping)**: Verify reachability and identify devices that might block ARP but respond to ICMP.
3. **Subnet Iteration**: Sweep the local subnet range to identify active IP addresses.

### 3.2 Node Identification (Fingerprinting Phase)
To move beyond "Unknown Device," the tool will employ the following hierarchy of naming:
1. **Reverse DNS Lookup**: Query the local DNS server for the hostname associated with the IP.
2. **mDNS/Bonjour**: Probe for multicast DNS records (common for Apple devices, printers, and IoT).
3. **NetBIOS**: Use NetBIOS name service (NBNS) for older Windows devices.
4. **MAC OUI Lookup**: Analyze the first 3 bytes of the MAC address against a vendor database to identify the manufacturer (e.g., "Apple", "Samsung", "Cisco").
5. **Service Probing**:
    - Scan common ports (80, 443, 22, 445, etc.).
    - For HTTP/HTTPS ports, attempt to fetch the `<title>` tag or server header.
    - Identify specific services (e.g., "SSH Server" $\rightarrow$ likely a Linux box or Switch).

### 3.3 Data Storage
The system will output a timestamped ASCII file (e.g., `network_map_20231027_1200.txt`).
- **Format**: A structured text format (or YAML/JSON represented as text) containing:
    - Scan timestamp and scanner IP/MAC.
    - List of devices with: IP, MAC, Vendor, Hostname, Detected Services, and Confidence Score.
    - Connection topology (Simple star topology relative to the scanner).

### 3.4 Visualization
The visualization component will transform the collected data into a graph:
- **Graph Engine**: `NetworkX` for managing nodes and edges.
- **Rendering**: `PyVis` (Interactive HTML/JS) or `Matplotlib`. `PyVis` is preferred for scaling and filtering capabilities.
- **Features**:
    - Nodes colored by device type/vendor.
    - Tooltips showing full device details.
    - Ability to filter out certain vendors or service types.

## 4. Proposed Technical Stack
- **Language**: Python 3.10+
- **Networking**:
    - `scapy`: For ARP scanning and packet crafting.
    - `socket`: For DNS lookups and port scanning.
    - `requests`: For HTTP title scraping.
    - `zeroconf`: For mDNS discovery.
- **Data/Graph**:
    - `networkx`: Graph theory and structure.
    - `pyvis`: Interactive network visualization.
- **Utilities**:
    - `datetime`: Timestamping.
    - `ipaddress`: Subnet calculations.

## 5. Implementation Plan
1. **Phase 1: Discovery Core**: Implement ARP scanning and subnet detection.
2. **Phase 2: Identification Suite**: Implement the naming hierarchy (DNS $\rightarrow$ mDNS $\rightarrow$ MAC OUI $\rightarrow$ Port Scan).
3. **Phase 3: Persistence Layer**: Implement the ASCII file exporter.
4. **Phase 4: Visualization**: Implement the NetworkX to PyVis pipeline.
5. **Phase 5: Refinement**: Add filtering, scaling, and performance optimizations (threading for port scans).

## 6. Phase Delivery and Test Workflow
Each implementation phase is delivered as an independent commit. Before committing, the phase must have:

1. A small design/API review recorded in code documentation or this document.
2. Unit tests for normal behavior, filtering, failure handling, and boundary cases.
3. A complete `uv run pytest` run with no failures.
4. A push to `origin/main` so the repository remains usable at every milestone.

Phase 4 uses a scanner-centric topology because discovery does not yet expose switch-port or router forwarding information. The visualizer therefore shows confirmed scanner-to-device reachability and clearly avoids claiming physical topology. Filters are applied before graph construction, while node titles, colors, and sizes communicate identification quality.

## 7. Feasibility Analysis
- **Technical Feasibility**: **High**. The required libraries (`scapy`, `zeroconf`, `pyvis`) are mature and well-documented. The logic for node identification is a standard process in network administration.
- **Resource Feasibility**: **High**. The tool has low CPU/RAM requirements, as it primarily performs I/O-bound network requests.
- **Environment Feasibility**: **Medium**. The tool will require administrative/root privileges to perform ARP scanning and raw socket manipulation (standard for network tools).

## 8. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Permission Issues** | High | Explicitly notify user that `sudo`/Administrator privileges are required for ARP scanning. |
| **Network Noise/Security** | Medium | Implement configurable scan speeds to avoid triggering Intrusion Detection Systems (IDS). |
| **Inaccurate Naming** | Medium | Use a "Confidence Score" for names; if multiple sources disagree, list the most reliable one first. |
| **Slow Scan Times** | Low | Use `concurrent.futures` for multi-threaded port scanning and identification. |
| **Firewalled Devices** | Medium | Combine multiple detection methods (ARP + ICMP + TCP) to ensure devices that block specific protocols are still caught. |
