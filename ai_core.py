import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from sklearn.neural_network import MLPClassifier
import heapq
import random
import math

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

# --- TÉCNICA 1: LÓGICA FUZZY (Define Prioridade) ---
class FuzzyPriority:
    def __init__(self):
        # Antecedentes
        wait = ctrl.Antecedent(np.arange(0, 121, 1), 'wait')
        dist = ctrl.Antecedent(np.arange(0, 101, 1), 'dist') # Distância relativa ao depósito
        priority = ctrl.Consequent(np.arange(0, 11, 1), 'priority')

        # Pertinência
        wait.automf(3, names=['curto', 'medio', 'longo'])
        dist.automf(3, names=['perto', 'media', 'longe'])
        priority.automf(3, names=['baixa', 'media', 'alta'])

        # Regras: Cliente esperando muito tempo ou perto tem prioridade maior
        rule1 = ctrl.Rule(wait['longo'] | dist['perto'], priority['alta'])
        rule2 = ctrl.Rule(wait['medio'] & dist['media'], priority['media'])
        rule3 = ctrl.Rule(wait['curto'] & dist['longe'], priority['baixa'])

        self.sim = ctrl.ControlSystemSimulation(ctrl.ControlSystem([rule1, rule2, rule3]))

    def calculate(self, order, depot_pos):
        dist_to_depot = np.linalg.norm(np.array([order.x, order.y]) - np.array(depot_pos))
        # Clamp valores para não estourar o range fuzzy
        self.sim.input['wait'] = min(order.wait_time, 120)
        self.sim.input['dist'] = min(dist_to_depot, 100)
        self.sim.compute()
        order.priority = self.sim.output['priority']
        return order

# --- TÉCNICA 2: REDE NEURAL (Previsão de Atraso) ---
class NeuralPredictor:
    def __init__(self):
        # Treinamento Simulado (Mock Training)
        # Features: [Peso, Chuva, Prioridade(Fuzzy)]
        # A rede aprende que Peso alto + Chuva = Atraso
        X_train = [
            [2, 0, 8], [20, 1, 2], [5, 0, 5], [30, 1, 9], 
            [1, 1, 4], [15, 0, 6], [10, 1, 5], [25, 1, 3]
        ]
        y_train = [0, 1, 0, 1, 0, 0, 1, 1] # 0 = No Prazo, 1 = Atraso

        self.clf = MLPClassifier(hidden_layer_sizes=(8, 4), max_iter=1000, random_state=42)
        self.clf.fit(X_train, y_train)

    def predict(self, order):
        # Usa a prioridade calculada pelo Fuzzy como input!
        features = [[order.weight, order.rain, order.priority]]
        pred = self.clf.predict(features)[0]
        prob = self.clf.predict_proba(features)[0][pred]
        
        order.delay_risk = "ALTO" if pred == 1 else "BAIXO"
        order.risk_prob = prob
        return order

# --- TÉCNICA 3: ALGORITMO GENÉTICO (Sequenciamento da Rota) ---
class GeneticTSP:
    def __init__(self, orders, depot_pos):
        self.orders = orders
        self.depot = depot_pos
        self.pop_size = 50
        self.generations = 50  # Reduzido para ficar rápido na demo

    def fitness(self, route_indices):
        # Calcula distância total: Deposito -> P1 -> P2 ... -> Deposito
        points = [self.depot] + [ (self.orders[i].x, self.orders[i].y) for i in route_indices ] + [self.depot]
        total_dist = 0
        for i in range(len(points)-1):
            total_dist += np.linalg.norm(np.array(points[i]) - np.array(points[i+1]))
        return total_dist

    def solve(self):
        indices = list(range(len(self.orders)))
        population = [random.sample(indices, len(indices)) for _ in range(self.pop_size)]
        
        best_route = None
        min_dist = float('inf')

        for _ in range(self.generations):
            population.sort(key=self.fitness)
            if self.fitness(population[0]) < min_dist:
                min_dist = self.fitness(population[0])
                best_route = population[0]

            # Seleção e Cruzamento (Simplificado)
            new_pop = population[:10] # Elitismo
            while len(new_pop) < self.pop_size:
                p1, p2 = random.sample(population[:25], 2)
                cut = len(p1)//2
                child = p1[:cut] + [x for x in p2 if x not in p1[:cut]]
                # Mutação
                if random.random() < 0.2:
                    a, b = random.sample(range(len(child)), 2)
                    child[a], child[b] = child[b], child[a]
                new_pop.append(child)
            population = new_pop
            
        return best_route

# --- TÉCNICA 4: A* (Navegação Física no Mapa) ---
class AStarNavigator:
    def __init__(self, grid_size=20):
        self.grid_size = grid_size
        self.grid = np.zeros((grid_size, grid_size))
        # Adiciona obstáculos (Prédios/Bloqueios)
        for _ in range(40):
            x, y = random.randint(0, grid_size-1), random.randint(0, grid_size-1)
            self.grid[x][y] = 1 

    def heuristic(self, a, b):
        return abs(b[0] - a[0]) + abs(b[1] - a[1])

    def get_path(self, start, end):
        # Garante que start/end não são obstáculos
        self.grid[start] = 0
        self.grid[end] = 0
        
        neighbors = [(0,1),(0,-1),(1,0),(-1,0)]
        open_list = []
        heapq.heappush(open_list, (0, start))
        came_from = {}
        g_score = {start: 0}
        
        while open_list:
            current = heapq.heappop(open_list)[1]

            if current == end:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]

            for dx, dy in neighbors:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < self.grid_size and 0 <= neighbor[1] < self.grid_size:
                    if self.grid[neighbor] == 1: continue
                    
                    temp_g = g_score[current] + 1
                    if temp_g < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        g_score[neighbor] = temp_g
                        f_score = temp_g + self.heuristic(neighbor, end)
                        heapq.heappush(open_list, (f_score, neighbor))
        return [start, end] # Retorna linha reta se falhar (fallback)