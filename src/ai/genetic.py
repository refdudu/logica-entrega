from typing import List, Callable, Optional
import random

class GeneticTSP:
    """Genetic Algorithm for solving Capacitated Vehicle Routing Problem (CVRP).
    
    Integrates with Fuzzy Logic system to prioritize high-priority orders,
    reducing total delivery time for urgent packages.
    """
    
    def __init__(self, orders: List, depot_node: int, astar_engine, 
                 truck_capacity: float = 30.0, population_size: int = 50, 
                 generations: int = 50, progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """Initialize the Genetic Algorithm solver.
        
        Args:
            orders: List of Order objects to deliver
            depot_node: ID of the depot node
            astar_engine: AStarNavigator instance for pathfinding
            truck_capacity: Maximum truck capacity in kg
            population_size: Number of individuals in each generation
            generations: Number of generations to evolve
            progress_callback: Optional callback function(current_gen, total_gens)
        """
        self.orders = orders
        self.depot_node = depot_node
        self.astar_engine = astar_engine
        self.truck_capacity = truck_capacity
        self.population_size = population_size
        self.generations = generations
        self.population = []
        self.progress_callback = progress_callback

    def _calculate_fitness(self, individual: List[int]) -> float:
        """Calculate fitness score with accumulated fragility tracking.
        
        The fitness function optimizes for:
        1. Minimizing total travel cost
        2. Delivering fragile items later (fragility 'infects' the truck)
        3. Intelligent capacity management
        
        Args:
            individual: Sequence of order indices representing a route
            
        Returns:
            Fitness score (higher is better)
        """
        total_cost = 0.0
        current_node = self.depot_node
        current_load = 0.0
        
        # Track if we HAVE fragile cargo in the truck right now
        # Once we pick up a fragile item, all subsequent routes must be fragile-safe
        has_fragile_cargo = False
        
        for order_index in individual:
            order = self.orders[order_index]
            
            # 1. Capacity check (existing logic)
            if current_load + order.weight > self.truck_capacity:
                # Return to depot with current fragility state
                cost_to_depot = self.astar_engine.get_path_cost(
                    current_node, self.depot_node, is_fragile=has_fragile_cargo
                )
                total_cost += cost_to_depot
                current_node = self.depot_node
                current_load = 0.0
                has_fragile_cargo = False  # Unloaded everything
            
            # 2. Travel cost to order location
            # KEY INSIGHT: Trip is fragile if the NEW order is fragile OR we already have fragile cargo
            trip_is_fragile = order.is_fragile or has_fragile_cargo
            
            travel_cost = self.astar_engine.get_path_cost(
                current_node, order.node_id, is_fragile=trip_is_fragile
            )
            
            # High cost paths (from A* penalties) will make the GA avoid this route
            total_cost += travel_cost
            
            # 3. Update truck state
            current_node = order.node_id
            current_load += order.weight
            
            # If we picked up a fragile item, truck is now "infected" with fragility
            # until we return to depot
            if order.is_fragile:
                has_fragile_cargo = True
        
        # Return to depot at end
        total_cost += self.astar_engine.get_path_cost(
            current_node, self.depot_node, is_fragile=has_fragile_cargo
        )
        
        # Convert to fitness (minimize total_cost)
        return 1.0 / (total_cost + 1e-6)

    def solve(self) -> List[int]:
        """Execute the genetic algorithm to find optimal route.
        
        Returns:
            List of order indices representing the optimized delivery sequence
        """
        if not self.orders:
            return []
            
        indices = list(range(len(self.orders)))
        self.population = [random.sample(indices, len(indices)) for _ in range(self.population_size)]
        
        best_route = None
        max_fitness = -1.0

        for generation in range(self.generations):
            fitness_scores = [self._calculate_fitness(ind) for ind in self.population]
            
            # Track best
            for i, score in enumerate(fitness_scores):
                if score > max_fitness:
                    max_fitness = score
                    best_route = self.population[i]
            
            # Report progress if callback provided
            if self.progress_callback:
                self.progress_callback(generation + 1, self.generations)
            
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

    def _tournament(self, pop: List[List[int]], scores: List[float], k: int = 3) -> List[int]:
        """Tournament selection: pick best from k random individuals."""
        selection_ix = random.sample(range(len(pop)), k)
        best_ix = selection_ix[0]
        for ix in selection_ix[1:]:
            if scores[ix] > scores[best_ix]:
                best_ix = ix
        return pop[best_ix]

    def _crossover(self, p1: List[int], p2: List[int]) -> List[int]:
        """Order 1 Crossover operator for TSP-like problems."""
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

    def _mutate(self, indiv: List[int]) -> None:
        """Swap mutation: randomly swap two positions with 10% probability."""
        if random.random() < 0.1:
            i, j = random.sample(range(len(indiv)), 2)
            indiv[i], indiv[j] = indiv[j], indiv[i]
