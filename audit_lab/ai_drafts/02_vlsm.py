def vlsm_allocate(root_cidr: str, host_counts: list) -> list:
    """VLSM allocator: given a root prefix and list of host counts, allocate subnets."""
    ip_str, prefix_len = root_cidr.split('/')
    prefix_len = int(prefix_len)
    
    # Convert IP to integer
    octets = list(map(int, ip_str.split('.')))
    root_ip = (octets[0] << 24) | (octets[1] << 16) | (octets[2] << 8) | octets[3]
    
    # Root network
    root_mask = (0xFFFFFFFF << (32 - prefix_len)) & 0xFFFFFFFF
    root_network = root_ip & root_mask
    root_end = root_network | (~root_mask & 0xFFFFFFFF)
    
    def int_to_dotted(val):
        return f"{(val >> 24) & 0xFF}.{(val >> 16) & 0xFF}.{(val >> 8) & 0xFF}.{val & 0xFF}"
    
    # Sort host counts descending
    sorted_counts = sorted(enumerate(host_counts), key=lambda x: x[1], reverse=True)
    
    cursor = root_network
    results = []
    
    for orig_idx, hosts in sorted_counts:
        # Calculate required block size (hosts + network + broadcast)
        block_size = 1
        while block_size < hosts + 2:
            block_size *= 2
        
        subnet_prefix = 32 - block_size.bit_length() + 1
        subnet_mask = (0xFFFFFFFF << (32 - subnet_prefix)) & 0xFFFFFFFF
        
        # Align cursor to block boundary
        if cursor % block_size != 0:
            cursor = ((cursor // block_size) + 1) * block_size
        
        if cursor + block_size - 1 > root_end:
            raise ValueError(f"Not enough address space for {hosts} hosts")
        
        network = cursor
        broadcast = network + block_size - 1
        
        results.append({
            'original_index': orig_idx,
            'hosts_requested': hosts,
            'network': int_to_dotted(network),
            'prefix': subnet_prefix,
            'mask': int_to_dotted(subnet_mask),
            'broadcast': int_to_dotted(broadcast),
            'usable': block_size - 2,
        })
        
        cursor = broadcast + 1
    
    return results


if __name__ == '__main__':
    result = vlsm_allocate("192.168.1.0/24", [50, 20, 100, 10])
    for r in result:
        print(r)
