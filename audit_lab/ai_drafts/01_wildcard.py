def wildcard_and_broadcast(cidr: str) -> dict:
    """Compute wildcard mask and broadcast address for an IPv4 CIDR prefix."""
    ip_str, prefix_len = cidr.split('/')
    prefix_len = int(prefix_len)
    
    # Convert IP to integer
    octets = list(map(int, ip_str.split('.')))
    ip_int = (octets[0] << 24) | (octets[1] << 16) | (octets[2] << 8) | octets[3]
    
    # Compute subnet mask
    if prefix_len == 0:
        mask = 0
    else:
        mask = (0xFFFFFFFF << (32 - prefix_len)) & 0xFFFFFFFF
    
    # Wildcard is the inverse of the mask
    wildcard = ~mask & 0xFFFFFFFF
    
    # Network address
    network = ip_int & mask
    
    # Broadcast = network OR wildcard
    broadcast = network | wildcard
    
    def int_to_dotted(val):
        return f"{(val >> 24) & 0xFF}.{(val >> 16) & 0xFF}.{(val >> 8) & 0xFF}.{val & 0xFF}"
    
    return {
        'network': int_to_dotted(network),
        'mask': int_to_dotted(mask),
        'wildcard': int_to_dotted(wildcard),
        'broadcast': int_to_dotted(broadcast),
    }


if __name__ == '__main__':
    print(wildcard_and_broadcast("192.168.1.0/24"))
    print(wildcard_and_broadcast("10.0.0.0/8"))
    print(wildcard_and_broadcast("172.16.0.0/12"))
