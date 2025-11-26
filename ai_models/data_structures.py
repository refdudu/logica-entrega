import numpy as np

# Estrutura de Dados para um Pedido
class Order:
    def __init__(self, id, x, y, wait_time, weight, rain):
        self.id = id
        self.x = x
        self.y = y
        self.wait_time = wait_time # minutos
        self.weight = weight # kg
        self.rain = rain # 0 ou 1
        
        # Serão preenchidos pelas IAs
        self.priority = 0.0 # Fuzzy
        self.delay_risk = "" # Rede Neural
        self.risk_prob = 0.0
