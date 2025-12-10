import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

class FuzzyPriority:
    def __init__(self):
        # Antecedents
        # Deadline: 0 to 120 minutes. Shorter is more urgent.
        deadline = ctrl.Antecedent(np.arange(0, 121, 1), 'deadline')
        # Distance: 0 to 5000 meters/units.
        dist = ctrl.Antecedent(np.arange(0, 5001, 10), 'dist')
        # Consequent: Priority (0 to 10)
        priority = ctrl.Consequent(np.arange(0, 11, 1), 'priority')

        # Membership Functions
        deadline.automf(3, names=['short', 'medium', 'long'])
        dist.automf(3, names=['close', 'medium', 'far'])
        priority.automf(3, names=['low', 'medium', 'high'])

        # Rules
        # Short deadline OR Close distance -> High Priority
        rule1 = ctrl.Rule(deadline['short'] | dist['close'], priority['high'])
        # Medium deadline AND Medium distance -> Medium Priority
        rule2 = ctrl.Rule(deadline['medium'] & dist['medium'], priority['medium'])
        # Long deadline AND Far distance -> Low Priority
        rule3 = ctrl.Rule(deadline['long'] & dist['far'], priority['low'])

        self.control_system = ctrl.ControlSystem([rule1, rule2, rule3])
        self.sim = ctrl.ControlSystemSimulation(self.control_system)

    def calculate(self, order, distance):
        self.sim.input['deadline'] = min(order.deadline, 120)
        self.sim.input['dist'] = min(distance, 5000)
        
        try:
            self.sim.compute()
            order.fuzzy_priority = self.sim.output['priority']
        except Exception as e:
            # Fallback if fuzzy inputs are out of bounds or other error
            print(f"Fuzzy Error: {e}")
            order.fuzzy_priority = 5.0
            
        return order
