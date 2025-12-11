Melhorias de Inteligência Artificial e OtimizaçãoEste documento consolida as alterações finais para elevar o nível do projeto de Logística com IA. As mudanças focam em:Performance: Transformar a Rede Neural em um Singleton para evitar retreino desnecessário.Inteligência: Adicionar consciência de "rotas ruins" na IA, permitindo que ela identifique quando um obstáculo é inevitável.Visualização: Exibir na interface quando a IA foi forçada a tomar uma decisão ruim.1. Modelo de Dados (src/models/order.py)Objetivo: Adicionar o campo unavoidable_bad_road para rastrear se o pedido foi forçado a passar por um caminho ruim.from dataclasses import dataclass
from typing import Optional

@dataclass
class Order:
    id: int
    node_id: int  # OSMnx Node ID
    deadline: int  # Minutes
    weight: float  # Kg
    is_fragile: bool
    priority_class: int  # 0 (Normal) or 1 (VIP)
    
    # Attributes calculated by AI
    fuzzy_priority: float = 0.0
    risk_level: str = "UNKNOWN"
    predicted_time: float = 0.0  # Predicted delivery time in minutes
    delivery_time_estimate: float = 0.0  # Neural network estimate
    
    # New: Cargo integrity tracking
    current_integrity: float = 100.0  # Starts at 100%
    delivered: bool = False
    
    # ✅ NOVO CAMPO: Indica se a IA percebeu que não havia escapatória
    unavoidable_bad_road: bool = False
    
    def __post_init__(self):
        pass
    
    def __repr__(self) -> str:
        return f"Order({self.id}, Fragile={self.is_fragile}, Integrity={self.current_integrity:.1f}%)"
2. Navegador Inteligente (src/ai/astar.py)Objetivo: Adicionar método check_if_bad_road_is_unavoidable para verificar se existe algum caminho alternativo seguro.from typing import List, Tuple
import networkx as nx
import math

class AStarNavigator:
    """Navigator using A* algorithm with real-world constraints."""
    
    def __init__(self, graph: nx.Graph) -> None:
        self.graph = graph

    def _heuristic(self, u: int, v: int) -> float:
        try:
            pos_u = (self.graph.nodes[u]['x'], self.graph.nodes[u]['y'])
            pos_v = (self.graph.nodes[v]['x'], self.graph.nodes[v]['y'])
            dx = pos_u[0] - pos_v[0]
            dy = pos_u[1] - pos_v[1]
            return math.sqrt(dx * dx + dy * dy)
        except (KeyError, TypeError):
            return 0.0

    # ✅ NOVO MÉTODO
    def check_if_bad_road_is_unavoidable(self, start_node: int, end_node: int) -> bool:
        """
        Verifica se é IMPOSSÍVEL chegar ao destino sem passar por obstáculos.
        Retorna True se o único caminho possível tiver asfalto ruim ou bloqueios.
        """
        def is_safe_edge(u, v, k):
            data = self.graph.edges[u, v, k]
            if data.get('road_block', False): return False
            if data.get('pavement_quality') == 'bad': return False
            return True

        # Cria subgrafo apenas com ruas boas
        safe_graph = nx.subgraph_view(self.graph, filter_edge=is_safe_edge)
        return not nx.has_path(safe_graph, start_node, end_node)

    def get_path(self, start_node: int, end_node: int, is_fragile: bool = False) -> List[int]:
        def weight_function(u, v, d):
            base_cost = d.get('length', 100)
            road_block_factor = 15.0 if d.get('road_block', False) else 1.0
            
            pavement_penalty = 1.0
            if d.get('pavement_quality') == 'bad':
                if is_fragile:
                    pavement_penalty = 40.0
                    if base_cost < 200: pavement_penalty *= 2.0
                else:
                    pavement_penalty = 1.4

            traffic_factor = 1.0 + d.get('traffic_level', 0.0)
            return base_cost * road_block_factor * pavement_penalty * traffic_factor

        try:
            return nx.astar_path(self.graph, start_node, end_node, heuristic=self._heuristic, weight=weight_function)
        except nx.NetworkXNoPath:
            return []
        except Exception as e:
            print(f"Pathfinding error: {e}")
            return []

    def get_path_cost(self, start_node: int, end_node: int, is_fragile: bool = False) -> float:
        # (Mesma lógica do get_path para weight_function)
        # ... Implementação omitida para brevidade (usar a mesma do arquivo original com a weight_function acima) ...
        pass
3. Cérebro Neural Otimizado (src/ai/neural.py)Objetivo: Implementar Singleton e adicionar feature bad_road_ratio (7ª entrada) para prever atrasos causados por buracos.import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from datetime import datetime
import random

