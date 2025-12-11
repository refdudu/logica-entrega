from typing import List

# Forward reference to avoid circular import
if False:  # TYPE_CHECKING
    from src.models.order import Order

class Truck:
    """Truck model managing cargo as Order objects.
    
    Tracks current cargo load and provides capacity management.
    """
    
    def __init__(self, capacity: float = 30.0) -> None:
        """Initialize truck with specified capacity.
        
        Args:
            capacity: Maximum weight capacity in kg
        """
        self.capacity = capacity
        self.cargo: List['Order'] = []  # Stores Order objects
        self.route: List[int] = []  # List of Node IDs to visit
    
    @property
    def current_load(self) -> float:
        """Calculate current total weight of cargo.
        
        Returns:
            Sum of weights of all orders in cargo
        """
        return sum(order.weight for order in self.cargo)
    
    def can_load(self, weight: float) -> bool:
        """Check if additional weight can be loaded.
        
        Args:
            weight: Weight to check in kg
            
        Returns:
            True if weight can be added without exceeding capacity
        """
        return (self.current_load + weight) <= self.capacity

    def load_order(self, order: 'Order') -> bool:
        """Load an order onto the truck.
        
        Args:
            order: Order object to load
            
        Returns:
            True if order was loaded successfully, False if exceeds capacity
        """
        if self.can_load(order.weight):
            self.cargo.append(order)
            return True
        return False

    def unload_all(self) -> None:
        """Remove all cargo from the truck."""
        self.cargo = []
    
    def get_fragile_cargo(self) -> List['Order']:
        """Get all fragile orders currently in cargo.
        
        Returns:
            List of fragile Order objects
        """
        return [order for order in self.cargo if order.is_fragile]
    
    def reset_load(self) -> None:
        """Deprecated: Use unload_all() instead."""
        self.unload_all()
