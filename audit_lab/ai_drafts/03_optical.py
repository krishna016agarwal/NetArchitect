def check_optical_budget(link_type: str, distance_km: float) -> dict:
    """Check if a 10GBASE-LR/ER fiber link has enough optical power budget."""
    
    # Transceiver specs
    specs = {
        'LR': {
            'wavelength': 1310,  # nm
            'max_reach': 10,     # km
            'tx_power': -8.2,    # dBm (min)
            'rx_sensitivity': -14.4,  # dBm
        },
        'ER': {
            'wavelength': 1550,  # nm
            'max_reach': 40,     # km
            'tx_power': -4.7,    # dBm (min)
            'rx_sensitivity': -15.8,  # dBm
        },
    }
    
    if link_type not in specs:
        raise ValueError(f"Unknown link type: {link_type}. Must be LR or ER.")
    
    spec = specs[link_type]
    
    # Power budget
    budget = spec['tx_power'] - spec['rx_sensitivity']
    
    # Fiber attenuation
    attenuation_per_km = 0.35 if spec['wavelength'] == 1310 else 0.22
    fiber_loss = distance_km * attenuation_per_km
    
    # Connector loss (2 connectors, 0.5 dB each)
    connector_loss = 2 * 0.5
    
    # Splice loss (1 splice per km, 0.1 dB each)
    splice_loss = distance_km * 0.1
    
    # Safety margin
    safety_margin = 3.0  # dB
    
    total_loss = fiber_loss + connector_loss + splice_loss + safety_margin
    
    margin = budget - total_loss
    
    return {
        'link_type': link_type,
        'distance_km': distance_km,
        'budget_dB': round(budget, 2),
        'total_loss_dB': round(total_loss, 2),
        'margin_dB': round(margin, 2),
        'feasible': margin >= 0,
    }


if __name__ == '__main__':
    print(check_optical_budget('LR', 8))
    print(check_optical_budget('ER', 35))
