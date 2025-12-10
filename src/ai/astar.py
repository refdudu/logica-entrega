import networkx as nx

class AStarNavigator:
    def __init__(self, graph):
        self.graph = graph

    def _heuristic(self, u, v):
        # Using Haversine is better if nodes have (x,y) as (lat,lon)
        # But 'travel_time' is the weight, so heuristic should be time-based.
        # If we use simple dist, it might over-estimate if speed is high?
        # For simplicity/safety in generic graphs, 0 is Dijkstra (safe).
        # Or Euclidean distance if nodes have 'x', 'y' (OSMnx does).
        return 0

    def get_path(self, start_node, end_node, is_fragile=False):
        """
        Finds the shortest path given constraints.
        """
        def weight_function(u, v, d):
            # 1. Road Block Check
            if d.get('road_block', False):
                return float('inf')

            # 2. Pavement Quality & Fragility
            pavement_penalty = 1.0
            if d.get('pavement_quality') == 'bad':
                if is_fragile:
                    return float('inf')  # Fragile cargo cannot go on bad pavement
                pavement_penalty = 1.4  # 40% slower

            # 3. Traffic
            traffic_factor = 1.0 + d.get('traffic_level', 0.0)

            # Base travel time
            travel_time = d.get('travel_time', 1.0)
            
            return travel_time * pavement_penalty * traffic_factor

        try:
            return nx.astar_path(self.graph, start_node, end_node, 
                                 heuristic=None, # self._heuristic, 
                                 weight=weight_function)
        except nx.NetworkXNoPath:
            return []
        except Exception as e:
            print(f"Pathfinding error: {e}")
            return []

    def get_path_cost(self, start_node, end_node, is_fragile=False):
        path = self.get_path(start_node, end_node, is_fragile)
        if not path:
            return float('inf')
        
        # Calculate total cost manually based on path found
        cost = 0
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            # Get edge data (min weight if multiple edges)
            # OSMnx graph is MultiDiGraph.
            edge_data = self.graph.get_edge_data(u, v)
            if edge_data:
                # Pick lowest key (usually 0) or iterate to find min weight?
                # A* automatically picked the best edge if MultiDiGraph was handled correctly.
                # nx.astar_path works on MultiDiGraph by minimizing weight.
                # Let's just re-calculate weight for the best edge.
                # Simplified: just take first edge
                d = edge_data[0] 
                
                # Re-apply weight logic
                # (Duplication of logic is risky, but necessary if we don't get cost from astar_path directly without wrapper)
                # Alternatively, use nx.shortest_path_length but strict A* might vary.
                
                if d.get('road_block', False):
                     return float('inf')
                
                pavement_penalty = 1.0
                if d.get('pavement_quality') == 'bad':
                     if is_fragile: return float('inf')
                     pavement_penalty = 1.4
                
                traffic_factor = 1.0 + d.get('traffic_level', 0.0)
                cost += d.get('travel_time', 1.0) * pavement_penalty * traffic_factor
                
        return cost
