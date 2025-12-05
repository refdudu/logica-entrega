import tkinter as tk
import matplotlib.pyplot as plt
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import osmnx as ox
import networkx as nx

class MapView(tk.Frame):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.root = root
        
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(expand=True, fill=tk.BOTH)
        
        # Add Toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        self.traffic_manager = None
        self.light_patches = {}

    def set_traffic_manager(self, manager):
        self.traffic_manager = manager

    def draw_graph(self, graph, depot_node):
        self.ax.clear()
        self.light_patches = {}
        
        # Plot the graph using osmnx
        # ox.plot_graph draws to a new figure by default, we need to draw to our axis
        # But ox.plot_graph is complex. Let's use a simpler approach for embedding:
        # Draw edges
        for u, v, data in graph.edges(data=True):
            x1 = graph.nodes[u]['x']
            y1 = graph.nodes[u]['y']
            x2 = graph.nodes[v]['x']
            y2 = graph.nodes[v]['y']
            
            # Color based on traffic?
            traffic = data.get('traffic_level', 0)
            color = 'gray'
            if traffic > 0.7: color = 'red'
            elif traffic > 0.4: color = 'orange'
            
            self.ax.plot([x1, x2], [y1, y2], color=color, linewidth=1, zorder=1)

        # Draw depot
        dx = graph.nodes[depot_node]['x']
        dy = graph.nodes[depot_node]['y']
        self.ax.plot(dx, dy, marker='D', color='yellow', markersize=12, label='Depósito', zorder=10)
        
        self.ax.set_title("Mapa de Santa Rosa - RS")
        self.ax.axis('off') # Hide axis for map look
        
        self.canvas.draw()

    def draw_traffic_lights(self):
        self.light_patches = {}
        for (x, y), state in self.traffic_manager.lights.items():
            color = 'red' if state == 'RED' else 'green'
            # Draw a small circle for the light
            patch = plt.Circle((y, x), 0.3, color=color, zorder=15)
            self.ax.add_patch(patch)
            self.light_patches[(x, y)] = patch

    def update_lights(self):
        """Updates the color of existing traffic lights without redrawing the whole grid."""
        if not self.traffic_manager:
            return
            
        for (x, y), state in self.traffic_manager.lights.items():
            if (x, y) in self.light_patches:
                color = 'red' if state == 'RED' else 'green'
                self.light_patches[(x, y)].set_color(color)
        
        self.canvas.draw_idle()

    def draw_orders(self, orders, graph):
        for o in orders:
            # Get coords from node_id
            node = graph.nodes[o.node_id]
            x, y = node['x'], node['y']
            
            # Blue circle with white edge for better contrast
            self.ax.plot(x, y, 'o', color='blue', markeredgecolor='white', markeredgewidth=1.5, markersize=8, zorder=20)
            # Text with background box
            self.ax.text(x, y, f"P{o.id}", color="white", fontsize=8, fontweight='bold',
                         bbox=dict(facecolor='blue', edgecolor='white', boxstyle='round,pad=0.2', alpha=0.8), zorder=25)
        self.canvas.draw()

    def draw_analyzed_orders(self, orders, graph):
        for o in orders:
            node = graph.nodes[o.node_id]
            x, y = node['x'], node['y']
            
            color = 'red' if o.delay_risk == "ALTO" else 'green'
            # Circle with white edge
            self.ax.plot(x, y, marker='o', color=color, markeredgecolor='white', markeredgewidth=1.5, markersize=10, zorder=20)
            # Text with background box
            self.ax.text(x, y, f"P{o.id}\nPri:{o.priority:.1f}", fontsize=7, color='white', fontweight='bold',
                         bbox=dict(facecolor=color, edgecolor='white', boxstyle='round,pad=0.2', alpha=0.8), zorder=25)
        self.canvas.draw()
        
    def draw_optimized_route(self, route_nodes, graph):
        # route_nodes is a list of node IDs
        # We need to plot the path between them
        # For visualization, just straight lines between sequence points is confusing on a real map
        # Ideally we plot the full path. But for "Step 3", maybe just show the sequence order?
        # Let's draw arrows between sequence stops.
        
        for i in range(len(route_nodes) - 1):
            u = route_nodes[i]
            v = route_nodes[i+1]
            x1, y1 = graph.nodes[u]['x'], graph.nodes[u]['y']
            x2, y2 = graph.nodes[v]['x'], graph.nodes[v]['y']
            self.ax.plot([x1, x2], [y1, y2], 'k--', alpha=0.5, zorder=5)
            
        self.canvas.draw()

    def animate_route(self, full_path_nodes, graph, on_animation_complete):
        self.ax.set_title("Animando Rota Real...")
        self.canvas.draw()
        self._animate_segment(full_path_nodes, 0, graph, on_animation_complete)

    def _animate_segment(self, path_nodes, index, graph, on_animation_complete):
        if index >= len(path_nodes) - 1:
            self.ax.set_title("Entrega Concluída!")
            self.canvas.draw()
            if on_animation_complete:
                on_animation_complete()
            return

        u = path_nodes[index]
        v = path_nodes[index+1]
        
        x1, y1 = graph.nodes[u]['x'], graph.nodes[u]['y']
        x2, y2 = graph.nodes[v]['x'], graph.nodes[v]['y']

        self.ax.plot([x1, x2], [y1, y2], linewidth=3, color="#0077be", solid_capstyle='round', zorder=30)
        self.canvas.draw_idle()

        # Delay based on edge travel time? For now fixed speed
        self.root.after(50, self._animate_segment, path_nodes, index + 1, graph, on_animation_complete)
