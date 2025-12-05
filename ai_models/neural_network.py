import numpy as np
from sklearn.neural_network import MLPClassifier

# --- TÉCNICA 2: REDE NEURAL (Previsão de Atraso) ---
class NeuralPredictor:
    def __init__(self):
        # Treinamento Simulado (Mock Training)
        # Features: [Peso, PriorityClass, Prioridade(Fuzzy)]
        # PriorityClass: 0 (Normal), 1 (VIP)
        # A rede aprende que Peso alto + VIP = Atraso (exemplo)
        X_train = [
            [2, 0, 8], [20, 1, 2], [5, 0, 5], [30, 1, 9], 
            [1, 1, 4], [15, 0, 6], [10, 1, 5], [25, 1, 3]
        ]
        y_train = [0, 1, 0, 1, 0, 0, 1, 1] # 0 = No Prazo, 1 = Atraso

        self.clf = MLPClassifier(hidden_layer_sizes=(8, 4), max_iter=1000, random_state=42)
        self.clf.fit(X_train, y_train)

    def predict(self, order):
        # Usa a prioridade calculada pelo Fuzzy como input!
        features = [[order.weight, order.priority_class, order.priority]]
        pred = self.clf.predict(features)[0]
        prob = self.clf.predict_proba(features)[0][pred]
        
        order.delay_risk = "ALTO" if pred == 1 else "BAIXO"
        order.risk_prob = prob
        return order
