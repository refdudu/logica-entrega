from dataclasses import dataclass
from typing import Optional

@dataclass
class Order:
    id: int
    node_id: int  # OSMnx Node ID
    deadline: int  # Minutes
    weight: float  # Kg
    is_fragile: bool
    priority_class: int  # 0 (Normal) or 1 (VIP)
    
    # Attributes calculated by AI
    fuzzy_priority: float = 0.0
    risk_level: str = "UNKNOWN"
    
    # New: Cargo integrity tracking
    current_integrity: float = 100.0  # Starts at 100%
    delivered: bool = False
    
    def __post_init__(self):
        # Validation or default processing if needed
        pass
    
    def __repr__(self) -> str:
        return f"Order({self.id}, Fragile={self.is_fragile}, Integrity={self.current_integrity:.1f}%)"
