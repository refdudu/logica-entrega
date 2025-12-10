from typing import List

class Truck:
    def __init__(self, capacity: float = 30.0):
        self.capacity = capacity
        self.current_load = 0.0
        self.route: List[int] = []  # List of Node IDs to visit
    
    def can_load(self, weight: float) -> bool:
        return (self.current_load + weight) <= self.capacity

    def load(self, weight: float):
        if self.can_load(weight):
            self.current_load += weight
            return True
        return False

    def reset_load(self):
        self.current_load = 0.0
