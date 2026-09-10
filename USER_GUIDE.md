# NetworkMapper User Guide

## 1. Purpose

NetworkMapper identifies devices on a local network and records the results in an ASCII snapshot and an interactive HTML map. It combines several signals because no single discovery or naming method works for every home, office, IoT, or firewalled device.

Run it only on networks you own or are authorized to assess.

## 2. Install

From the repository root:

```bash
uv sync
```

Confirm the installation:

```bash
uv run pytest
```

## 3. Run a Scan

The simplest scan is:

```bash
sudo .venv/bin/python main.py
```

The tool infers the active local address and scans an assumed `/24` network. For a known network, provide the CIDR explicitly:

```bash
sudo .venv/bin/python main.py --subnet 10.0.0.0/24
```

If ICMP is undesirable or unnecessary, use ARP only:

```bash
sudo .venv/bin/python main.py --skip-icmp
```

## 4. Command-Line Options

| Option | Default | Description |
|---|---:|---|
| `--subnet CIDR` | inferred `/24` | Network range to scan |
| `--output-dir PATH` | `snapshots` | Directory for text snapshots and maps |
| `--workers N` | `16` | Maximum concurrent probes |
| `--arp-timeout SECONDS` | `2.0` | ARP response timeout |
| `--icmp-timeout SECONDS` | `0.5` | ICMP response timeout per host |
| `--socket-timeout SECONDS` | `0.2` | TCP connection timeout |
| `--http-timeout SECONDS` | `1.0` | HTTP title request timeout |
| `--skip-icmp` | disabled | Skip the ICMP fallback scan |

For a slower, less aggressive scan, reduce concurrency and increase timeouts:

```bash
sudo .venv/bin/python main.py \
  --subnet 192.168.1.0/24 \
  --workers 4 \
  --socket-timeout 0.5 \
  --icmp-timeout 1.0
```

## 5. Understanding Identification

The tool records:

- **IP/MAC**: Addresses observed during discovery.
- **Hostname**: Usually obtained through reverse DNS; an HTTP page title may refine it.
- **Vendor**: Derived from the MAC OUI through the configured vendor service.
- **Services**: Responses from common TCP ports such as SSH, HTTP(S), SMB, DNS, IPP, and port 8080.
- **Role**: A best-effort role inferred from detected services.
- **Confidence**: A score reflecting DNS, service, and HTTP-title evidence; it is not a probability.

`Unknown` is a valid result. Firewalls, client isolation, sleeping devices, randomized MAC addresses, and missing DNS records can all limit identification.

## 6. Reading the Output

Each scan writes an ASCII report similar to:

```text
snapshots/network_map_20250909_184530.txt
```

The map is written beneath the selected output directory:

```text
snapshots/maps/network_map_20250909_184530.html
```

Open the HTML map in a modern browser. Hover over a device for its details. Node color indicates an inferred role, while node size reflects identification confidence. The scanner is shown as the central node.

## 7. Troubleshooting

### Permission denied or no ARP results
Run the command with `sudo` or an Administrator shell. Confirm that the selected interface is connected to the target LAN and that Wi-Fi client isolation is disabled if appropriate.

### The inferred subnet is wrong
Always specify the range explicitly with `--subnet`, for example `--subnet 192.168.50.0/24`.

### The scan is too slow
Use `--workers` to increase concurrency, or use `--skip-icmp`. Increasing concurrency can create more network traffic and may trigger monitoring systems.

### Names or vendors are missing
Check local DNS and mDNS availability. Some devices do not publish names. Vendor lookup depends on an external service and may fail without Internet access; the MAC address is still retained in the local snapshot.

### Existing files are not overwritten
If two scans occur in the same second, the second file receives a numeric suffix such as `_1`.

## 8. Privacy and Operational Considerations

Snapshots contain network addresses, hostnames, MAC addresses, services, and potentially HTTP page titles. Store them securely and avoid committing them to a public repository. The vendor lookup sends a MAC address to an external service; do not use that feature where this is unacceptable without replacing it with a local OUI database.
