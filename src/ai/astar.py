from typing import List, Tuple
import networkx as nx
import math

class AStarNavigator:
    """Navigator using A* algorithm with real-world constraints.
    
    Implements A* pathfinding considering road blocks, pavement quality,
    traffic levels, and cargo fragility.
    """
    
    def __init__(self, graph: nx.Graph) -> None:
        """Initialize the A* navigator.
        
        Args:
            graph: NetworkX graph with nodes containing 'x', 'y' coordinates
        """
        self.graph = graph

    def _heuristic(self, u: int, v: int) -> float:
        """Calculate Euclidean distance between two nodes.
        
        Args:
            u: Source node ID
            v: Target node ID
            
        Returns:
            Euclidean distance between nodes (admissible heuristic for A*)
        """
        try:
            # Get node positions (OSMnx uses 'x' and 'y' attributes)
            pos_u = (self.graph.nodes[u]['x'], self.graph.nodes[u]['y'])
            pos_v = (self.graph.nodes[v]['x'], self.graph.nodes[v]['y'])
            
            # Calculate Euclidean distance
            dx = pos_u[0] - pos_v[0]
            dy = pos_u[1] - pos_v[1]
            return math.sqrt(dx * dx + dy * dy)
        except (KeyError, TypeError):
            # Fallback to 0 if coordinates are missing
            return 0.0

    def get_path(self, start_node: int, end_node: int, is_fragile: bool = False) -> List[int]:
        """Find the optimal path between two nodes considering constraints.
        
        Args:
            start_node: Starting node ID
            end_node: Destination node ID  
            is_fragile: Whether cargo is fragile (avoids bad pavement)
            
        Returns:
            List of node IDs forming the optimal path, or empty list if no path exists
        """
        def weight_function(u, v, d):
            # 1. Road Block Check
            if d.get('road_block', False):
                return float('inf')

            # 2. Pavement Quality & Fragility
            pavement_penalty = 1.0
            if d.get('pavement_quality') == 'bad':
                if is_fragile:
                    # Massive penalty but still navigable as last resort
                    pavement_penalty = 5000.0
                else:
                    pavement_penalty = 1.4  # 40% slower

            # 3. Traffic
            traffic_factor = 1.0 + d.get('traffic_level', 0.0)

            # Base travel time
            travel_time = d.get('travel_time', 1.0)
            
            return travel_time * pavement_penalty * traffic_factor

        try:
            return nx.astar_path(
                self.graph, 
                start_node, 
                end_node,
                heuristic=self._heuristic,
                weight=weight_function
            )
        except nx.NetworkXNoPath:
            return []
        except Exception as e:
            print(f"Pathfinding error: {e}")
            return []

    def get_path_cost(self, start_node: int, end_node: int, is_fragile: bool = False) -> float:
        """Calculate the cost of the optimal path between two nodes.
        
        Args:
            start_node: Starting node ID
            end_node: Destination node ID
            is_fragile: Whether the cargo is fragile (affects route selection)
            
        Returns:
            Total cost of the path, or infinity if no valid path exists
        """
        def weight_function(u, v, d):
            # Same logic as in get_path for consistency
            if d.get('road_block', False):
                return float('inf')

            pavement_penalty = 1.0
            if d.get('pavement_quality') == 'bad':
                if is_fragile:
                    # Massive penalty but still navigable as last resort
                    pavement_penalty = 5000.0
                else:
                    pavement_penalty = 1.4

            traffic_factor = 1.0 + d.get('traffic_level', 0.0)
            travel_time = d.get('travel_time', 1.0)
            
            return travel_time * pavement_penalty * traffic_factor
        
        try:
            # Use NetworkX's efficient shortest_path_length
            return nx.shortest_path_length(
                self.graph,
                start_node,
                end_node,
                weight=weight_function
            )
        except nx.NetworkXNoPath:
            return float('inf')
        except Exception as e:
            print(f"Path cost calculation error: {e}")
            return float('inf')
