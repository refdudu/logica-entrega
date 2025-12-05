import random
import time

class TrafficLightManager:
    def __init__(self, grid_size=20, cycle_duration=3.0):
        self.grid_size = grid_size
        self.lights = {}  # (x, y) -> 'RED' or 'GREEN'
        self.intersections = []
        self.cycle_duration = cycle_duration
        self.last_switch_time = time.time()

    def add_intersection(self, x, y):
        """Registers an intersection and initializes a traffic light there."""
        self.intersections.append((x, y))
        # Randomly assign initial state to desynchronize slightly if needed
        self.lights[(x, y)] = random.choice(['RED', 'GREEN'])

    def update(self):
        """Toggles lights if the cycle duration has passed."""
        current_time = time.time()
        if current_time - self.last_switch_time > self.cycle_duration:
            for pos in self.lights:
                self.lights[pos] = 'GREEN' if self.lights[pos] == 'RED' else 'RED'
            self.last_switch_time = current_time
            return True # State changed
        return False

    def get_state(self, x, y):
        return self.lights.get((x, y), 'GREEN') # Default to GREEN if no light
