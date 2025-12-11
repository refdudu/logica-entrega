"""
Basic Search Algorithms module.

Implements Depth-First Search (DFS) and Breadth-First Search (BFS)
for graph traversal and pathfinding, plus integrated SearchEngine.
"""

from typing import List, Optional, Set, Tuple
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
    
    def find_all_routes(self, start: int, goal: int, max_routes: int = 5) -> List[List[int]]:
        """DFS modificado para encontrar múltiplas rotas alternativas.
        
        Uso: Quando A* encontra obstáculo, explorar alternativas.
        
        Args:
            start: Starting node ID
            goal: Target node ID
            max_routes: Maximum number of routes to find
            
        Returns:
            List of routes (each route is a list of node IDs),
            sorted by total cost (shortest first)
        """
        if start not in self.graph or goal not in self.graph:
            return []
        
        if start == goal:
            return [[start]]
        
        all_paths = []
        
        def dfs_recursive(current, goal, path, visited):
            """Recursive DFS helper to find all paths."""
            if len(all_paths) >= max_routes:
                return
            
            if current == goal:
                all_paths.append(path[:])
                return
            
            try:
                neighbors = list(self.graph.neighbors(current))
            except nx.NetworkXError:
                return
            
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    path.append(neighbor)
                    dfs_recursive(neighbor, goal, path, visited)
                    path.pop()
                    visited.remove(neighbor)
        
        # Execute DFS
        dfs_recursive(start, goal, [start], {start})
        
        # Sort routes by total cost
        routes_with_cost = [(route, self.get_path_cost(route)) for route in all_paths]
        routes_with_cost.sort(key=lambda x: x[1])
        
        return [route for route, _ in routes_with_cost]
    
    def find_nearest_from_set(self, start: int, target_nodes: Set[int]) -> tuple:
        """BFS para encontrar o nó mais próximo de um conjunto.
        
        Uso: Encontrar farmácia/depósito mais próximo para reabastecimento.
        
        Args:
            start: Starting node ID
            target_nodes: Set of target node IDs to search for
            
        Returns:
            Tuple (nearest_node_id, path_to_node) where:
            - nearest_node_id: ID of the nearest target node, or None if not found
            - path_to_node: List of node IDs forming the path, or empty list if not found
        """
        if start not in self.graph:
            return None, []
        
        if start in target_nodes:
            return start, [start]
        
        # Queue stores (current_node, path_so_far)
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            current, path = queue.popleft()
            
            try:
                neighbors = list(self.graph.neighbors(current))
            except nx.NetworkXError:
                continue
            
            for neighbor in neighbors:
                if neighbor not in visited:
                    new_path = path + [neighbor]
                    
                    if neighbor in target_nodes:
                        return neighbor, new_path
                    
                    visited.add(neighbor)
                    queue.append((neighbor, new_path))
        
        return None, []


class SearchEngine:
    """Fachada que integra DFS, BFS e A* com casos de uso claros.
    
    Combina algoritmos de busca para fornecer rotas otimizadas
    com fallback automático quando necessário.
    """
    
    def __init__(self, graph: nx.Graph) -> None:
        """Inicializa o motor de busca integrado.
        
        Args:
            graph: NetworkX graph para navegação
        """
        self.graph = graph
        self.basic_search = BasicSearch(graph)
        # A* será importado dinamicamente para evitar dependência circular
        self._astar = None
    
    def _get_astar(self):
        """Lazy loading do A* para evitar imports circulares."""
        if self._astar is None:
            from .astar import AStarNavigator
            self._astar = AStarNavigator(self.graph)
        return self._astar
    
    def route_with_backup(self, start: int, goal: int, is_fragile: bool = False) -> Tuple[List[int], str]:
        """Busca rota otimizada com fallback automático.
        
        Estratégia:
        1. Tenta A* (ótimo e rápido)
        2. Se falhar, usa DFS para encontrar alternativas
        3. Se nenhuma rota, retorna vazio
        
        Args:
            start: Nó inicial
            goal: Nó destino
            is_fragile: Se carga é frágil (evita pavimento ruim)
            
        Returns:
            Tuple (path, method) onde:
            - path: Lista de IDs de nós formando a rota
            - method: String indicando método usado ("astar", "dfs_backup", "no_path")
        """
        # Tentativa 1: A* (ótimo)
        try:
            astar = self._get_astar()
            path = astar.get_path(start, goal, is_fragile)
            if path:
                return path, "astar"
        except Exception as e:
            # A* falhou, continuar para fallback
            pass
        
        # Tentativa 2: DFS para explorar alternativas
        routes = self.basic_search.find_all_routes(start, goal, max_routes=3)
        if routes:
            return routes[0], "dfs_backup"
        
        # Nenhuma rota encontrada
        return [], "no_path"
    
    def find_nearest_depot(self, current_pos: int, depot_nodes: List[int]) -> Tuple[Optional[int], List[int], str]:
        """Usa BFS para encontrar depósito mais próximo (emergências).
        
        Args:
            current_pos: Posição atual
            depot_nodes: Lista de IDs de nós que são depósitos
            
        Returns:
            Tuple (nearest_id, path, method) onde:
            - nearest_id: ID do depósito mais próximo (None se não encontrado)
            - path: Caminho até o depósito
            - method: Sempre "bfs"
        """
        nearest, path = self.basic_search.find_nearest_from_set(current_pos, set(depot_nodes))
        return nearest, path, "bfs"
    
    def explore_alternatives(self, start: int, goal: int, max_routes: int = 5) -> List[Tuple[List[int], float]]:
        """Explora múltiplas rotas alternativas com seus custos.
        
        Útil para:
        - Análise de rotas alternativas
        - Comparação de custos
        - Planos de contingência
        
        Args:
            start: Nó inicial
            goal: Nó destino
            max_routes: Número máximo de rotas a retornar
            
        Returns:
            Lista de tuplas (rota, custo) ordenadas por custo (menor primeiro)
        """
        routes = self.basic_search.find_all_routes(start, goal, max_routes)
        routes_with_cost = [(route, self.basic_search.get_path_cost(route)) for route in routes]
        return routes_with_cost

