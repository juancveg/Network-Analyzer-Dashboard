# network_scanner.py
# Local network scanner — Phase 2 of the project
#
# After building the subnet calculator I wanted to actually scan a real
# network instead of just doing math on paper. This script discovers
# active devices on the local subnet using two complementary methods:
#
#   1. ARP table lookup — reads devices the OS already knows about (layer 2)
#   2. ICMP ping sweep — actively probes each host in the subnet (layer 3)
#
# On Windows, reading the ARP table turns out to be more reliable than
# spawning ping subprocesses. Also learned that the -W flag for ping
# timeout is Linux-only — Windows uses -w (milliseconds), and ignoring
# that caused the sweep to hang for several minutes.

import socket
import subprocess
import platform
import ipaddress
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_local_ip():
    # Opening a UDP socket to an external IP (no data sent) forces the OS
    # to pick the active interface, which reveals the local IP.
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def get_network_range(local_ip, prefix=24):
    # strict=False handles cases like 192.168.40.25/24 — uses
    # 192.168.40.0/24 as the network address instead of throwing an error.
    network = ipaddress.IPv4Network(f"{local_ip}/{prefix}", strict=False)
    return network


def get_arp_devices(network):
    # Read the ARP table — most reliable method on Windows since it shows
    # devices the OS has already talked to, regardless of ICMP settings.
    # Splitting by whitespace works regardless of language (ES/EN Windows).
    devices = {}

    try:
        output = subprocess.check_output(["arp", "-a"], text=True, timeout=5)

        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 3:
                ip_str = parts[0]
                mac = parts[1]
                try:
                    ip = ipaddress.IPv4Address(ip_str)
                    if ip in network:
                        devices[ip_str] = mac
                except ValueError:
                    continue
    except Exception as e:
        print(f"  ARP error: {e}")

    return devices


def ping(ip):
    # ICMP Echo Request — secondary discovery method for hosts not in ARP.
    # -w on Windows is timeout in milliseconds (500ms here).
    # -W on Linux/Mac is timeout in seconds — different flags, easy to mix up.
    flag = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_flag = ["-w", "500"] if platform.system().lower() == "windows" else ["-W", "1"]

    try:
        result = subprocess.run(
            ["ping", flag, "1"] + timeout_flag + [str(ip)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2
        )
        return result.returncode == 0
    except Exception:
        return False


def resolve_hostname(ip):
    # Reverse DNS: given an IP, try to get the device name.
    # Falls back to "unknown" if no DNS record exists locally.
    try:
        return socket.gethostbyaddr(str(ip))[0]
    except socket.herror:
        return "unknown"


def classify_device(hostname, ip_str):
    # Best-effort classification based on hostname keywords and last octet.
    # Home routers are almost always at .1 or .254.
    hostname_lower = hostname.lower()
    last_octet = int(ip_str.split(".")[-1])

    if last_octet in [1, 254] or any(p in hostname_lower for p in ["router", "gateway", "modem"]):
        return "Router / Gateway"
    elif any(p in hostname_lower for p in ["phone", "android", "iphone"]):
        return "Mobile device"
    elif any(p in hostname_lower for p in ["printer", "hp", "epson", "canon"]):
        return "Printer"
    elif any(p in hostname_lower for p in ["tv", "roku", "chromecast"]):
        return "Smart TV"
    else:
        return "Host"


def scan_network(prefix=24):
    local_ip = get_local_ip()
    network = get_network_range(local_ip, prefix)
    hosts = list(network.hosts())

    print(f"\n{'='*55}")
    print(f"  Local network scanner")
    print(f"{'='*55}")
    print(f"  My IP          : {local_ip}")
    print(f"  Network        : {network}")
    print(f"  Subnet mask    : {network.netmask}")
    print(f"  Network addr   : {network.network_address}  (not assignable)")
    print(f"  Broadcast      : {network.broadcast_address}  (not assignable)")
    print(f"  Hosts to check : {len(hosts)}")
    print(f"\n  Step 1: reading ARP table...")

    arp_devices = get_arp_devices(network)
    print(f"  Found {len(arp_devices)} device(s) in ARP table")

    print(f"\n  Step 2: ICMP ping sweep...\n")

    start = datetime.now()
    found_ips = set(arp_devices.keys())

    completed = 0
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(ping, ip): ip for ip in hosts}
        for future in as_completed(futures):
            completed += 1
            pct = int((completed / len(hosts)) * 40)
            bar = "█" * pct + "░" * (40 - pct)
            print(f"\r  [{bar}] {completed}/{len(hosts)}", end="", flush=True)
            result = future.result()
            if result:
                found_ips.add(str(futures[future]))

    duration = (datetime.now() - start).total_seconds()

    # Build final device list combining ARP and ping results
    found = []
    for ip_str in sorted(found_ips, key=lambda x: int(x.split(".")[-1])):
        hostname = resolve_hostname(ip_str)
        device_type = classify_device(hostname, ip_str)
        mac = arp_devices.get(ip_str, "n/a")
        found.append({
            "ip": ip_str,
            "hostname": hostname,
            "mac": mac,
            "type": device_type
        })

    print(f"\n\n{'='*55}")
    print(f"  Results")
    print(f"{'='*55}")
    print(f"  Time     : {duration:.1f}s")
    print(f"  Active   : {len(found)} of {len(hosts)} hosts\n")

    for d in found:
        print(f"  [{d['type']}]")
        print(f"    IP       : {d['ip']}")
        print(f"    MAC      : {d['mac']}")
        print(f"    Hostname : {d['hostname']}\n")

    # Save to JSON — the web dashboard in Phase 3 reads this file
    output = {
        "timestamp": datetime.now().isoformat(),
        "network": str(network),
        "subnet_mask": str(network.netmask),
        "scanner_ip": local_ip,
        "total_possible": len(hosts),
        "total_active": len(found),
        "duration_seconds": round(duration, 2),
        "devices": found
    }

    with open("scan_result.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  Results saved to scan_result.json")
    return output


if __name__ == "__main__":
    scan_network()
