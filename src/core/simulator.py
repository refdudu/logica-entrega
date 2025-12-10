import networkx as nx
import random
import time
from copy import deepcopy

from src.core.map_manager import MapManager
from src.models.order import Order
from src.models.truck import Truck
from src.ai.fuzzy import FuzzyPriority
from src.ai.neural import NeuralPredictor
from src.ai.genetic import GeneticTSP
from src.ai.astar import AStarNavigator

class Simulator:
    def __init__(self, num_orders=15, mode="smart"):
        self.num_orders = num_orders
        self.mode = mode
        
        # 1. Init Map
        self.map_manager = MapManager()
        self.graph = self.map_manager.load_graph()
        self.astar = AStarNavigator(self.graph)
        
        # 2. Init Models
        self.orders = []
        self.depot_node = list(self.graph.nodes())[0] # Simplification
        self.truck = Truck(capacity=30.0)
        
        # 3. Init AI
        self.fuzzy = FuzzyPriority()
        self.neural = NeuralPredictor()
        
        # Generate random orders
        self._generate_orders()

    def _generate_orders(self):
        print(f"Generating {self.num_orders} orders...")
        for i in range(self.num_orders):
            node_id = self.map_manager.get_random_node()
            # Random attributes
            deadline = random.randint(10, 120)
            weight = random.uniform(1.0, 15.0)
            is_fragile = random.choice([True, False])
            priority_class = random.choice([0, 1])
            
            order = Order(i+1, node_id, deadline, weight, is_fragile, priority_class)
            self.orders.append(order)

    def run(self):
        if self.mode == "smart":
            return self._run_smart()
        else:
            return self._run_legacy()

    def _calculate_real_cost(self, path):
        """Calculates the actual time/cost taken to traverse a path, considering current conditions."""
        total_time = 0.0
        damaged_cargo = False
        
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            data = self.graph.get_edge_data(u, v)[0]
            
            # Real traversal physics
            
            # 1. Road Block?
            # If path was planned on a road block (Legacy might do this), effectively infinite delay or reroute.
            # Simplified: add huge penalty.
            if data.get('road_block'):
                total_time += 3600 # 1 hour stuck/rerouting
            
            # 2. Pavement & Fragility
            # If cargo is fragile and pavement is bad -> Damage
            # We need to know if we are carrying fragile cargo *at this moment*.
            # Simplified: If any order in the truck is fragile? 
            # Or just count stats.
            # Let's assume the truck currently has the relevant cargo.
            # This is hard to track without full state. 
            # We will approximate: we track "Fragile Orders Broken" count.
            
            pavement_quality = data.get('pavement_quality', 'good')
            if pavement_quality == 'bad':
                total_time += data.get('travel_time', 0) * 0.4 # Slower
                # If we are carrying fragile, mark damage potential
                # We handle this in the main loop traversal
            
            traffic = data.get('traffic_level', 0)
            effective_time = data.get('travel_time', 1.0) * (1.0 + traffic)
            total_time += effective_time
            
        return total_time

    def _run_legacy(self):
        print("Running Legacy Simulation...")
        start_time = time.time()
        
        # 1. Sort by Deadline (Simple)
        sorted_orders = sorted(self.orders, key=lambda x: x.deadline)
        
        total_dist = 0.0
        total_travel_time = 0.0
        broken_fragile_count = 0
        
        current_node = self.depot_node
        self.truck.reset_load()
        
        # Route: simply go to next in list
        # If full, go to depot, then next.
        
        # Path trace
        trace = [current_node]
        
        for order in sorted_orders:
            # Check capacity
            if not self.truck.can_load(order.weight):
                # Go to depot
                path_to_depot = nx.shortest_path(self.graph, current_node, self.depot_node, weight='length')
                # Calculate real cost
                total_travel_time += self._traverse_path(path_to_depot, has_fragile=False) # Empty return?
                trace.extend(path_to_depot[1:])
                current_node = self.depot_node
                self.truck.reset_load()
            
            # Go to order
            try:
                # Dijkstra using 'length' (ignores traffic/pavement)
                path = nx.shortest_path(self.graph, current_node, order.node_id, weight='length')
                
                # Check for damage during traversal
                trip_time, damaged = self._traverse_path_detailed(path, is_fragile=order.is_fragile)
                total_travel_time += trip_time
                if damaged and order.is_fragile:
                    broken_fragile_count += 1
                
                trace.extend(path[1:])
                total_dist += nx.path_weight(self.graph, path, weight='length')
                
                self.truck.load(order.weight)
                current_node = order.node_id
                
            except nx.NetworkXNoPath:
                print(f"Unreachable order {order.id}")
        
        # Return to depot
        path = nx.shortest_path(self.graph, current_node, self.depot_node, weight='length')
        t, _ = self._traverse_path_detailed(path, False)
        total_travel_time += t
        trace.extend(path[1:])
        
        return {
            "mode": "Legacy",
            "time_total": total_travel_time / 60.0, # minutes
            "distance_km": total_dist / 1000.0,
            "broken_fragile": broken_fragile_count,
            "orders_delivered": len(sorted_orders) # Assumption
        }

    def _run_smart(self):
        print("Running Smart Simulation...")
        
        # 1. Fuzzy & Neural
        current_node = self.depot_node
        for order in self.orders:
            # Estimate distance for fuzzy (using air dist or prev known)
            # Use A* cost from depot as approximation
            dist = self.astar.get_path_cost(self.depot_node, order.node_id, is_fragile=False)
            self.fuzzy.calculate(order, dist)
            self.neural.predict(order)
        
        # 2. Genetic Optimization
        print("Optimizing route (Genetic Algorithm)...")
        ga = GeneticTSP(self.orders, self.depot_node, self.astar, truck_capacity=30.0)
        best_indices = ga.solve()
        
        # 3. Execution using A* paths
        print("Executing Smart Route...")
        optimized_orders = [self.orders[i] for i in best_indices]
        
        total_dist = 0.0
        total_travel_time = 0.0
        broken_fragile_count = 0
        
        self.truck.reset_load()
        current_node = self.depot_node
        
        for order in optimized_orders:
            # Capacity check (Genetic should have optimized, but we simulate execution)
            if not self.truck.can_load(order.weight):
                 # Return to depot
                 path = self.astar.get_path(current_node, self.depot_node, is_fragile=False)
                 t, d = self._traverse_path_detailed(path, False)
                 total_travel_time += t
                 current_node = self.depot_node
                 self.truck.reset_load()
            
            # Go to order (Smart Path)
            path = self.astar.get_path(current_node, order.node_id, is_fragile=order.is_fragile)
            if not path:
                # Retry without fragile constraints? No, smart skips or fails.
                print(f"Smart: Could not reach {order.id}")
                continue
                
            t, damaged = self._traverse_path_detailed(path, is_fragile=order.is_fragile)
            total_travel_time += t
            if damaged and order.is_fragile:
                broken_fragile_count += 1
            
            # Approximate distance (just for stats)
            # path_weight using length
            for i in range(len(path)-1):
                 d = self.graph.get_edge_data(path[i], path[i+1])[0]
                 total_dist += d.get('length', 0)

            self.truck.load(order.weight)
            current_node = order.node_id

        # Return to depot
        path = self.astar.get_path(current_node, self.depot_node, is_fragile=False)
        t, _ = self._traverse_path_detailed(path, False)
        total_travel_time += t
        
        return {
            "mode": "Smart",
            "time_total": total_travel_time / 60.0,
            "distance_km": total_dist / 1000.0,
            "broken_fragile": broken_fragile_count,
            "orders_delivered": len(optimized_orders) # Assumption
        }

    def _traverse_path_detailed(self, path, is_fragile):
        """Simulates driving the path and returns (time_taken, is_damaged)"""
        time_taken = 0.0
        damaged = False
        
        if not path: return 0.0, False

        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            # Handle MultiDiGraph
            all_edges = self.graph.get_edge_data(u, v)
            # With A* or shortest_path, we assume the best edge was picked if multiples exist?
            # Or we just take key=0
            data = all_edges[0]
            
            length = data.get('length', 100)
            traffic = data.get('traffic_level', 0.0)
            pavement = data.get('pavement_quality', 'good')
            road_block = data.get('road_block', False)
            
            # 1. Physics
            if road_block:
                time_taken += 1800 # 30 mins penalty
            
            # Speed logic re-use?
            # Base speed
            speed_limit = data.get('maxspeed', 40.0)
            if isinstance(speed_limit, list): speed_limit = float(speed_limit[0])
            else: speed_limit = float(speed_limit)

            effective_speed = speed_limit * (1.0 - traffic * 0.8)
            if pavement == 'bad':
                effective_speed *= 0.6 # Bad pavement slows down
                if is_fragile:
                    damaged = True # Fragile on bad pavement breaks
            
            if effective_speed < 1: effective_speed = 1.0
            
            # Time = Distance / Speed
            # m / (km/h / 3.6) -> s
            segment_time = length / (effective_speed / 3.6)
            time_taken += segment_time
        
        return time_taken, damaged

    def _traverse_path(self, path, has_fragile):
        # Wrapper for simple cost
        t, _ = self._traverse_path_detailed(path, has_fragile)
        return t
