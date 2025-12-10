import numpy as np
from sklearn.neural_network import MLPClassifier

class NeuralPredictor:
    def __init__(self):
        # Mock Training Data
        # Features: [Weight, PriorityClass (0/1), FuzzyPriority (0-10)]
        # Target: 0 (On Time), 1 (Late/High Risk)
        X_train = [
            [2, 0, 8], [20, 1, 2], [5, 0, 5], [30, 1, 9], 
            [1, 1, 4], [15, 0, 6], [10, 1, 5], [25, 1, 3],
            [35, 1, 9], [40, 0, 2], [28, 1, 8], [12, 0, 4] 
        ]
        y_train = [0, 1, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0] 

        self.clf = MLPClassifier(hidden_layer_sizes=(8, 4), max_iter=1000, random_state=42)
        self.clf.fit(X_train, y_train)

    def predict(self, order):
        # Ensure fuzzy_priority is calculated before calling this
        features = [[order.weight, order.priority_class, order.fuzzy_priority]]
        
        try:
            pred_class = self.clf.predict(features)[0]
            # Probabilities: [Prob(0), Prob(1)]
            prob_risk = self.clf.predict_proba(features)[0][1]
            
            order.risk_level = "HIGH" if pred_class == 1 else "LOW"
            # We could attach risk_prob to order if we wanted to
        except Exception as e:
            print(f"Neural Prediction Error: {e}")
            order.risk_level = "UNKNOWN"
            
        return order
