# subnet_calculator.py
# Subnet calculator and VLSM tool — Phase 1 of the project
#
# Built while going through the Cisco Networking Academy basics course.
# The goal was to actually implement the math behind subnetting instead
# of just using an online calculator. Turns out it's mostly bit manipulation
# once you understand that a subnet mask is just a sequence of 1s followed
# by 0s in binary.

import math


def calcular_subred(ip_red, prefijo):
    # Break the IP into its four octets so we can work with each part
    octetos = list(map(int, ip_red.split('.')))

    # The number of host bits determines how many devices fit in this subnet.
    # Formula: 2^(host bits) - 2  (subtract network address and broadcast)
    bits_host = 32 - prefijo
    total_hosts = (2 ** bits_host) - 2

    # Build the subnet mask: prefijo ones followed by zeros, split into octets
    mascara_bits = ('1' * prefijo).ljust(32, '0')
    mascara = [int(mascara_bits[i:i+8], 2) for i in range(0, 32, 8)]

    # Convert IP to a single 32-bit integer so we can do bitwise operations
    ip_num = int(''.join(f'{o:08b}' for o in octetos), 2)

    # Broadcast: set all host bits to 1 using a bitwise OR with the host mask
    broadcast_num = ip_num | ((2 ** bits_host) - 1)
    broadcast_bits = f'{broadcast_num:032b}'
    broadcast = [int(broadcast_bits[i:i+8], 2) for i in range(0, 32, 8)]

    # First usable host is network address + 1, last is broadcast - 1
    primer_host_num = ip_num + 1
    ultimo_host_num = broadcast_num - 1

    def num_a_ip(n):
        b = f'{n:032b}'
        return '.'.join(str(int(b[i:i+8], 2)) for i in range(0, 32, 8))

    return {
        'network':       ip_red,
        'prefix':        prefijo,
        'subnet_mask':   '.'.join(map(str, mascara)),
        'broadcast':     '.'.join(map(str, broadcast)),
        'first_host':    num_a_ip(primer_host_num),
        'last_host':     num_a_ip(ultimo_host_num),
        'usable_hosts':  total_hosts,
        'host_bits':     bits_host
    }


def vlsm(ip_base, prefijo_base, necesidades):
    # VLSM assigns the smallest possible block to each subnet requirement.
    # Sorting from largest to smallest first is important — it prevents
    # address space fragmentation.
    necesidades_ordenadas = sorted(necesidades, reverse=True)
    subredes = []

    octetos = list(map(int, ip_base.split('.')))
    ip_actual = int(''.join(f'{o:08b}' for o in octetos), 2)

    for n_hosts in necesidades_ordenadas:
        # Find how many host bits we need: 2^n - 2 >= required hosts
        bits_host_necesarios = math.ceil(math.log2(n_hosts + 2))
        prefijo_nuevo = 32 - bits_host_necesarios

        if prefijo_nuevo < prefijo_base:
            print(f"  Not enough space for {n_hosts} hosts in this address space")
            continue

        ip_subred = (
            f'{ip_actual >> 24}.'
            f'{(ip_actual >> 16) & 255}.'
            f'{(ip_actual >> 8) & 255}.'
            f'{ip_actual & 255}'
        )

        datos = calcular_subred(ip_subred, prefijo_nuevo)
        datos['required_hosts'] = n_hosts
        subredes.append(datos)

        # Jump to the start of the next block
        ip_actual += 2 ** bits_host_necesarios

    return subredes


if __name__ == '__main__':
    print("=" * 60)
    print("  Subnet Calculator — Cisco Networking Academy practice")
    print("=" * 60)

    # Example 1: basic subnet breakdown
    print("\n  Example 1: Analyze 192.168.1.0/24")
    datos = calcular_subred('192.168.1.0', 24)
    for key, val in datos.items():
        print(f"    {key:<16}: {val}")

    # Example 2: VLSM across three departments
    print("\n  Example 2: VLSM on 10.0.0.0/24")
    print("  Requirements — Sales: 50 hosts, IT: 25 hosts, Management: 10 hosts\n")

    subredes = vlsm('10.0.0.0', 24, [50, 25, 10])

    for i, s in enumerate(subredes, 1):
        print(f"  Subnet {i}  (needed: {s['required_hosts']} hosts)")
        print(f"    Network   : {s['network']}/{s['prefix']}")
        print(f"    Mask      : {s['subnet_mask']}")
        print(f"    Host range: {s['first_host']} – {s['last_host']}")
        print(f"    Broadcast : {s['broadcast']}")
        print(f"    Usable    : {s['usable_hosts']} hosts")
        print()
