import osmnx as ox
import networkx as nx
import random

class MapLoader:
    def __init__(self, place_name="Santa Rosa, Rio Grande do Sul, Brazil"):
        self.place_name = place_name
        self.graph = None

    def load_graph(self):
        print(f"Loading map for {self.place_name} (Urban Area)...")
        # Center of Santa Rosa, RS
        point = (-27.8727, -54.4781)
        # Download drive network within 3km radius
        self.graph = ox.graph_from_point(point, dist=3000, network_type='drive')
        
        # Convert to undirected for simpler navigation (optional, but realistic for some streets)
        # For now, keep directed but maybe add reverse edges if needed. 
        # OSMnx graphs are MultiDiGraphs.
        
        # Inject variables into edges
        self._inject_variables()
        
        return self.graph

    def _inject_variables(self):
        """Adds simulation variables to each street segment (edge)."""
        for u, v, k, data in self.graph.edges(keys=True, data=True):
            # Distance is usually already there (length in meters)
            length = data.get('length', 100)
            
            # Traffic: 0.0 (Empty) to 1.0 (Jam)
            data['traffic_level'] = random.uniform(0.0, 0.8)
            
            # Safety: 0.0 (Dangerous) to 1.0 (Safe)
            data['safety_index'] = random.uniform(0.5, 1.0)
            
            # Pavement: 'good', 'fair', 'bad'
            data['pavement_quality'] = random.choice(['good', 'good', 'fair', 'bad'])
            
            # Speed Limit (if not present, guess)
            if 'maxspeed' not in data:
                data['maxspeed'] = 40 # km/h default
            
            # Calculate estimated time (cost) based on length, speed, and traffic
            # Time = Distance / (Speed * (1 - Traffic))
            try:
                speed_limit = float(data['maxspeed']) if isinstance(data['maxspeed'], (int, float, str)) and str(data['maxspeed']).replace('.','',1).isdigit() else 40.0
            except:
                speed_limit = 40.0
                
            effective_speed = speed_limit * (1.0 - data['traffic_level'] * 0.8) # Traffic reduces speed
            if effective_speed < 5: effective_speed = 5
            
            data['travel_time'] = (length / 1000) / effective_speed * 3600 # seconds

    def get_random_node(self):
        return random.choice(list(self.graph.nodes()))
