"""
Neural Network Predictor module.

Uses MLPRegressor to predict delivery time based on order features.
"""

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler


class NeuralPredictor:
    """Neural network for predicting delivery time.
    
    Uses a Multi-Layer Perceptron (MLP) regressor trained on synthetic
    data to predict estimated delivery time for orders.
    """
    
    def __init__(self) -> None:
        """Initialize and train the neural network."""
        self.scaler = StandardScaler()
        self.model = MLPRegressor(
            hidden_layer_sizes=(10, 5),
            max_iter=1000,
            random_state=42,
            early_stopping=True
        )
        self._train()
    
    def _train(self) -> None:
        """Train the model on synthetic data.
        
        Features: [distance_km, weight, deadline, traffic_level]
        Target: estimated_time_minutes
        """
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 200
        
        # Features
        distances = np.random.uniform(0.5, 10.0, n_samples)      # km
        weights = np.random.uniform(1.0, 30.0, n_samples)        # kg
        deadlines = np.random.uniform(10, 120, n_samples)        # minutes
        traffic = np.random.uniform(0.0, 1.0, n_samples)         # 0-1 level
        
        X_train = np.column_stack([distances, weights, deadlines, traffic])
        
        # Target: Estimated time (synthetic but realistic formula)
        # Time = base + distance_factor + weight_penalty + traffic_delay
        base_time = 5.0  # Base delivery time in minutes
        y_train = (
            base_time +
            distances * 3.0 +                   # 3 min per km
            weights * 0.1 +                     # 0.1 min per kg
            traffic * 10.0 +                    # up to 10 min traffic delay
            np.random.normal(0, 2, n_samples)   # noise
        )
        y_train = np.maximum(y_train, 5.0)  # Minimum 5 minutes
        
        # Normalize features
        X_normalized = self.scaler.fit_transform(X_train)
        
        # Train model
        self.model.fit(X_normalized, y_train)
    
    def predict(self, order, distance: float = 1.0, traffic: float = 0.5):
        """Predict delivery time for an order.
        
        Args:
            order: Order object with weight, deadline attributes
            distance: Estimated distance in km
            traffic: Traffic level 0-1
            
        Returns:
            The order with predicted_time attribute set
        """
        try:
            # Build feature vector
            features = np.array([[
                distance,
                order.weight,
                order.deadline,
                traffic
            ]])
            
            # Normalize and predict
            features_normalized = self.scaler.transform(features)
            predicted_time = self.model.predict(features_normalized)[0]
            
            # Ensure reasonable value
            predicted_time = max(5.0, predicted_time)
            
            # Set on order
            order.predicted_time = round(predicted_time, 1)
            
            # Also set risk level based on prediction vs deadline
            if predicted_time > order.deadline:
                order.risk_level = "HIGH"
            elif predicted_time > order.deadline * 0.8:
                order.risk_level = "MEDIUM"
            else:
                order.risk_level = "LOW"
                
        except Exception as e:
            print(f"Neural Prediction Error: {e}")
            order.predicted_time = 30.0  # Default estimate
            order.risk_level = "UNKNOWN"
        
        return order
