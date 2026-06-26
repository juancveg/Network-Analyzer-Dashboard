# Network Analyzer — Cisco Networking Academy Practice Project

A hands-on project built while going through the **Cisco Networking Academy: Networking Basics** course. Instead of just reading about subnetting and network protocols, I wanted to actually implement the concepts in code and get measurable results from a real network.

The project has three parts that build on each other: a subnet calculator, a live network scanner, and a web dashboard that visualizes the results.

---

## What it does

### Part 1 — Subnet Calculator (`subnet_calculator.py`)
Takes an IP address and prefix and computes everything about that subnet: network address, subnet mask, broadcast address, first and last usable host, and total host count. Also implements **VLSM (Variable Length Subnet Masking)** to split a network into subnets of different sizes based on actual requirements.

**Cisco course concepts applied:** IPv4 addressing, subnet masks, broadcast domains, VLSM.

**Measured result:**
```
Network   : 10.0.0.0/24  →  split into 3 subnets
Subnet 1  : 10.0.0.0/26   — 62 usable hosts  (needed 50)
Subnet 2  : 10.0.0.64/27  — 30 usable hosts  (needed 25)
Subnet 3  : 10.0.0.96/28  — 14 usable hosts  (needed 10)
```

---

### Part 2 — Network Scanner (`network_scanner.py`)
Scans the local subnet using two methods:
1. **ARP table lookup** — reads devices the OS already knows about (Layer 2)
2. **ICMP ping sweep** — actively probes every host in the subnet (Layer 3)

Outputs a list of active devices with their IP, MAC address, hostname (via reverse DNS), and an inferred device type. Results are saved to `scan_result.json`.

**Cisco course concepts applied:** ARP, ICMP, OSI model layers 2 and 3, subnet ranges, network vs. broadcast address.

**Measured result on a real home network:**
```
Scanned  : 254 hosts
Active   : 7 devices found
Time     : 2.7 seconds
Devices  : Router, 4 hosts, 1 mobile device, 1 unknown
```

> Note: `scan_result.json` is in `.gitignore` to avoid exposing real network data.  
> Use `scan_result.example.json` as a reference for the expected format.

---

### Part 3 — Dashboard (`index.html`)
A browser-based dashboard that reads the scan results and draws an interactive network topology map. Each device is represented as a node with a color based on its type. Clicking a node shows its details. The layout reflects a **star topology** — the most common in home and office networks, and a core concept in the Cisco course.

**Cisco course concepts applied:** network topologies (star), end devices vs. intermediary devices, LAN structure.

---

## Requirements

- Python 3.8 or higher
- [scapy](https://scapy.net/) — for raw packet access
- [Npcap](https://npcap.com/#download) — required on Windows for scapy to work

Install the Python dependency:
```bash
pip install scapy
```

---

## How to run it

### Subnet calculator
```bash
python subnet_calculator.py
```
Edit the bottom of the file to test different networks and VLSM requirements.

### Network scanner
Run as administrator (required for raw network access):

**Windows:**
```bash
# Open PowerShell as Administrator, then:
python network_scanner.py
```

**Linux / Mac:**
```bash
sudo python3 network_scanner.py
```

This generates `scan_result.json` in the project folder.

### Dashboard
Start a local server in the project folder:
```bash
python -m http.server 8080
```
Then open `http://localhost:8080` in your browser.

The dashboard reads `scan_result.json` if it exists, or falls back to the embedded example data so it always has something to display.

> **Why a local server?** Opening `index.html` directly as a file (`file://`) causes browsers to block `fetch()` calls for security reasons. The local server avoids that.

---

## Project structure

```
.
├── subnet_calculator.py       # Part 1: subnet math and VLSM
├── network_scanner.py         # Part 2: ARP + ICMP network discovery
├── index.html                 # Part 3: interactive topology dashboard
├── scan_result.example.json   # Sample output for reference
├── .gitignore                 # Excludes scan_result.json (real network data)
└── README.md
```

---

## Why this project

The Cisco Networking Basics course covers a lot of theory — IP addressing, subnetting, protocols, topologies. This project was my way of making that theory concrete. Every function in the code maps directly to something from the course, and the scanner actually ran against my real home network and found 7 devices in under 3 seconds.

It's not a polished tool, but it works, and building it made the concepts stick in a way that just reading about them didn't.
