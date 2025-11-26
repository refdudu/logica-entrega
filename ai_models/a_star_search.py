import numpy as np
import heapq
import random

# --- TÉCNICA 4: A* (Navegação Física no Mapa) ---
class AStarNavigator:
    def __init__(self, grid_size=20):
        self.grid_size = grid_size
        self.grid = np.zeros((grid_size, grid_size))
        # Adiciona obstáculos (Prédios/Bloqueios)
        for _ in range(40):
            x, y = random.randint(0, grid_size-1), random.randint(0, grid_size-1)
            self.grid[x][y] = 1 

    def heuristic(self, a, b):
        return abs(b[0] - a[0]) + abs(b[1] - a[1])

    def get_path(self, start, end):
        # Garante que start/end não são obstáculos
        self.grid[start] = 0
        self.grid[end] = 0
        
        neighbors = [(0,1),(0,-1),(1,0),(-1,0)]
        open_list = []
        heapq.heappush(open_list, (0, start))
        came_from = {}
        g_score = {start: 0}
        
        while open_list:
            current = heapq.heappop(open_list)[1]

            if current == end:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]

            for dx, dy in neighbors:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < self.grid_size and 0 <= neighbor[1] < self.grid_size:
                    if self.grid[neighbor] == 1: continue
                    
                    temp_g = g_score[current] + 1
                    if temp_g < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        g_score[neighbor] = temp_g
                        f_score = temp_g + self.heuristic(neighbor, end)
                        heapq.heappush(open_list, (f_score, neighbor))
        return [start, end] # Retorna linha reta se falhar (fallback)
