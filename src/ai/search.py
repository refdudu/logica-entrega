"""
Basic Search Algorithms module.

Implements Depth-First Search (DFS) and Breadth-First Search (BFS)
for graph traversal and pathfinding.
"""

from typing import List, Optional, Set
from collections import deque
import networkx as nx


class BasicSearch:
    """Basic graph search algorithms implementation.
    
    Provides DFS and BFS pathfinding methods that work with NetworkX graphs.
    These are uninformed search algorithms that don't use heuristics.
    """
    
    def __init__(self, graph: nx.Graph) -> None:
        """Initialize the search engine.
        
        Args:
            graph: NetworkX graph to search
        """
        self.graph = graph
    
    def dfs(self, start: int, goal: int) -> List[int]:
        """Depth-First Search pathfinding.
        
        Uses a stack (LIFO) to explore paths, going as deep as possible
        before backtracking. Not guaranteed to find the shortest path.
        
        Args:
            start: Starting node ID
            goal: Target node ID
            
        Returns:
            List of node IDs forming a path from start to goal,
            or empty list if no path exists
        """
        if start not in self.graph or goal not in self.graph:
            return []
        
        if start == goal:
            return [start]
        
        # Stack stores (current_node, path_so_far)
        stack: List[tuple] = [(start, [start])]
        visited: Set[int] = set()
        
        while stack:
            current, path = stack.pop()
            
            if current in visited:
                continue
            
            visited.add(current)
            
            if current == goal:
                return path
            
            # Get neighbors (handle MultiDiGraph)
            try:
                neighbors = list(self.graph.neighbors(current))
            except nx.NetworkXError:
                continue
            
            # Add unvisited neighbors to stack (reverse for consistent ordering)
            for neighbor in reversed(neighbors):
                if neighbor not in visited:
                    stack.append((neighbor, path + [neighbor]))
        
        return []  # No path found
    
    def bfs(self, start: int, goal: int) -> List[int]:
        """Breadth-First Search pathfinding.
        
        Uses a queue (FIFO) to explore paths level by level.
        Guaranteed to find the shortest path (by number of edges).
        
        Args:
            start: Starting node ID
            goal: Target node ID
            
        Returns:
            List of node IDs forming the shortest path from start to goal,
            or empty list if no path exists
        """
        if start not in self.graph or goal not in self.graph:
            return []
        
        if start == goal:
            return [start]
        
        # Queue stores (current_node, path_so_far)
        queue: deque = deque([(start, [start])])
        visited: Set[int] = {start}
        
        while queue:
            current, path = queue.popleft()
            
            # Get neighbors (handle MultiDiGraph)
            try:
                neighbors = list(self.graph.neighbors(current))
            except nx.NetworkXError:
                continue
            
            for neighbor in neighbors:
                if neighbor not in visited:
                    new_path = path + [neighbor]
                    
                    if neighbor == goal:
                        return new_path
                    
                    visited.add(neighbor)
                    queue.append((neighbor, new_path))
        
        return []  # No path found
    
    def get_path_cost(self, path: List[int]) -> float:
        """Calculate the total cost of a path using edge lengths.
        
        Args:
            path: List of node IDs forming the path
            
        Returns:
            Total cost (sum of edge lengths), or infinity if path is invalid
        """
        if not path or len(path) < 2:
            return 0.0
        
        total_cost = 0.0
        
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            
            # Get edge data (handle MultiDiGraph)
            edge_data = self.graph.get_edge_data(u, v)
            if not edge_data:
                return float('inf')
            
            # Get first edge if multiple exist
            data = edge_data[0] if isinstance(edge_data, dict) and 0 in edge_data else edge_data
            
            # Use length as cost
            total_cost += data.get('length', 100)
        
        return total_cost
