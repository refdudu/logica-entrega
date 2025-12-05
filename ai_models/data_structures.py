import numpy as np

# Estrutura de Dados para um Pedido
class Order:
    def __init__(self, id, node_id, weight, deadline, priority_class):
        self.id = id
        self.node_id = node_id # Graph Node ID
        self.weight = weight
        self.deadline = deadline
        self.priority_class = priority_class
        
        # AI Analysis Results
        self.priority = 0.0
        self.delay_risk = "BAIXO" # Rede Neural
        self.risk_prob = 0.0
