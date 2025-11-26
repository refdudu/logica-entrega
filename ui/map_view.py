import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class MapView(tk.Frame):
    def __init__(self, parent, root):
        super().__init__(parent)
        self.root = root
        
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(expand=True, fill=tk.BOTH)

    def draw_grid(self, grid_data, depot_pos):
        self.ax.clear()
        self.ax.imshow(grid_data, cmap='Greys', origin='lower')
        self.ax.plot(depot_pos[1], depot_pos[0], 
                     marker='D',
                     color='red',
                     markersize=18,
                     label='Depósito',
                     zorder=10)
        self.ax.set_title("Mapa da Cidade")
        self.ax.grid(True, which='both', color='lightgray', linestyle='-', linewidth=0.5)
        self.canvas.draw()

    def draw_orders(self, orders):
        for o in orders:
            self.ax.plot(o.y, o.x, 'bo', markersize=8)
            self.ax.text(o.y + 0.3, o.x + 0.3, f"P{o.id}", color="blue")
        self.canvas.draw()

    def draw_analyzed_orders(self, orders):
        for o in orders:
            color = 'red' if o.delay_risk == "ALTO" else 'green'
            self.ax.plot(o.y, o.x, marker='o', color=color, markersize=10)
            self.ax.text(o.y + 0.3, o.x + 0.3, f"P{o.id}\nPri:{o.priority:.1f}", fontsize=8)
        self.canvas.draw()
        
    def draw_optimized_route(self, route_points):
        ys, xs = zip(*route_points)
        self.ax.plot(xs, ys, 'k--', alpha=0.5, label='Sequência Lógica')
        self.ax.legend()
        self.canvas.draw()

    def animate_route(self, path, on_animation_complete):
        self.ax.set_title("Animando Rota Executável (A*)...")
        self.canvas.draw()
        self._animate_segment(path, 0, on_animation_complete)

    def _animate_segment(self, path, index, on_animation_complete):
        if index >= len(path) - 1:
            self.ax.set_title("Rota Final Executável (A*)")
            self.canvas.draw()
            if on_animation_complete:
                on_animation_complete()
            return

        p1 = path[index]
        p2 = path[index+1]

        self.ax.plot([p1[1], p2[1]], [p1[0], p2[0]], linewidth=2.5, color="#0077be", solid_capstyle='round')
        self.canvas.draw_idle()

        self.root.after(40, self._animate_segment, path, index + 1, on_animation_complete)
