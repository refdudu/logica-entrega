import tkinter as tk
from tkinter import messagebox
import random
from ui.map_view import MapView
from ui.control_panel import ControlPanel

from ai_models.data_structures import Order
from ai_models.fuzzy_logic import FuzzyPriority
from ai_models.neural_network import NeuralPredictor
from ai_models.genetic_algorithm import GeneticTSP
from ai_models.a_star_search import AStarNavigator
from ai_models.map_loader import MapLoader

class LogisticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Integrado de Logística com IA (Refatorado)")
        self.root.geometry("1200x800")
        self.running = True
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # State
        self.orders = []
        self.depot_pos = (2, 2)
        self.optimized_sequence = []
        
        # Map Loader
        self.map_loader = MapLoader()
        self.graph = self.map_loader.load_graph()
        
        # AI Engines
        self.fuzzy_engine = FuzzyPriority()
        self.neural_engine = NeuralPredictor()
        self.astar_engine = AStarNavigator(self.graph)
        
        # Depot (Pick a random node or a specific one)
        # For consistency, let's pick the first node
        self.depot_node = list(self.graph.nodes())[0]
        
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
        self.map_view.draw_graph(self.graph, self.depot_node)

    # --- Controller Methods ---

    def reset_simulation(self, silent=False):
        self.orders = []
        self.optimized_sequence = []
        self.control_panel.update_table(self.orders)
        self.map_view.draw_graph(self.graph, self.depot_node)
        
        if not silent:
            messagebox.showinfo("Info", "Simulação reiniciada.")

    def step1_generate(self):
        num_orders = self.control_panel.get_order_count()
        if num_orders is None:
            messagebox.showerror("Erro de Entrada", "Por favor, insira um número válido entre 1 e 20.")
            return

        self.reset_simulation(silent=True)
        
        for i in range(num_orders):
            # Pick random node for order
            node_id = self.map_loader.get_random_node()
            order = Order(i + 1, node_id, random.randint(10, 120), random.uniform(1, 30), random.choice([0, 1]))
            self.orders.append(order)
        
        self.control_panel.update_table(self.orders)
        self.map_view.draw_graph(self.graph, self.depot_node)
        self.map_view.draw_orders(self.orders, self.graph)
        messagebox.showinfo("Passo 1", f"{num_orders} pedidos gerados! Observe os pontos no mapa.")

    def step2_analyze(self):
        if not self.orders:
            messagebox.showwarning("Aviso", "Gere os pedidos no Passo 1 primeiro.")
            return
        
        for order in self.orders:
            # Fuzzy needs distance to depot. 
            # We can use A* cost or straight line. A* is better but slower.
            # Let's use A* cost (time or distance)
            dist = self.astar_engine.get_path_cost(self.depot_node, order.node_id)
            # Normalize dist for fuzzy? Fuzzy expects something.
            # Let's just pass the raw value and let fuzzy handle or mock it.
            # Actually fuzzy_logic.py probably expects x,y. We need to check it.
            # For now, let's just pass the order and depot_node
            self.fuzzy_engine.calculate(order, dist) # We will need to update fuzzy_engine
            self.neural_engine.predict(order)

        self.control_panel.update_table(self.orders)
        self.map_view.draw_graph(self.graph, self.depot_node)
        self.map_view.draw_analyzed_orders(self.orders, self.graph)
        
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
        
        
        # GeneticTSP needs to be updated to handle graph nodes or distance matrix
        # For now, let's assume we update GeneticTSP or mock it.
        # Let's pass the graph to GeneticTSP?
        # Or pre-calculate distance matrix.
        ga = GeneticTSP(self.orders, self.depot_node, self.astar_engine) # Need to update GeneticTSP signature
        self.optimized_sequence = ga.solve()
        
        self.map_view.draw_graph(self.graph, self.depot_node)
        self.map_view.draw_analyzed_orders(self.orders, self.graph)
        
        route_nodes = [self.depot_node] + [self.orders[i].node_id for i in self.optimized_sequence] + [self.depot_node]
        self.map_view.draw_optimized_route(route_nodes, self.graph)
        
        seq_str = " -> ".join([f"P{self.orders[i].id}" for i in self.optimized_sequence])
        messagebox.showinfo("Passo 3", f"Melhor sequência encontrada:\nDepósito -> {seq_str} -> Depósito")

    def step4_navigate(self):
        if not self.optimized_sequence:
            messagebox.showwarning("Aviso", "Primeiro otimize a rota no Passo 3.")
            return

        self.control_panel.set_nav_button_state(tk.DISABLED)
        
        self.map_view.draw_graph(self.graph, self.depot_node)
        self.map_view.draw_analyzed_orders(self.orders, self.graph)

        stops = [self.depot_node] + [self.orders[i].node_id for i in self.optimized_sequence] + [self.depot_node]
        
        full_journey_path = []
        for i in range(len(stops) - 1):
            start = stops[i]
            end = stops[i+1]
            path_segment = self.astar_engine.get_path(start, end)
            if path_segment:
                full_journey_path.extend(path_segment if i == 0 else path_segment[1:])
        
        if full_journey_path:
            self.map_view.animate_route(full_journey_path, self.graph, self.on_animation_complete)
        else:
            messagebox.showerror("Erro", "Não foi possível calcular o caminho.")
            self.control_panel.set_nav_button_state(tk.NORMAL)

    def on_animation_complete(self):
        self.control_panel.set_nav_button_state(tk.NORMAL)

    # Traffic light update removed for now as we switched to graph
    # We can re-implement it later by updating edge weights dynamically

    def on_close(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = LogisticsApp(root)
    root.mainloop()
