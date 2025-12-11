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
        """Calculate fitness score integrating travel cost, fuzzy priority, and fragility.
        
        The fitness function optimizes for:
        1. Routes that deliver high-priority orders early
        2. Routes that deliver fragile items later (reduces detour penalty)
        3. Minimizing total travel cost
        
        Args:
            individual: Sequence of order indices representing a route
            
        Returns:
            Fitness score (higher is better)
        """
        total_score = 0.0
        current_node = self.depot_node
        current_load = 0.0
        current_time = 0.0  # Accumulated time for priority penalty calculation
        fragile_position_penalty = 0.0  # Penalty for fragile items delivered early
        
        total_orders = len(individual)
        
        # Iterate through the sequence of orders
        for position, order_index in enumerate(individual):
            order = self.orders[order_index]
            
            # Check capacity constraint
            if current_load + order.weight > self.truck_capacity:
                # Return to depot to unload
                cost_to_depot = self.astar_engine.get_path_cost(
                    current_node, self.depot_node, is_fragile=False
                )
                total_score += cost_to_depot
                current_time += cost_to_depot
                
                current_node = self.depot_node
                current_load = 0.0
            
            # Travel to order location
            is_fragile_trip = order.is_fragile
            travel_cost = self.astar_engine.get_path_cost(
                current_node, order.node_id, is_fragile=is_fragile_trip
            )
            
            # Update cumulative metrics
            total_score += travel_cost
            current_time += travel_cost
            
            # ** FUZZY INTEGRATION: Priority-based penalty **
            # High-priority orders (fuzzy_priority near 10) get heavy penalties if delivered late
            # This encourages the GA to place urgent orders early in the route
            priority_weight = getattr(order, 'fuzzy_priority', 5.0)
            time_penalty = current_time * (priority_weight / 5.0)
            total_score += time_penalty
            
            # ** FRAGILITY OPTIMIZATION: Position-based penalty **
            # Fragile items delivered early in the route add penalty
            # This encourages delivering fragile items later, reducing total detour distance
            if order.is_fragile:
                # Higher penalty for fragile items in early positions
                # Position 0 = highest penalty, last position = no penalty
                position_ratio = 1.0 - (position / max(total_orders - 1, 1))
                fragile_position_penalty += position_ratio * 50.0  # Base penalty of 50
            
            # Update state
            current_node = order.node_id
            current_load += order.weight
            
        # Return to depot at end
        final_cost = self.astar_engine.get_path_cost(
            current_node, self.depot_node, is_fragile=False
        )
        total_score += final_cost
        
        # Add fragile position penalty to total score
        total_score += fragile_position_penalty
        
        # Convert to fitness (minimize total_score)
        return 1.0 / (total_score + 1e-6)

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
