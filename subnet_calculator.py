import math

def calcular_subred(ip_red, prefijo):
    """
    Dado una IP de red y su prefijo CIDR, calcula todos los datos de la subred.
    Conceptos del curso aplicados: direccionamiento IP, máscaras, broadcast.
    """
    # Convertir IP a lista de octetos
    octetos = list(map(int, ip_red.split('.')))
    
    # Calcular máscara de subred (concepto: bits de red vs bits de host)
    bits_host = 32 - prefijo
    total_hosts = (2 ** bits_host) - 2  # Se restan red y broadcast
    
    # Construir máscara en decimal
    mascara_bits = ('1' * prefijo).ljust(32, '0')
    mascara = [
        int(mascara_bits[i:i+8], 2) for i in range(0, 32, 8)
    ]
    
    # Calcular dirección de broadcast (todos los bits de host en 1)
    ip_num = int(''.join(f'{o:08b}' for o in octetos), 2)
    broadcast_num = ip_num | ((2 ** bits_host) - 1)
    broadcast_bits = f'{broadcast_num:032b}'
    broadcast = [
        int(broadcast_bits[i:i+8], 2) for i in range(0, 32, 8)
    ]
    
    # Primer y último host usable
    primer_host_num = ip_num + 1
    ultimo_host_num = broadcast_num - 1
    
    def num_a_ip(n):
        b = f'{n:032b}'
        return '.'.join(str(int(b[i:i+8], 2)) for i in range(0, 32, 8))
    
    return {
        'red': ip_red,
        'prefijo': prefijo,
        'mascara': '.'.join(map(str, mascara)),
        'broadcast': '.'.join(map(str, broadcast)),
        'primer_host': num_a_ip(primer_host_num),
        'ultimo_host': num_a_ip(ultimo_host_num),
        'total_hosts': total_hosts,
        'bits_host': bits_host
    }


def vlsm(ip_base, prefijo_base, necesidades):
    """
    Aplica VLSM: divide una red base en subredes según las necesidades de hosts.
    Las necesidades deben venir ordenadas de mayor a menor (mejor práctica VLSM).
    """
    necesidades_ordenadas = sorted(necesidades, reverse=True)
    subredes = []
    
    # Convertir IP base a número para poder avanzar
    octetos = list(map(int, ip_base.split('.')))
    ip_actual = int(''.join(f'{o:08b}' for o in octetos), 2)
    
    for n_hosts in necesidades_ordenadas:
        # Calcular el prefijo necesario para ese número de hosts
        # 2^(bits_host) - 2 >= n_hosts
        bits_host_necesarios = math.ceil(math.log2(n_hosts + 2))
        prefijo_nuevo = 32 - bits_host_necesarios
        
        # Verificar que no nos salimos de la red base
        if prefijo_nuevo < prefijo_base:
            print(f"Error: no hay espacio suficiente para {n_hosts} hosts")
            continue
        
        ip_subred = f'{ip_actual >> 24}.{(ip_actual >> 16) & 255}.{(ip_actual >> 8) & 255}.{ip_actual & 255}'
        datos = calcular_subred(ip_subred, prefijo_nuevo)
        datos['hosts_requeridos'] = n_hosts
        subredes.append(datos)
        
        # Avanzar al siguiente bloque
        ip_actual += 2 ** bits_host_necesarios
    
    return subredes


# ── Ejecución de ejemplo ──────────────────────────────────────────────────────
if __name__ == '__main__':
    print("=" * 65)
    print("CALCULADORA DE SUBREDES — Practice of Basic Networking Concepts")
    print("=" * 65)
    
    # Ejemplo 1: información de una subred simple
    print("\nEjemplo 1: Análisis de 192.168.1.0/24")
    datos = calcular_subred('192.168.1.0', 24)
    for clave, valor in datos.items():
        print(f"  {clave:<18}: {valor}")
    
    # Ejemplo 2: VLSM con 3 departamentos
    print("\nEjemplo 2: VLSM — Red 10.0.0.0/24")
    print("  Necesidades: Ventas=50 hosts, IT=25 hosts, Gerencia=10 hosts")
    print()
    
    subredes = vlsm('10.0.0.0', 24, [50, 25, 10])
    
    for i, s in enumerate(subredes, 1):
        print(f"  Subred {i} ({s['hosts_requeridos']} hosts requeridos):")
        print(f"    Red:          {s['red']}/{s['prefijo']}")
        print(f"    Máscara:      {s['mascara']}")
        print(f"    Rango hosts:  {s['primer_host']} – {s['ultimo_host']}")
        print(f"    Broadcast:    {s['broadcast']}")
        print(f"    Hosts útiles: {s['total_hosts']}")
        print()
