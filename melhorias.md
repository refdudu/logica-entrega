✅ FASE 1: CORRIGIR IMPLEMENTAÇÕES FAKES (PRIORIDADE MÁXIMA)
1.1 Rede Neural Real com TensorFlow
Arquivo: src/ai/neural.py

Problema atual:

python
# FAKE - apenas retorna número aleatório
self.model = lambda x: np.random.uniform(50, 95)
Implementação correta:

 Instalar dependências necessárias

python
# requirements.txt
tensorflow>=2.13.0
scikit-learn>=1.3.0
 Criar dataset de treinamento sintético realista

python
def generate_training_data(self, n_samples=1000):
    """Gera dados sintéticos baseados em lógica real de entregas."""
    X = []
    y = []
    
    for _ in range(n_samples):
        # Features: [hora_dia, dia_semana, distancia_km, peso_kg, eh_fragil, trafego]
        hora = random.randint(0, 23)
        dia_semana = random.randint(0, 6)
        distancia = random.uniform(0.5, 25.0)
        peso = random.uniform(1, 30)
        fragil = random.choice([0, 1])
        trafego = random.uniform(0, 1)  # 0=livre, 1=congestionado
        
        # Tempo calculado com lógica realista
        tempo_base = distancia * 2.5  # ~2.5 min/km em cidade
        
        # Ajustes realistas
        if 7 <= hora <= 9 or 17 <= hora <= 19:  # Horário de pico
            tempo_base *= 1.5
        if dia_semana >= 5:  # Final de semana
            tempo_base *= 0.8
        if fragil:  # Carga frágil = mais cuidado
            tempo_base *= 1.2
        
        tempo_base += trafego * 15  # Tráfego adiciona até 15min
        tempo_base += random.gauss(0, 2)  # Ruído realista
        
        X.append([hora, dia_semana, distancia, peso, fragil, trafego])
        y.append(max(5, tempo_base))  # Mínimo 5 min
    
    return np.array(X), np.array(y)
 Implementar arquitetura da rede neural

python
def build_model(self):
    """Constrói e compila a RNA."""
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(32, activation='relu', input_shape=(6,)),
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
 Treinar o modelo no construtor da classe

python
def __init__(self):
    X, y = self.generate_training_data(1000)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)
    
    # Normalização
    self.scaler_X = StandardScaler()
    self.scaler_y = StandardScaler()
    
    X_train = self.scaler_X.fit_transform(X_train)
    X_val = self.scaler_X.transform(X_val)
    y_train = self.scaler_y.fit_transform(y_train.reshape(-1, 1)).ravel()
    y_val = self.scaler_y.transform(y_val.reshape(-1, 1)).ravel()
    
    self.model = self.build_model()
    
    # Treinamento silencioso
    self.model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=50,
        batch_size=32,
        verbose=0
    )
 Atualizar método predict() para usar RNA treinada

python
def predict(self, order, distance_km):
    """Predição real usando a RNA treinada."""
    hora = datetime.now().hour
    dia = datetime.now().weekday()
    peso = order.weight
    fragil = 1 if order.is_fragile else 0
    trafego = random.uniform(0.3, 0.8)  # Simula API de tráfego
    
    features = np.array([[hora, dia, distance_km/1000, peso, fragil, trafego]])
    features_scaled = self.scaler_X.transform(features)
    
    pred_scaled = self.model.predict(features_scaled, verbose=0)[0][0]
    pred_time = self.scaler_y.inverse_transform([[pred_scaled]])[0][0]
    
    order.predicted_time = max(5, pred_time)
    return order.predicted_time
1.2 Integrar DFS e BFS ao Sistema Real
Arquivo: src/ai/search.py (já existe, mas não é usado)

Tarefa: Criar casos de uso REAIS para essas técnicas

 Adicionar método de exploração de rotas alternativas (DFS)

python
def find_all_routes(self, start: int, goal: int, max_routes: int = 5) -> List[List[int]]:
    """
    DFS modificado para encontrar múltiplas rotas.
    Uso: Quando A* encontra obstáculo, explorar alternativas.
    """
    all_paths = []
    
    def dfs_recursive(current, goal, path, visited):
        if len(all_paths) >= max_routes:
            return
        
        if current == goal:
            all_paths.append(path[:])
            return
        
        for neighbor in self.graph.neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                dfs_recursive(neighbor, goal, path, visited)
                path.pop()
                visited.remove(neighbor)
    
    dfs_recursive(start, goal, [start], {start})
    
    # Retornar rotas ordenadas por custo total
    routes_with_cost = [(route, self.get_path_cost(route)) for route in all_paths]
    routes_with_cost.sort(key=lambda x: x[1])
    
    return [route for route, _ in routes_with_cost]
 Adicionar método de busca de nó mais próximo (BFS)

python
def find_nearest_from_set(self, start: int, target_nodes: Set[int]) -> tuple[int, List[int]]:
    """
    BFS para encontrar o nó mais próximo de um conjunto.
    Uso: Encontrar farmácia/depósito mais próximo para reabastecimento.
    """
    if start in target_nodes:
        return start, [start]
    
    queue = deque([(start, [start])])
    visited = {start}
    
    while queue:
        current, path = queue.popleft()
        
        for neighbor in self.graph.neighbors(current):
            if neighbor not in visited:
                new_path = path + [neighbor]
                
                if neighbor in target_nodes:
                    return neighbor, new_path
                
                visited.add(neighbor)
                queue.append((neighbor, new_path))
    
    return None, []
 Criar wrapper para facilitar uso no main.py

python
class SearchEngine:
    """Fachada que integra DFS, BFS e A* com casos de uso claros."""
    
    def __init__(self, graph):
        self.basic_search = BasicSearch(graph)
        self.astar = AStarNavigator(graph)
    
    def route_with_backup(self, start, goal, is_fragile=False):
        """
        1. Tenta A* (ótimo)
        2. Se falhar, usa DFS para encontrar alternativas
        3. Se nenhuma rota, retorna vazio
        """
        try:
            path = self.astar.get_path(start, goal, is_fragile)
            if path:
                return path, "astar"
        except:
            pass
        
        # Fallback: DFS para explorar alternativas
        routes = self.basic_search.find_all_routes(start, goal, max_routes=3)
        if routes:
            return routes[0], "dfs_backup"
        
        return [], "no_path"
    
    def find_nearest_depot(self, current_pos, depot_nodes):
        """Usa BFS para encontrar depósito mais próximo (emergências)."""
        nearest, path = self.basic_search.find_nearest_from_set(current_pos, set(depot_nodes))
        return nearest, path, "bfs"