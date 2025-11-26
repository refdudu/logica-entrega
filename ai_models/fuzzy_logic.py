import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# --- TÉCNICA 1: LÓGICA FUZZY (Define Prioridade) ---
class FuzzyPriority:
    def __init__(self):
        # Antecedentes
        wait = ctrl.Antecedent(np.arange(0, 121, 1), 'wait')
        dist = ctrl.Antecedent(np.arange(0, 101, 1), 'dist') # Distância relativa ao depósito
        priority = ctrl.Consequent(np.arange(0, 11, 1), 'priority')

        # Pertinência
        wait.automf(3, names=['curto', 'medio', 'longo'])
        dist.automf(3, names=['perto', 'media', 'longe'])
        priority.automf(3, names=['baixa', 'media', 'alta'])

        # Regras: Cliente esperando muito tempo ou perto tem prioridade maior
        rule1 = ctrl.Rule(wait['longo'] | dist['perto'], priority['alta'])
        rule2 = ctrl.Rule(wait['medio'] & dist['media'], priority['media'])
        rule3 = ctrl.Rule(wait['curto'] & dist['longe'], priority['baixa'])

        self.sim = ctrl.ControlSystemSimulation(ctrl.ControlSystem([rule1, rule2, rule3]))

    def calculate(self, order, depot_pos):
        dist_to_depot = np.linalg.norm(np.array([order.x, order.y]) - np.array(depot_pos))
        # Clamp valores para não estourar o range fuzzy
        self.sim.input['wait'] = min(order.wait_time, 120)
        self.sim.input['dist'] = min(dist_to_depot, 100)
        self.sim.compute()
        order.priority = self.sim.output['priority']
        return order
