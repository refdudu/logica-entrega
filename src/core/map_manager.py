import osmnx as ox
import networkx as nx
import random
import os

class MapManager:
    def __init__(self, place_name="Santa Rosa, Rio Grande do Sul, Brazil"):
        self.place_name = place_name
        self.graph = None
        # Configure osmnx cache
        ox.settings.use_cache = True
        ox.settings.log_console = False

    def load_graph(self):
        """Loads the graph from OSMnx and enriches it with simulation data."""
        print(f"Loading map for {self.place_name}...")
        # Load from a point in Santa Rosa center (Zoo/Parque)
        # Center approx: -27.8727, -54.4781
        point = (-27.8727, -54.4781)
        # Reduced distance to 1000m for "Zoom" effect (City Center)
        print("Loading zoomed map (1km radius from center)...")
        self.graph = ox.graph_from_point(point, dist=1000, network_type='drive')

        self._enrich_edges()
        print(f"Map loaded: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges.")
        return self.graph

    def _enrich_edges(self):
        """Adds simulation attributes to edges."""
        for u, v, k, data in self.graph.edges(keys=True, data=True):
            # Traffic: 0.0 (None) to 1.0 (Heavy)
            data['traffic_level'] = random.uniform(0.0, 1.0)
            
            # Pavement quality
            data['pavement_quality'] = random.choice(['good', 'good', 'fair', 'bad'])
            
            # Road Block (Very Rare event)
            # 0.2% chance of being blocked to avoid sealing off areas
            data['road_block'] = random.random() < 0.002

            # Store speed limit helper
            if 'maxspeed' not in data:
                data['maxspeed'] = 40
    
    def enrich_map_with_obstacles(self, graph: nx.MultiDiGraph, seed: int = 42) -> nx.MultiDiGraph:
        """Enrich map with consistent obstacles using a seed.
        
        This ensures both Legacy and Smart simulations face the same challenges.
        
        Args:
            graph: NetworkX graph to enrich
            seed: Random seed for reproducibility
            
        Returns:
            Enriched graph with pavement quality and road blocks
        """
        print(f"Enriching map with obstacles (seed={seed})...")
        random.seed(seed)
        
        obstacle_count = {'bad_pavement': 0, 'road_blocks': 0}
        
        for u, v, k, data in graph.edges(keys=True, data=True):
            # 10% chance of bad pavement (potholes) - reduced for better gameplay
            if random.random() < 0.10:
                data['pavement_quality'] = 'bad'
                obstacle_count['bad_pavement'] += 1
            elif 'pavement_quality' not in data:
                data['pavement_quality'] = 'good'
            
            # 1% chance of road block - reduced for better gameplay
            if random.random() < 0.01:
                data['road_block'] = True
                obstacle_count['road_blocks'] += 1
            elif 'road_block' not in data:
                data['road_block'] = False
            
            # Ensure traffic_level exists
            if 'traffic_level' not in data:
                data['traffic_level'] = random.uniform(0.0, 0.5)
        
        # Reset random state
        random.seed()
        
        print(f"  Added {obstacle_count['bad_pavement']} bad pavement sections")
        print(f"  Added {obstacle_count['road_blocks']} road blocks")
        
        return graph

    def get_random_node(self):
        """Returns a random node ID from the graph."""
        if not self.graph:
            raise ValueError("Graph not loaded. Call load_graph() first.")
        return random.choice(list(self.graph.nodes()))
