import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import osmnx as ox
import networkx as nx

class MapView(tk.Frame):
    def __init__(self, parent, root, title="Mapa"):
        super().__init__(parent)
        self.root = root
        self.map_title = title
        
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(expand=True, fill=tk.BOTH)
        
        # Add Toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        self.truck_marker = None
        
        # Legend (could be improved)
        # We will add legend when drawing the graph

    def draw_graph(self, graph, depot_node):
        self.ax.clear()
        self.truck_marker = None
        
        # Draw edges
        for u, v, data in graph.edges(data=True):
            x1 = graph.nodes[u]['x']
            y1 = graph.nodes[u]['y']
            x2 = graph.nodes[v]['x']
            y2 = graph.nodes[v]['y']
            
            # 1. Road Block?
            road_block = data.get('road_block', False)
            if road_block:
                # Draw Red X in middle of edge
                mx, my = (x1+x2)/2, (y1+y2)/2
                self.ax.plot(mx, my, 'rx', markersize=8, markeredgewidth=2, zorder=5)
                # Dotted line for blocked road?
                self.ax.plot([x1, x2], [y1, y2], color='red', linestyle=':', linewidth=1, zorder=1)
                continue

            # 2. Traffic / Standard
            traffic = data.get('traffic_level', 0)
            color = 'gray'
            if traffic > 0.7: color = 'red'
            elif traffic > 0.4: color = 'orange'
            
            self.ax.plot([x1, x2], [y1, y2], color=color, linewidth=1, zorder=1)

        # Draw depot
        dx = graph.nodes[depot_node]['x']
        dy = graph.nodes[depot_node]['y']
        self.ax.plot(dx, dy, marker='D', color='yellow', markeredgecolor='black', markersize=12, label='Depósito', zorder=10)
        
        self.ax.set_title(self.map_title)
        self.ax.axis('off')
        
        self.canvas.draw()

    def draw_orders(self, orders, graph):
        for o in orders:
            node = graph.nodes[o.node_id]
            x, y = node['x'], node['y']
            self.ax.plot(x, y, 'o', color='blue', markeredgecolor='white', markeredgewidth=1.5, markersize=8, zorder=20)
            self.ax.text(x, y, f"P{o.id}", color="white", fontsize=8, fontweight='bold',
                         bbox=dict(facecolor='blue', edgecolor='white', boxstyle='round,pad=0.2', alpha=0.8), zorder=25)
        self.canvas.draw()

    def draw_analyzed_orders(self, orders, graph):
        for o in orders:
            node = graph.nodes[o.node_id]
            x, y = node['x'], node['y']
            color = 'red' if o.risk_level == "HIGH" else 'green'
            self.ax.plot(x, y, marker='o', color=color, markeredgecolor='white', markeredgewidth=1.5, markersize=10, zorder=20)
            self.ax.text(x, y, f"P{o.id}\nPri:{o.fuzzy_priority:.1f}", fontsize=7, color='white', fontweight='bold',
                         bbox=dict(facecolor=color, edgecolor='white', boxstyle='round,pad=0.2', alpha=0.8), zorder=25)
        self.canvas.draw()
        
    def draw_optimized_route(self, route_nodes, graph):
        for i in range(len(route_nodes) - 1):
            u = route_nodes[i]
            v = route_nodes[i+1]
            x1, y1 = graph.nodes[u]['x'], graph.nodes[u]['y']
            x2, y2 = graph.nodes[v]['x'], graph.nodes[v]['y']
            self.ax.plot([x1, x2], [y1, y2], 'k--', alpha=0.5, zorder=5)
        self.canvas.draw()

    def animate_route(self, full_path_nodes, graph, on_animation_complete):
        self.ax.set_title("Animando Rota (Caminhão em Movimento)...")
        
        # Initialize Truck Marker (Square 's')
        if not full_path_nodes: return
        start_node = full_path_nodes[0]
        sx, sy = graph.nodes[start_node]['x'], graph.nodes[start_node]['y']
        
        # Remove old marker if exists
        if self.truck_marker:
            self.truck_marker.remove()
            
        self.truck_marker, = self.ax.plot(sx, sy, marker='s', color='black', markerfacecolor='yellow', markeredgewidth=2, markersize=12, zorder=40)
        
        self.canvas.draw()
        self._animate_segment(full_path_nodes, 0, graph, on_animation_complete)

    def _animate_segment(self, path_nodes, index, graph, on_animation_complete):
        if index >= len(path_nodes) - 1:
            self.ax.set_title("Entrega Concluída!")
            if self.truck_marker:
                 # Check if we removed it? No, keep it at end pos
                 pass
            self.canvas.draw()
            if on_animation_complete:
                on_animation_complete()
            return

        u = path_nodes[index]
        v = path_nodes[index+1]
        
        x1, y1 = graph.nodes[u]['x'], graph.nodes[u]['y']
        x2, y2 = graph.nodes[v]['x'], graph.nodes[v]['y']

        # Draw trail
        self.ax.plot([x1, x2], [y1, y2], linewidth=3, color="#0077be", solid_capstyle='round', zorder=30)
        
        # Move Truck Marker
        self.truck_marker.set_data([x2], [y2]) # Move to next node
        
        self.canvas.draw_idle()

        # Speed of animation
        self.root.after(100, self._animate_segment, path_nodes, index + 1, graph, on_animation_complete)
