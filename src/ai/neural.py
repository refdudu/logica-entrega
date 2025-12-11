"""
Módulo de Predição de Tempo de Entrega usando Rede Neural Artificial.

Implementa MLPRegressor (Multi-Layer Perceptron) para estimar o tempo
real de entrega baseado em características do pedido e condições da rota.

Dataset de Treino:
- 100 exemplos sintéticos
- Features: distância, peso, prazo, tráfego
- Target: tempo de entrega (minutos)

Arquitetura:
- Camada de entrada: 4 neurônios (features)
- Camada oculta 1: 10 neurônios (ReLU)
- Camada oculta 2: 5 neurônios (ReLU)
- Camada de saída: 1 neurônio (tempo)
"""

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
import random


class NeuralPredictor:
    """Preditor de tempo de entrega usando Rede Neural Artificial (RNA).
    
    Treina com dataset sintético baseado em simulações realistas de entregas
    considerando distância, peso da carga, prazo e condições de tráfego.
    """
    
    def __init__(self, seed: int = 42) -> None:
        """Inicializa e treina a rede neural.
        
        Args:
            seed: Semente para reprodutibilidade
        """
        self.seed = seed
        self.scaler = StandardScaler()
        self.model = MLPRegressor(
            hidden_layer_sizes=(10, 5),
            activation='relu',
            solver='adam',
            max_iter=2000,
            random_state=seed,
            early_stopping=True,
            validation_fraction=0.1
        )
        self._train()
    
    def _generate_training_data(self) -> tuple:
        """Gera dataset sintético para treinamento.
        
        Returns:
            Tuple (X, y) com features e targets
        """
        random.seed(self.seed)
        np.random.seed(self.seed)
        
        X = []
        y = []
        
        for _ in range(100):
            # Features realistas
            distance = random.uniform(1000, 30000)  # 1-30km em metros
            weight = random.uniform(1, 30)          # 1-30kg
            deadline = random.uniform(10, 120)      # 10-120min
            traffic = random.uniform(0.0, 1.0)      # 0-100%
            
            # Cálculo do tempo de entrega (target)
            # Base: velocidade média de 30km/h = 500m/min
            base_time = distance / 500
            
            # Penalidade por peso (cargas pesadas = mais tempo de carga/descarga)
            weight_penalty = weight * 0.1
            
            # Penalidade por tráfego (até 50% mais lento)
            traffic_penalty = traffic * base_time * 0.5
            
            # Tempo total com pequena variação aleatória
            delivery_time = base_time + weight_penalty + traffic_penalty
            delivery_time += random.uniform(-2, 2)  # Variação de ±2min
            delivery_time = max(5, delivery_time)   # Mínimo 5min
            
            X.append([distance, weight, deadline, traffic])
            y.append(delivery_time)
        
        return np.array(X), np.array(y)
    
    def _train(self) -> None:
        """Treina o modelo com dados sintéticos."""
        X, y = self._generate_training_data()
        
        # Normaliza features
        X_scaled = self.scaler.fit_transform(X)
        
        # Treina modelo
        self.model.fit(X_scaled, y)
        
        # Calcula RMSE de treino
        predictions = self.model.predict(X_scaled)
        mse = np.mean((predictions - y) ** 2)
        rmse = np.sqrt(mse)
        
        print(f"[NeuralPredictor] Treinamento concluído. RMSE: {rmse:.2f} min")
    
    def predict(self, order, distance: float) -> float:
        """Prediz tempo de entrega para um pedido.
        
        Args:
            order: Objeto Order com atributos weight, deadline
            distance: Distância em metros até o destino
            
        Returns:
            Tempo estimado de entrega em minutos
        """
        # Gera tráfego simulado (poderia vir do mapa real)
        traffic = random.uniform(0.0, 1.0)
        
        # Monta vetor de features
        features = np.array([[
            distance,
            order.weight,
            order.deadline,
            traffic
        ]])
        
        # Normaliza e prediz
        features_scaled = self.scaler.transform(features)
        predicted_time = self.model.predict(features_scaled)[0]
        
        # Garante valor mínimo
        predicted_time = max(5.0, predicted_time)
        
        # Salva no pedido
        order.delivery_time_estimate = round(predicted_time, 1)
        
        # Define risk_level baseado em deadline
        if predicted_time > order.deadline:
            order.risk_level = "HIGH"
        elif predicted_time > order.deadline * 0.8:
            order.risk_level = "MEDIUM"
        else:
            order.risk_level = "LOW"
        
        return predicted_time
