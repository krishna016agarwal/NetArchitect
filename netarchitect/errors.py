"""
errors.py — Custom exceptions for NetArchitect.
CLI catches these, prints clear message, exits code 2, no stack trace.
"""


class NetArchitectError(Exception):
    """Base exception for all NetArchitect errors."""
    pass


class InvalidParameterError(NetArchitectError):
    """Raised when an input parameter fails validation."""
    pass


class PhysicalDistanceViolationError(NetArchitectError):
    """Raised when copper media is requested but distance exceeds 100 m.

    Message includes signal attenuation/crosstalk warning and the 100 m limit.
    """
    def __init__(self, link_name: str, distance_m: float):
        self.link_name = link_name
        self.distance_m = distance_m
        super().__init__(
            f"Physical distance violation on link '{link_name}': "
            f"{distance_m} m exceeds the 100 m maximum for Cat6a copper cabling "
            f"(IEEE 802.3an). Beyond 100 m, signal attenuation and crosstalk "
            f"degrade 10GBASE-T to unacceptable BER levels. "
            f"Use fiber optic media instead."
        )


class AddressSpaceExhaustedError(NetArchitectError):
    """Raised when VLSM allocation cannot fit all subnets into the root prefix."""
    def __init__(self, requested: int, available: int, root_prefix: str):
        self.requested = requested
        self.available = available
        self.root_prefix = root_prefix
        super().__init__(
            f"Address space exhausted in {root_prefix}: "
            f"need {requested} addresses but only {available} remain. "
            f"Consider using a larger root prefix or reducing host counts."
        )


class OpticalBudgetError(NetArchitectError):
    """Raised when no transceiver can meet optical budget for a fiber link."""
    def __init__(self, link_name: str, distance_km: float, best_margin_db: float):
        self.link_name = link_name
        self.distance_km = distance_km
        self.best_margin_db = best_margin_db
        super().__init__(
            f"Optical budget exceeded on link '{link_name}' ({distance_km} km): "
            f"best available margin is {best_margin_db:.2f} dB (negative = insufficient). "
            f"Consider optical amplification (EDFA) or signal regeneration."
        )
