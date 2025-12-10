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
    
    def __post_init__(self):
        # Validation or default processing if needed
        pass
