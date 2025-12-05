import networkx as nx

# --- TÉCNICA 4: A* (Navegação Física no Mapa) ---
class AStarNavigator:
    def __init__(self, graph):
        self.graph = graph

    def get_path(self, start_node, end_node):
        """
        Finds the shortest path between two nodes in the graph.
        Uses 'travel_time' as the weight.
        """
        try:
            # networkx has a built-in astar_path, but dijkstra is often faster for simple weighted graphs without a perfect heuristic
            # We can use nx.shortest_path with weight='travel_time'
            path = nx.shortest_path(self.graph, start_node, end_node, weight='travel_time')
            return path
        except nx.NetworkXNoPath:
            return []
        except Exception as e:
            print(f"Pathfinding error: {e}")
            return []

    def get_path_cost(self, start_node, end_node):
        try:
            return nx.shortest_path_length(self.graph, start_node, end_node, weight='travel_time')
        except:
            return float('inf')