class NeuralPredictor:
    """Singleton Neural Network Predictor."""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(NeuralPredictor, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, seed: int = 42) -> None:
        if self.initialized: return

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
        X, y = [], []
        for _ in range(n_samples):
            hora = random.randint(0, 23)
            dia = random.randint(0, 6)
            dist = random.uniform(0.5, 25.0)
            peso = random.uniform(1, 30)
            fragil = random.choice([0, 1])
            trafego = random.uniform(0, 1)
            
            # ✅ NOVA FEATURE
            bad_ratio = random.uniform(0, 0.5) 
            
            tempo_base = dist * 2.5
            if 7 <= hora <= 9 or 17 <= hora <= 19: tempo_base *= 1.5
            if dia_semana >= 5: tempo_base *= 0.8
            if fragil: tempo_base *= 1.2
            
            # ✅ Penalidade por rua ruim
            if bad_ratio > 0.1: tempo_base *= (1.0 + bad_ratio)
            
            tempo_base += trafego * 15 + random.gauss(0, 2)
            
            X.append([hora, dia, dist, peso, fragil, trafego, bad_ratio])
            y.append(max(5, tempo_base))
        
        return np.array(X), np.array(y)
    
    def _build_model(self) -> tf.keras.Model:
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(32, activation='relu', input_shape=(7,)), # ✅ 7 Features
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(8, activation='relu'),
            tf.keras.layers.Dense(1, activation='linear')
        ])
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model
    
    def _train(self) -> None:
        X, y = self._generate_training_data(1000)
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=self.seed)
        
        X_train = self.scaler_X.fit_transform(X_train)
        X_val = self.scaler_X.transform(X_val)
        y_train = self.scaler_y.fit_transform(y_train.reshape(-1, 1)).ravel()
        y_val = self.scaler_y.transform(y_val.reshape(-1, 1)).ravel()
        
        self.model = self._build_model()
        self.model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=50, batch_size=32, verbose=0)
        print("[NeuralPredictor] Treinamento concluído.")
    
    def predict(self, order, distance: float, bad_road_ratio: float = 0.0) -> float:
        hora = datetime.now().hour
        dia = datetime.now().weekday()
        
        features = np.array([[hora, dia, distance/1000, order.weight, 
                            1 if order.is_fragile else 0, 0.5, bad_road_ratio]])
        
        features_scaled = self.scaler_X.transform(features)
        pred_time = self.scaler_y.inverse_transform([[self.model.predict(features_scaled, verbose=0)[0][0]]])[0][0]
        
        predicted_time = max(5.0, pred_time)
        order.delivery_time_estimate = round(predicted_time, 1)
        
        if hasattr(order, 'deadline'):
            if predicted_time > order.deadline: order.risk_level = "HIGH"
            elif predicted_time > order.deadline * 0.8: order.risk_level = "MEDIUM"
            else: order.risk_level = "LOW"
        
        return predicted_time
4. Simulador Integrador (src/core/simulator.py)Objetivo: Calcular o bad_road_ratio real do trajeto e verificar inevitabilidade antes de chamar a IA.# Apenas o método _run_smart precisa ser atualizado, o restante permanece igual.

    def _run_smart(self) -> Dict[str, float]:
        print("Running Smart Simulation (AI Pipeline)...")
        
        for order in self.orders:
            # 1. Analisa caminho
            path = self.astar.get_path(self.depot_node, order.node_id, is_fragile=order.is_fragile)
            
            dist_meters = 0
            bad_meters = 0
            
            if path:
                for i in range(len(path) - 1):
                    u, v = path[i], path[i+1]
                    data = self.graph.get_edge_data(u, v)[0]
                    length = data.get('length', 100)
                    dist_meters += length
                    
                    if data.get('pavement_quality') == 'bad' or data.get('road_block'):
                        bad_meters += length
            
            # 2. Calcula Ratio e Inevitabilidade
            ratio = (bad_meters / dist_meters) if dist_meters > 0 else 0.0
            
            if bad_meters > 0:
                # ✅ Verifica se a IA foi "forçada"
                order.unavoidable_bad_road = self.astar.check_if_bad_road_is_unavoidable(self.depot_node, order.node_id)
            else:
                order.unavoidable_bad_road = False

            # 3. Predição com nova feature
            self.neural.predict(order, dist_meters, bad_road_ratio=ratio)
            self.fuzzy.calculate(order, dist_meters)
        
        # ... (restante do método igual: GA optimization, etc) ...
5. Interface de Usuário (ui/control_panel.py)Objetivo: Exibir a coluna "Obs" para mostrar "⚠️ Inevitável" quando a IA não teve escolha.# No método __init__:
        # ✅ ADICIONADA COLUNA 'Obs'
        self.tree = ttk.Treeview(self, columns=('ID', 'Peso', 'Prazo', 'VIP', 'Pri', 'Risco', 'Obs'), show='headings', height=12)
        # ... (outros headings) ...
        self.tree.heading('Obs', text='Obs')
        self.tree.column('Obs', width=80)
        self.tree.pack(pady=20, fill=tk.X)

# No método update_table:
    def update_table(self, orders):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        for o in orders:
            vip_str = "Sim" if o.priority_class == 1 else "Não"
            
            # ✅ Lógica visual
            obs = ""
            if getattr(o, 'unavoidable_bad_road', False):
                obs = "⚠️ Inevitável"
            elif o.risk_level == "HIGH":
                obs = "Atraso!"
            
            self.tree.insert('', 'end', values=(
                o.id, o.weight, int(o.deadline), vip_str, 
                f"{o.fuzzy_priority:.1f}", o.risk_level, obs
            ))
