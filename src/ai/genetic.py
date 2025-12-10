import random

class GeneticTSP:
    def __init__(self, orders, depot_node, astar_engine, truck_capacity=30.0, population_size=50, generations=50):
        self.orders = orders
        self.depot_node = depot_node
        self.astar_engine = astar_engine
        self.truck_capacity = truck_capacity
        self.population_size = population_size
        self.generations = generations
        self.population = []

    def _calculate_fitness(self, individual):
        """
        Calculates fitness based on CVRP (Capacitated Vehicle Routing Problem).
        If capacity is exceeded, truck must return to depot.
        """
        total_cost = 0.0
        current_node = self.depot_node
        current_load = 0.0
        
        # Iterate through the sequence of orders
        for order_index in individual:
            order = self.orders[order_index]
            
            # Check capacity
            if current_load + order.weight > self.truck_capacity:
                # Must return to depot first
                cost_to_depot = self.astar_engine.get_path_cost(current_node, self.depot_node, is_fragile=False) # Empty truck is not fragile?
                total_cost += cost_to_depot
                
                current_node = self.depot_node
                current_load = 0.0
            
            # Go to order location
            # Note: Truck fragility status depends on what it is carrying. 
            # If it carries fragile item, it is fragile.
            # Here implementation is simplified: we assume if we are carrying fragile, it's fragile.
            # But we are just adding one item.
            
            is_fragile_trip = order.is_fragile 
            # Wait, if we already have fragile items?
            # Simplified: considers current order fragility for this leg.
            
            cost_to_order = self.astar_engine.get_path_cost(current_node, order.node_id, is_fragile=is_fragile_trip)
            total_cost += cost_to_order
            
            current_node = order.node_id
            current_load += order.weight
            
        # Return to depot at end
        total_cost += self.astar_engine.get_path_cost(current_node, self.depot_node, is_fragile=False)
        
        return 1.0 / (total_cost + 1e-6)

    def solve(self):
        if not self.orders:
            return []
            
        indices = list(range(len(self.orders)))
        self.population = [random.sample(indices, len(indices)) for _ in range(self.population_size)]
        
        best_route = None
        max_fitness = -1.0

        for _ in range(self.generations):
            fitness_scores = [self._calculate_fitness(ind) for ind in self.population]
            
            # Track best
            for i, score in enumerate(fitness_scores):
                if score > max_fitness:
                    max_fitness = score
                    best_route = self.population[i]
            
            # Selection & Next Gen ...
            # Simplified standard GA
            next_pop = []
            
            # Elitism (Top 2)
            sorted_pop = [x for _, x in sorted(zip(fitness_scores, self.population), key=lambda pair: pair[0], reverse=True)]
            next_pop.extend(sorted_pop[:2])
            
            while len(next_pop) < self.population_size:
                p1 = self._tournament(self.population, fitness_scores)
                p2 = self._tournament(self.population, fitness_scores)
                child = self._crossover(p1, p2)
                self._mutate(child)
                next_pop.append(child)
                
            self.population = next_pop
            
        return best_route

    def _tournament(self, pop, scores, k=3):
        selection_ix = random.sample(range(len(pop)), k)
        best_ix = selection_ix[0]
        for ix in selection_ix[1:]:
            if scores[ix] > scores[best_ix]:
                best_ix = ix
        return pop[best_ix]

    def _crossover(self, p1, p2):
        # Order 1 Crossover
        start, end = sorted(random.sample(range(len(p1)), 2))
        child = [None] * len(p1)
        child[start:end] = p1[start:end]
        
        ptr = 0
        for gene in p2:
            if gene not in child[start:end]:
                while child[ptr] is not None:
                    ptr += 1
                child[ptr] = gene
        return child

    def _mutate(self, indiv):
        if random.random() < 0.1:
            i, j = random.sample(range(len(indiv)), 2)
            indiv[i], indiv[j] = indiv[j], indiv[i]
