import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# --- TÉCNICA 1: LÓGICA FUZZY (Define Prioridade) ---
class FuzzyPriority:
    def __init__(self):
        # Antecedentes
        # Deadline: 0 a 120 minutos. Menor é mais urgente.
        deadline = ctrl.Antecedent(np.arange(0, 121, 1), 'deadline')
        dist = ctrl.Antecedent(np.arange(0, 5000, 100), 'dist') # Distância em metros ou segundos (ajustar range)
        priority = ctrl.Consequent(np.arange(0, 11, 1), 'priority')

        # Pertinência
        deadline.automf(3, names=['curto', 'medio', 'longo'])
        dist.automf(3, names=['perto', 'media', 'longe'])
        priority.automf(3, names=['baixa', 'media', 'alta'])

        # Regras: 
        # Deadline curto -> Prioridade Alta
        # Distancia perto -> Prioridade Alta (ou talvez longe precise de mais prioridade para compensar?)
        # Vamos manter: Perto = Alta prioridade (para limpar rápido)
        
        rule1 = ctrl.Rule(deadline['curto'] | dist['perto'], priority['alta'])
        rule2 = ctrl.Rule(deadline['medio'] & dist['media'], priority['media'])
        rule3 = ctrl.Rule(deadline['longo'] & dist['longe'], priority['baixa'])

        self.sim = ctrl.ControlSystemSimulation(ctrl.ControlSystem([rule1, rule2, rule3]))

    def calculate(self, order, distance):
        # Clamp valores
        self.sim.input['deadline'] = min(order.deadline, 120)
        self.sim.input['dist'] = min(distance, 5000) # Assumindo max 5km ou 5000s
        self.sim.compute()
        order.priority = self.sim.output['priority']
        return order
