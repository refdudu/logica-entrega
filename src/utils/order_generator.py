"""
Order Generator Utility

Provides reproducible order generation for benchmarking and testing.
"""

import random
from typing import List

from src.models.order import Order


def generate_test_orders(map_manager, count: int, seed: int = 42) -> List[Order]:
    """Generate test orders with reproducible randomness.
    
    Args:
        map_manager: MapManager instance with loaded graph
        count: Number of orders to generate
        seed: Random seed for reproducibility
        
    Returns:
        List of Order objects with randomized but reproducible attributes
    """
    random.seed(seed)
    orders = []
    
    for i in range(count):
        node_id = map_manager.get_random_node()
        
        order = Order(
            id=i + 1,
            node_id=node_id,
            deadline=random.randint(10, 120),  # 10 to 120 minutes
            weight=random.uniform(1.0, 8.0),   # 1 to 8 kg
            is_fragile=random.choice([True, False]),
            priority_class=random.choice([0, 1])  # Normal or VIP
        )
        orders.append(order)
    
    # Reset random state to not affect other parts of the program
    random.seed()
    
    return orders
