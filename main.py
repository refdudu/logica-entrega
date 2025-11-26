import tkinter as tk
from tkinter import messagebox

import ai_core
import random
from ui.map_view import MapView
from ui.control_panel import ControlPanel

class LogisticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Integrado de Logística com IA (Refatorado)")
        self.root.geometry("1200x800")

        # State
        self.orders = []
        self.depot_pos = (2, 2)
        self.optimized_sequence = []
        
        # AI Engines
        self.fuzzy_engine = ai_core.FuzzyPriority()
        self.neural_engine = ai_core.NeuralPredictor()
        self.astar_engine = ai_core.AStarNavigator(grid_size=20)

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        # Control Panel (Left)
        self.control_panel = ControlPanel(self.root, self)
        self.control_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Map View (Right)
        self.map_view = MapView(self.root, self.root)
        self.map_view.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        
        # Initial Draw
        self.map_view.draw_grid(self.astar_engine.grid, self.depot_pos)

    # --- Controller Methods ---

    def reset_simulation(self, silent=False):
        self.orders = []
        self.optimized_sequence = []
        self.control_panel.update_table(self.orders)
        self.map_view.draw_grid(self.astar_engine.grid, self.depot_pos)
        
        if not silent:
            messagebox.showinfo("Info", "Simulação reiniciada.")

    def step1_generate(self):
        num_orders = self.control_panel.get_order_count()
        if num_orders is None:
            messagebox.showerror("Erro de Entrada", "Por favor, insira um número válido entre 1 e 20.")
            return

        self.reset_simulation(silent=True)
        
        for i in range(num_orders):
            x, y = tk.IntVar(), tk.IntVar()
            x, y = random.randint(0, 19), random.randint(0, 19)
            order = ai_core.Order(i + 1, x, y, random.randint(10, 120), random.uniform(1, 30), random.choice([0, 1]))
            self.orders.append(order)
        
        self.control_panel.update_table(self.orders)
        self.map_view.draw_grid(self.astar_engine.grid, self.depot_pos)
        self.map_view.draw_orders(self.orders)
        messagebox.showinfo("Passo 1", f"{num_orders} pedidos gerados! Observe os pontos no mapa.")

    def step2_analyze(self):
        if not self.orders:
            messagebox.showwarning("Aviso", "Gere os pedidos no Passo 1 primeiro.")
            return
        
        for order in self.orders:
            self.fuzzy_engine.calculate(order, self.depot_pos)
            self.neural_engine.predict(order)

        self.control_panel.update_table(self.orders)
        self.map_view.draw_grid(self.astar_engine.grid, self.depot_pos)
        self.map_view.draw_analyzed_orders(self.orders)
        
        try:
            focused_widget = self.root.focus_get()
            if focused_widget and '2. Analisar' in focused_widget.cget('text'):
                messagebox.showinfo("Passo 2", "Análise Completa!\nVermelho = Alto Risco de Atraso\nVerde = Baixo Risco")
        except (tk.TclError, AttributeError):
            pass

    def step3_optimize(self):
        if not self.orders:
            messagebox.showwarning("Aviso", "Execute os Passos 1 e 2 primeiro.")
            return
        
        ga = ai_core.GeneticTSP(self.orders, self.depot_pos)
        self.optimized_sequence = ga.solve()
        
        self.map_view.draw_grid(self.astar_engine.grid, self.depot_pos)
        self.map_view.draw_analyzed_orders(self.orders)
        
        route_points = [self.depot_pos] + [(self.orders[i].x, self.orders[i].y) for i in self.optimized_sequence] + [self.depot_pos]
        self.map_view.draw_optimized_route(route_points)
        
        seq_str = " -> ".join([f"P{self.orders[i].id}" for i in self.optimized_sequence])
        messagebox.showinfo("Passo 3", f"Melhor sequência encontrada:\nDepósito -> {seq_str} -> Depósito")

    def step4_navigate(self):
        if not self.optimized_sequence:
            messagebox.showwarning("Aviso", "Primeiro otimize a rota no Passo 3.")
            return

        self.control_panel.set_nav_button_state(tk.DISABLED)
        
        self.map_view.draw_grid(self.astar_engine.grid, self.depot_pos)
        self.map_view.draw_analyzed_orders(self.orders)

        stops = [self.depot_pos] + [(self.orders[i].x, self.orders[i].y) for i in self.optimized_sequence] + [self.depot_pos]
        
        full_journey_path = []
        for i in range(len(stops) - 1):
            start = (int(stops[i][0]), int(stops[i][1]))
            end = (int(stops[i+1][0]), int(stops[i+1][1]))
            path_segment = self.astar_engine.get_path(start, end)
            if path_segment:
                full_journey_path.extend(path_segment if i == 0 else path_segment[1:])
        
        if full_journey_path:
            self.map_view.animate_route(full_journey_path, self.on_animation_complete)
        else:
            messagebox.showerror("Erro", "Não foi possível calcular o caminho.")
            self.control_panel.set_nav_button_state(tk.NORMAL)

    def on_animation_complete(self):
        self.control_panel.set_nav_button_state(tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = LogisticsApp(root)
    root.mainloop()
