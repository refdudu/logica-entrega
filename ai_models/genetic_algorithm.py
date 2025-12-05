import random

# --- TÉCNICA 3: ALGORITMO GENÉTICO (Sequenciamento da Rota) ---
class GeneticTSP:
    def __init__(self, orders, depot_node, astar_engine, population_size=50, generations=100):
        self.orders = orders
        self.depot_node = depot_node
        self.astar_engine = astar_engine
        self.population_size = population_size
        self.generations = generations
        self.population = []

    def _calculate_fitness(self, individual):
        total_distance = 0
        current_node = self.depot_node
        
        for order_index in individual:
            next_node = self.orders[order_index].node_id
            # Use A* engine to get cost (time/distance)
            dist = self.astar_engine.get_path_cost(current_node, next_node)
            total_distance += dist
            current_node = next_node
            
        # Return to depot
        total_distance += self.astar_engine.get_path_cost(current_node, self.depot_node)
        
        return 1 / (total_distance + 1e-6) # Inverse of distance

    def solve(self):
        if not self.orders:
            return []
            
        indices = list(range(len(self.orders)))
        self.population = [random.sample(indices, len(indices)) for _ in range(self.population_size)]
        
        best_route = None
        max_fitness = -1

        for _ in range(self.generations):
            # Calculate fitness for all
            fitness_scores = [self._calculate_fitness(ind) for ind in self.population]
            
            # Find best in this generation
            gen_best_idx = fitness_scores.index(max(fitness_scores))
            if fitness_scores[gen_best_idx] > max_fitness:
                max_fitness = fitness_scores[gen_best_idx]
                best_route = self.population[gen_best_idx]
            
            # Elitism: Keep top 10%
            sorted_pop = [x for _, x in sorted(zip(fitness_scores, self.population), key=lambda pair: pair[0], reverse=True)]
            elite_count = int(self.population_size * 0.1)
            new_pop = sorted_pop[:elite_count]
            
            # Fill rest
            while len(new_pop) < self.population_size:
                # Tournament Selection
                p1 = self._tournament_selection(self.population, fitness_scores)
                p2 = self._tournament_selection(self.population, fitness_scores)
                
                # Crossover (Order Crossover)
                cut = len(p1) // 2
                child = p1[:cut] + [x for x in p2 if x not in p1[:cut]]
                
                # Mutation
                if random.random() < 0.2:
                    a, b = random.sample(range(len(child)), 2)
                    child[a], child[b] = child[b], child[a]
                    
                new_pop.append(child)
            
            self.population = new_pop
            
        return best_route

    def _tournament_selection(self, population, fitness_scores, k=3):
        selection_ix = random.sample(range(len(population)), k)
        best_ix = selection_ix[0]
        for ix in selection_ix[1:]:
            if fitness_scores[ix] > fitness_scores[best_ix]:
                best_ix = ix
        return population[best_ix]
