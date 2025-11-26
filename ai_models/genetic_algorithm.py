import numpy as np
import random

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
