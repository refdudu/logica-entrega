"""
Módulo de Predição de Tempo de Entrega usando Rede Neural Artificial.

Implementa rede neural com TensorFlow para estimar o tempo
real de entrega baseado em características do pedido e condições da rota.

Dataset de Treino:
- 1000 exemplos sintéticos realistas
- Features: hora do dia, dia da semana, distância, peso, fragilidade, tráfego
- Target: tempo de entrega (minutos)

Arquitetura:
- Camada de entrada: 6 neurônios (features)
- Camada oculta 1: 32 neurônios (ReLU) + Dropout(0.3)
- Camada oculta 2: 16 neurônios (ReLU) + Dropout(0.2)
- Camada oculta 3: 8 neurônios (ReLU)
- Camada de saída: 1 neurônio (regressão linear)
"""

import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from datetime import datetime
import random


class NeuralPredictor:
    """Singleton Neural Network Predictor com TensorFlow.
    
    Treina uma vez e reutiliza o modelo em todas as instâncias,
    considerando hora do dia, dia da semana, distância, peso, fragilidade,
    tráfego e proporção de estradas ruins (bad_road_ratio).
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Implementação do Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(NeuralPredictor, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, seed: int = 42) -> None:
        """Inicializa e treina a rede neural (apenas uma vez devido ao Singleton).
        
        Args:
            seed: Semente para reprodutibilidade
        """
        if self.initialized:
            return
        
        print("[NeuralPredictor] Inicializando Singleton e treinando modelo...")
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        tf.random.set_seed(seed)
        
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        self.model = None
        self._train()
        self.initialized = True
    
    def _generate_training_data(self, n_samples: int = 1000) -> tuple:
        """Gera dataset sintético realista para treinamento.
        
        Features:
        - hora_dia: 0-23
        - dia_semana: 0-6 (0=segunda, 6=domingo)
        - distancia_km: 0.5-25.0
        - peso_kg: 1-30
        - eh_fragil: 0 ou 1
        - trafego: 0-1 (0=livre, 1=congestionado)
        - ✅ bad_road_ratio: 0-0.5 (proporção de estradas ruins no trajeto)
        
        Returns:
            Tuple (X, y) com features e targets
        """
        X = []
        y = []
        
        for _ in range(n_samples):
            # Features realistas
            hora = random.randint(0, 23)
            dia_semana = random.randint(0, 6)
            distancia = random.uniform(0.5, 25.0)
            peso = random.uniform(1, 30)
            fragil = random.choice([0, 1])
            trafego = random.uniform(0, 1)
            
            # ✅ NOVA FEATURE: Proporção de estradas ruins (0% a 50%)
            bad_ratio = random.uniform(0, 0.5)
            
            # Tempo calculado com lógica realista
            tempo_base = distancia * 2.5  # ~2.5 min/km em cidade
            
            # Ajustes realistas
            if 7 <= hora <= 9 or 17 <= hora <= 19:  # Horário de pico
                tempo_base *= 1.5
            if dia_semana >= 5:  # Final de semana
                tempo_base *= 0.8
            if fragil:  # Carga frágil = mais cuidado
                tempo_base *= 1.2
            
            # ✅ Penalidade por rua ruim (quanto maior o ratio, mais devagar)
            if bad_ratio > 0.1:
                tempo_base *= (1.0 + bad_ratio)
                tempo_base += trafego * 15  # Tráfego adiciona até 15min
            tempo_base += random.gauss(0, 2)  # Ruído realista
            
            X.append([hora, dia_semana, distancia, peso, fragil, trafego, bad_ratio])
            y.append(max(5, tempo_base))  # Mínimo 5 min
        
        return np.array(X), np.array(y)
    
    def _build_model(self) -> tf.keras.Model:
        """Constrói e compila a RNA com TensorFlow.
        
        Returns:
            Modelo Keras compilado
        """
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(32, activation='relu', input_shape=(7,)),  # ✅ 7 Features
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(8, activation='relu'),
            tf.keras.layers.Dense(1, activation='linear')  # Regressão
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def _train(self) -> None:
        """Treina o modelo com dados sintéticos usando TensorFlow."""
        X, y = self._generate_training_data(1000)
        
        # Split train/validation
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=self.seed)
        
        # Normalização
        X_train = self.scaler_X.fit_transform(X_train)
        X_val = self.scaler_X.transform(X_val)
        y_train = self.scaler_y.fit_transform(y_train.reshape(-1, 1)).ravel()
        y_val = self.scaler_y.transform(y_val.reshape(-1, 1)).ravel()
        
        # Constrói e treina modelo
        self.model = self._build_model()
        
        # Treinamento silencioso
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=50,
            batch_size=32,
            verbose=0
        )
        
        # Calcula métricas finais
        final_loss = history.history['loss'][-1]
        final_mae = history.history['mae'][-1]
        
        print(f"[NeuralPredictor] Treinamento concluído. Loss: {final_loss:.4f}, MAE: {final_mae:.2f} min")
    
    def predict(self, order, distance: float, bad_road_ratio: float = 0.0) -> float:
        """Prediz tempo de entrega para um pedido usando RNA treinada.
        
        Args:
            order: Objeto Order com atributos weight, is_fragile
            distance: Distância em metros até o destino
            bad_road_ratio: ✅ Proporção de estradas ruins no trajeto (0.0 a 1.0)
            
        Returns:
            Tempo estimado de entrega em minutos
        """
        # Extrai features do contexto atual
        hora = datetime.now().hour
        dia = datetime.now().weekday()
        distancia_km = distance / 1000.0
        peso = order.weight
        fragil = 1 if order.is_fragile else 0
        trafego = random.uniform(0.3, 0.8)  # Simula API de tráfego
        
        # ✅ Monta vetor com 7 features (incluindo bad_road_ratio)
        features = np.array([[hora, dia, distancia_km, peso, fragil, trafego, bad_road_ratio]])
        
        # Normaliza e prediz
        features_scaled = self.scaler_X.transform(features)
        pred_scaled = self.model.predict(features_scaled, verbose=0)[0][0]
        pred_time = self.scaler_y.inverse_transform([[pred_scaled]])[0][0]
        
        # Garante valor mínimo
        predicted_time = max(5.0, pred_time)
        
        # Salva no pedido
        order.delivery_time_estimate = round(predicted_time, 1)
        
        # Define risk_level baseado em deadline
        if hasattr(order, 'deadline'):
            if predicted_time > order.deadline:
                order.risk_level = "HIGH"
            elif predicted_time > order.deadline * 0.8:
                order.risk_level = "MEDIUM"
            else:
                order.risk_level = "LOW"
        
        return predicted_time
