"""
Simulator module with dependency injection for consistent testing.

Implements real-world delivery simulation with cargo integrity tracking,
road obstacles, and time-based penalties.
"""

import networkx as nx
from typing import List, Dict, Tuple

from src.models.order import Order
from src.models.truck import Truck
from src.ai.fuzzy import FuzzyPriority
from src.ai.neural import NeuralPredictor
from src.ai.genetic import GeneticTSP
from src.ai.astar import AStarNavigator
from src.ai.search import BasicSearch


class Simulator:
    """Delivery route simulator with AI integration.
    
    Simulates real-world delivery scenarios including:
    - Cargo integrity damage on bad roads
    - Time penalties from road blocks
    - Capacity constraints requiring depot returns
    - Fragile cargo requiring careful routing
    """
    
    def __init__(self, graph: nx.MultiDiGraph, orders: List[Order], 
                 depot_node: int, mode: str = "smart") -> None:
        """Initialize simulator with dependency injection.
        
        Args:
            graph: Pre-loaded and enriched NetworkX graph
            orders: List of Order objects to deliver
            depot_node: Starting depot node ID
            mode: "smart" (AI-optimized), "legacy" (deadline sorting), "dfs", or "bfs"
        """
        self.graph = graph
        self.orders = orders
        self.depot_node = depot_node
        self.mode = mode
        
        # Initialize subsystems
        self.truck = Truck(capacity=30.0)
        self.astar = AStarNavigator(self.graph)
        self.fuzzy = FuzzyPriority()
        self.neural = NeuralPredictor()
        self.basic_search = BasicSearch(self.graph)
    
    def run(self) -> Dict[str, float]:
        """Execute simulation and return results.
        
        Returns:
            Dictionary with: mode, time_total, distance_km, avg_integrity, orders_delivered
        """
        # Reset all orders to 100% integrity before simulation
        for order in self.orders:
            order.current_integrity = 100.0
            order.delivered = False
        
        if self.mode == "smart":
            return self._run_smart()
        elif self.mode == "dfs":
            return self._run_dfs()
        elif self.mode == "bfs":
            return self._run_bfs()
        else:
            return self._run_legacy()
    
    def _run_legacy(self) -> Dict[str, float]:
        """Execute legacy simulation using simple deadline sorting.
        
        Returns:
            Simulation results dictionary
        """
        print("Running Legacy Simulation (Simple Deadline Sorting)...")
        
        # Sort by deadline only (no AI)
        sorted_orders = sorted(self.orders, key=lambda x: x.deadline)
        
        return self._execute_delivery_route(sorted_orders, use_ai_pathing=False)
    
    def _run_smart(self) -> Dict[str, float]:
        """Execute smart simulation using full AI pipeline.
        
        Returns:
            Simulation results dictionary
        """
        print("Running Smart Simulation (AI Pipeline)...")
        
        # 1. Analyze orders with Fuzzy Logic and Neural Network
        for order in self.orders:
            # Calcula caminho e distância
            path = self.astar.get_path(self.depot_node, order.node_id, is_fragile=order.is_fragile)
            
            dist_meters = 0
            bad_meters = 0
            
            if path:
                # Analisa o caminho para calcular bad_road_ratio
                for i in range(len(path) - 1):
                    u, v = path[i], path[i+1]
                    edge_data = self.graph.get_edge_data(u, v)
                    
                    # Handle MultiDiGraph (get first edge)
                    if edge_data:
                        data = edge_data[0] if isinstance(edge_data, dict) and 0 in edge_data else edge_data
                        length = data.get('length', 100)
                        dist_meters += length
                        
                        # Conta metros de estrada ruim
                        if data.get('pavement_quality') == 'bad' or data.get('road_block'):
                            bad_meters += length
            
            # 2. Calcula Ratio e verifica Inevitabilidade
            ratio = (bad_meters / dist_meters) if dist_meters > 0 else 0.0
            
            if bad_meters > 0:
                # ✅ Verifica se a IA foi "forçada" a passar por estrada ruim
                order.unavoidable_bad_road = self.astar.check_if_bad_road_is_unavoidable(
                    self.depot_node, order.node_id
                )
            else:
                order.unavoidable_bad_road = False
            
            # 3. Predição com nova feature (bad_road_ratio)
            dist = dist_meters if dist_meters > 0 else 5000
            self.neural.predict(order, dist, bad_road_ratio=ratio)
            self.fuzzy.calculate(order, dist)
        
        # 2. Optimize route with Genetic Algorithm
        print("Optimizing route (Genetic Algorithm)...")
        ga = GeneticTSP(
            self.orders, 
            self.depot_node, 
            self.astar, 
            truck_capacity=30.0,
            generations=30
        )
        best_indices = ga.solve()
        optimized_orders = [self.orders[i] for i in best_indices]
        
        return self._execute_delivery_route(optimized_orders, use_ai_pathing=True)
    
    def _run_dfs(self) -> Dict[str, float]:
        """Execute simulation using Depth-First Search pathfinding.
        
        Returns:
            Simulation results dictionary
        """
        print("Running DFS Simulation (Depth-First Search)...")
        
        # Sort by deadline (no AI optimization)
        sorted_orders = sorted(self.orders, key=lambda x: x.deadline)
        
        return self._execute_delivery_route(sorted_orders, use_ai_pathing=False, search_mode="dfs")
    
    def _run_bfs(self) -> Dict[str, float]:
        """Execute simulation using Breadth-First Search pathfinding.
        
        Returns:
            Simulation results dictionary
        """
        print("Running BFS Simulation (Breadth-First Search)...")
        
        # Sort by deadline (no AI optimization)
        sorted_orders = sorted(self.orders, key=lambda x: x.deadline)
        
        return self._execute_delivery_route(sorted_orders, use_ai_pathing=False, search_mode="bfs")
    
    def _execute_delivery_route(self, sequence_orders: List[Order], 
                                use_ai_pathing: bool,
                                search_mode: str = "dijkstra") -> Dict[str, float]:
        """Simulate physical execution of delivery route.
        
        Args:
            sequence_orders: Ordered list of deliveries to make
            use_ai_pathing: If True, use A* with constraints; if False, use basic search
            search_mode: "dijkstra" (default), "dfs", or "bfs"
            
        Returns:
            Dictionary with simulation metrics
        """
        total_time_minutes = 0.0
        total_dist_km = 0.0
        
        current_node = self.depot_node
        self.truck.unload_all()
        
        for order in sequence_orders:
            # 1. Check capacity - return to depot if needed
            if not self.truck.can_load(order.weight):
                has_fragile = len(self.truck.get_fragile_cargo()) > 0
                path = self._get_path(current_node, self.depot_node, use_ai_pathing, has_fragile, search_mode)
                
                t, d = self._traverse_path(path)
                total_time_minutes += t
                total_dist_km += d
                
                current_node = self.depot_node
                self.truck.unload_all()
            
            # 2. Travel to order pickup location
            has_fragile = len(self.truck.get_fragile_cargo()) > 0
            path = self._get_path(current_node, order.node_id, use_ai_pathing, has_fragile, search_mode)
            
            if not path:
                print(f"  Skipping unreachable order {order.id}")
                continue
            
            # 3. Traverse path and apply damage to cargo
            t, d = self._traverse_path(path)
            total_time_minutes += t
            total_dist_km += d
            
            # 4. Load order and mark as delivered
            self.truck.load_order(order)
            order.delivered = True
            current_node = order.node_id
        
        # Return to depot at end
        has_fragile = len(self.truck.get_fragile_cargo()) > 0
        path = self._get_path(current_node, self.depot_node, use_ai_pathing, has_fragile, search_mode)
        t, d = self._traverse_path(path)
        total_time_minutes += t
        total_dist_km += d
        
        # Calculate average integrity
        delivered_orders = [o for o in sequence_orders if o.delivered]
        avg_integrity = (sum(o.current_integrity for o in delivered_orders) / 
                        len(delivered_orders) if delivered_orders else 100.0)
        
        # Determine mode name
        if use_ai_pathing:
            mode_name = "Smart"
        elif search_mode == "dfs":
            mode_name = "DFS"
        elif search_mode == "bfs":
            mode_name = "BFS"
        else:
            mode_name = "Legacy"
        
        return {
            "mode": mode_name,
            "time_total": total_time_minutes,
            "distance_km": total_dist_km,
            "avg_integrity": avg_integrity,
            "orders_delivered": len(delivered_orders)
        }
    
    def _get_path(self, start: int, end: int, use_ai: bool, has_fragile: bool, 
                  search_mode: str = "dijkstra") -> List[int]:
        """Get path between two nodes based on routing mode.
        
        Args:
            start: Starting node ID
            end: Ending node ID
            use_ai: If True, use A* with constraints
            has_fragile: Whether truck currently carries fragile cargo
            search_mode: "dijkstra", "dfs", or "bfs"
            
        Returns:
            List of node IDs forming the path
        """
        if use_ai:
            return self.astar.get_path(start, end, is_fragile=has_fragile)
        elif search_mode == "dfs":
            return self.basic_search.dfs(start, end)
        elif search_mode == "bfs":
            return self.basic_search.bfs(start, end)
        else:
            try:
                # Legacy: simple shortest path ignoring constraints
                return nx.shortest_path(self.graph, start, end, weight='length')
            except nx.NetworkXNoPath:
                return []
    
    def _traverse_path(self, path: List[int]) -> Tuple[float, float]:
        """Traverse a path and apply real-world effects.
        
        Calculates travel time considering traffic and obstacles.
        Applies damage to fragile cargo on bad roads.
        
        Args:
            path: List of node IDs to traverse
            
        Returns:
            Tuple of (time_in_minutes, distance_in_km)
        """
        if not path:
            return 0.0, 0.0
        
        time_seconds = 0.0
        distance_meters = 0.0
        
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            
            # Get edge data (handle MultiDiGraph)
            edge_data = self.graph.get_edge_data(u, v)
            if not edge_data:
                continue
            data = edge_data[0]  # Take first edge if multiple exist
            
            length_m = data.get('length', 100)
            distance_meters += length_m
            
            # ** FEATURE 2: Road Block Penalty **
            if data.get('road_block', False):
                # Massive time penalty: 120 minutes stuck
                time_seconds += 120 * 60
                print(f"  ⚠️ Hit road block on edge {u}-{v} (+120min penalty)")
            
            # ** Calculate normal travel time **
            speed_kmh = float(data.get('maxspeed', 40))
            if isinstance(speed_kmh, list):
                speed_kmh = float(speed_kmh[0])
            
            # Traffic slowdown
            traffic_factor = 1.0 + data.get('traffic_level', 0.0)
            
            # Bad pavement slowdown
            pavement_quality = data.get('pavement_quality', 'good')
            if pavement_quality == 'bad':
                speed_kmh *= 0.8  # 20% slower on bad roads (more realistic)
            
            effective_speed_kmh = speed_kmh / traffic_factor
            if effective_speed_kmh < 5:
                effective_speed_kmh = 5  # Minimum speed
            
            # Time = Distance / Speed (convert to seconds)
            segment_time_hours = (length_m / 1000.0) / effective_speed_kmh
            time_seconds += segment_time_hours * 3600
            
            # ** FEATURE 1: Cargo Integrity Damage **
            if pavement_quality == 'bad':
                # Apply damage to fragile items in cargo
                # ✅ REDUZIR: 0.5% por 100m (era 0.8% ou 1.5%)
                # Com penalização 40x, Smart ainda pode passar por 200-300m ruins
                # Precisamos que isso cause <5% de dano
                # damage_per_100m = 0.5  # Mais realista
                damage_per_100m = 1  # Mais realista
                damage_ticks = (length_m / 100.0) * damage_per_100m
                
                for order in self.truck.get_fragile_cargo():
                    order.current_integrity -= damage_ticks
                    if order.current_integrity < 0:
                        order.current_integrity = 0.0
        
        return time_seconds / 60.0, distance_meters / 1000.0
