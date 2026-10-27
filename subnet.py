"""Calculation logic: subnet calculator + VLSM planner."""
import ipaddress
import math


def calculate(ip, prefix):
    """Return subnet details for an IPv4 address and prefix length."""
    try:
        addr = ipaddress.IPv4Address(ip.strip())
    except ValueError:
        raise ValueError(f"'{ip}' is not a valid IPv4 address")
    try:
        prefix = int(prefix)
    except (TypeError, ValueError):
        raise ValueError("Prefix must be a number between 0 and 32")
    if not 0 <= prefix <= 32:
        raise ValueError("Prefix must be between 0 and 32")

    net = ipaddress.IPv4Network(f"{addr}/{prefix}", strict=False)
    total = net.num_addresses
    if prefix == 32:
        usable, first, last, note = 1, net.network_address, net.network_address, "Single-address prefix"
    elif prefix == 31:
        usable, first, last, note = 2, net.network_address, net.broadcast_address, "Point-to-point link (RFC 3021), no network/broadcast"
    else:
        usable = total - 2
        first, last, note = net.network_address + 1, net.broadcast_address - 1, ""
    return {
        "ip": str(addr), "prefix": prefix, "mask": str(net.netmask),
        "network": str(net.network_address), "broadcast": str(net.broadcast_address),
        "total": total, "usable": usable, "first": str(first), "last": str(last),
        "binary_ip": ".".join(f"{o:08b}" for o in addr.packed),
        "binary_mask": ".".join(f"{o:08b}" for o in net.netmask.packed),
        "note": note,
    }


def plan(parent, requirements):
    """VLSM: requirements = list of (name, hosts). Returns (rows, remaining_free_addresses)."""
    try:
        pnet = ipaddress.IPv4Network(parent.strip(), strict=True)
    except ValueError:
        raise ValueError("Parent network must look like 192.168.10.0/24 (host bits must be 0)")
    if not requirements:
        raise ValueError("Add at least one department")
    clean = []
    for name, hosts in requirements:
        if not isinstance(hosts, int) or hosts < 1:
            raise ValueError(f"Hosts for '{name}' must be a positive whole number")
        clean.append((name, hosts))

    clean.sort(key=lambda r: r[1], reverse=True)          # largest first
    pointer = int(pnet.network_address)
    end = int(pnet.broadcast_address)
    rows = []
    for name, hosts in clean:
        host_bits = max(2, math.ceil(math.log2(hosts + 2)))  # +2 = network & broadcast
        size = 2 ** host_bits
        pointer = (pointer + size - 1) // size * size        # align to block boundary
        if pointer + size - 1 > end:
            raise ValueError(f"Not enough address space for '{name}' ({hosts} hosts) in {pnet}")
        sub = ipaddress.IPv4Network((pointer, 32 - host_bits))
        rows.append({
            "name": name, "hosts": hosts, "network": str(sub.network_address),
            "prefix": sub.prefixlen, "mask": str(sub.netmask),
            "first": str(sub.network_address + 1), "last": str(sub.broadcast_address - 1),
            "broadcast": str(sub.broadcast_address), "usable": size - 2,
        })
        pointer += size
    return rows, end - pointer + 1


def parse_requirements(text):
    """Parse lines like 'IT,100' into [(name, hosts)]."""
    reqs = []
    for line in text.strip().splitlines():
        if not line.strip():
            continue
        parts = line.split(",")
        if len(parts) != 2:
            raise ValueError(f"Bad line '{line}'. Use: Name,Hosts (e.g. IT,100)")
        try:
            reqs.append((parts[0].strip(), int(parts[1])))
        except ValueError:
            raise ValueError(f"Hosts must be a number in line '{line}'")
    return reqs
