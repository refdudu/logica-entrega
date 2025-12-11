import tkinter as tk
from tkinter import messagebox
import random
import networkx as nx
import time
import threading
from typing import List, Optional
from ui.map_view import MapView
from ui.control_panel import ControlPanel

from src.models.order import Order
from src.ai.fuzzy import FuzzyPriority
from src.ai.neural import NeuralPredictor
from src.ai.genetic import GeneticTSP
from src.ai.astar import AStarNavigator
from src.core.map_manager import MapManager

class LogisticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Integrado de Logística com IA (Santa Rosa - RS)")
        self.root.geometry("1400x900") # Larger window for side-by-side
        self.running = True
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # State
        self.orders = []
        self.depot_pos = (2, 2)
        self.optimized_sequence = []
        
        # Map Loader
        self.map_manager = MapManager()
        self.graph = self.map_manager.load_graph()
        
        # AI Engines
        self.fuzzy_engine = FuzzyPriority()
        self.neural_engine = NeuralPredictor()
        self.astar_engine = AStarNavigator(self.graph)
        
        # Depot (Pick the first node or specific if known)
        self.depot_node = list(self.graph.nodes())[0]
        
        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        # Control Panel (Left)
        self.control_panel = ControlPanel(self.root, self)
        self.control_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Right Side - Split directly into two Maps
        right_frame = tk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        
        # Legacy Map (Top or Left) - Let's do Side by Side inside Right Frame
        self.map_view_legacy = MapView(right_frame, self.root, title="Modo Legacy (Sem Otimização)")
        self.map_view_legacy.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=2)
        
        self.map_view_smart = MapView(right_frame, self.root, title="Modo Smart (AI)")
        self.map_view_smart.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH, padx=2)
        
        # Initial Draw
        self.map_view_legacy.draw_graph(self.graph, self.depot_node)
        self.map_view_smart.draw_graph(self.graph, self.depot_node)

    # --- Controller Methods ---

    def reset_simulation(self, silent=False):
        self.orders = []
        self.optimized_sequence = []
        self.control_panel.update_table(self.orders)
        self.map_view_legacy.draw_graph(self.graph, self.depot_node)
        self.map_view_smart.draw_graph(self.graph, self.depot_node)
        self.control_panel.update_results("")
        
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
            try:
                node_id = self.map_manager.get_random_node()
                # Deadline (10-120min), Weight (1-30kg), VIP (0/1)
                order = Order(i + 1, node_id, random.randint(10, 120), random.uniform(1, 30), random.choice([True, False]), random.choice([0, 1]))
                self.orders.append(order)
            except Exception as e:
                print(f"Error generating order: {e}")
        
        self.control_panel.update_table(self.orders)
        self.map_view_legacy.draw_graph(self.graph, self.depot_node)
        self.map_view_legacy.draw_orders(self.orders, self.graph)
        self.map_view_smart.draw_graph(self.graph, self.depot_node)
        self.map_view_smart.draw_orders(self.orders, self.graph)
        # messagebox.showinfo("Passo 1", f"{num_orders} pedidos gerados! Observe os pontos no mapa.")

    def run_full_comparison(self):
        """Run complete comparison between legacy and smart routing in a background thread."""
        # 0. Generate if no orders
        if not self.orders:
            self.step1_generate()
        
        if not self.orders:
            return

        # Run in background thread to avoid blocking UI
        thread = threading.Thread(target=self._run_comparison_thread, daemon=True)
        thread.start()
    
    def _run_comparison_thread(self) -> None:
        """Background thread for route optimization (avoids UI freeze)."""
        self.root.config(cursor="wait")
        self.control_panel.update_results("Calculando rotas...")
        
        try:
            # --- 1. RUN LEGACY CALCULATION ---
            legacy_path = self._calculate_legacy_path()
            legacy_dist = 0
            if legacy_path:
                legacy_dist = self._calculate_path_length(legacy_path)
                
            # --- 2. RUN SMART CALCULATION ---
            # Analyze orders
            for order in self.orders:
                dist = self.astar_engine.get_path_cost(
                    self.depot_node, order.node_id, is_fragile=False
                )
                self.fuzzy_engine.calculate(order, dist if dist != float('inf') else 5000)
                self.neural_engine.predict(order)
            
            # Update UI from thread safely
            self.root.after(0, lambda: self.control_panel.update_table(self.orders))
            self.root.after(0, lambda: self.map_view_smart.draw_analyzed_orders(self.orders, self.graph))

            # Optimize with progress callback
            def update_progress(current_gen: int, total_gens: int) -> None:
                progress_msg = f"Otimizando rotas... {current_gen}/{total_gens} gerações"
                self.root.after(0, lambda: self.control_panel.update_results(progress_msg))
            
            ga = GeneticTSP(
                self.orders, 
                self.depot_node, 
                self.astar_engine, 
                truck_capacity=30.0, 
                generations=20,
                progress_callback=update_progress
            )
            self.optimized_sequence = ga.solve()
            
            # Navigate
            smart_path = self._calculate_smart_path()
            smart_dist = 0
            if smart_path:
                smart_dist = self._calculate_smart_dist(smart_path)

            # --- 3. ANIMATE BOTH (on main thread) ---
            self.root.after(0, lambda: self._animate_comparison(
                legacy_path, legacy_dist, smart_path, smart_dist
            ))
            
        except Exception as e:
            error_msg = f"Erro durante otimização: {str(e)}"
            self.root.after(0, lambda: messagebox.showerror("Erro", error_msg))
        finally:
            self.root.after(0, lambda: self.root.config(cursor=""))
    
    def _animate_comparison(self, legacy_path: List[int], legacy_dist: float,
                           smart_path: List[int], smart_dist: float) -> None:
        """Animate both routes and display comparison results (must run on main thread)."""
        if legacy_path:
            self.map_view_legacy.animate_route(legacy_path, self.graph, None)
        else:
            messagebox.showwarning("Legacy", "Legacy falhou (sem rota).")
            
        if smart_path:
            self.map_view_smart.animate_route(smart_path, self.graph, None)
        else:
            messagebox.showwarning("Smart", "Smart falhou (sem rota).")
        
        # --- 4. SHOW RESULTS ---
        # Check if Legacy hit a block
        legacy_valid = True
        legacy_block_count = 0
        if legacy_path:
            for i in range(len(legacy_path)-1):
                u, v = legacy_path[i], legacy_path[i+1]
                d = self.graph.get_edge_data(u, v)[0]
                if d.get('road_block', False):
                    legacy_valid = False
                    legacy_block_count += 1

        legacy_status = f"{legacy_dist/1000:.2f} km"
        if not legacy_valid:
            legacy_status += f"\n   ❌ FALHOU: Atravessou {legacy_block_count} via(s) bloqueada(s)!"
        else:
            legacy_status += "\n   ✅ Sucesso (Sorte!)"

        results_str = (
            f"📍 LEGACY (Sem IA):\n"
            f"   Distância: {legacy_status}\n\n"
            f"🧠 SMART (Com IA):\n"
            f"   Distância: {smart_dist/1000:.2f} km\n"
            f"   ✅ Evitou bloqueios e trânsito\n\n"
            f"🏆 Veredito: "
        )
        
        if not legacy_valid:
            results_str += "Smart Venceu (Legacy bateu)!"
        elif legacy_dist > 0 and smart_dist > 0:
            if smart_dist < legacy_dist:
                results_str += "Smart Venceu (Menor Distância)!"
            else:
                results_str += "Smart foi mais cauteloso."
        
        self.control_panel.update_results(results_str)


    # --- Support Methods ---

    def _calculate_legacy_path(self):
        sorted_orders = sorted(self.orders, key=lambda x: x.deadline)
        stops = [self.depot_node] + [o.node_id for o in sorted_orders] + [self.depot_node]
        full_path_nodes = []
        for i in range(len(stops) - 1):
            start = stops[i]
            end = stops[i+1]
            try:
                # Naive shortest path (shortest distance), ignoring 'road_block' attribute
                path = nx.shortest_path(self.graph, start, end, weight='length')
                full_path_nodes.extend(path if i == 0 else path[1:])
            except nx.NetworkXNoPath:
                pass
        return full_path_nodes
    
    def _calculate_path_length(self, nodes):
        total_len = 0
        for i in range(len(nodes)-1):
            u, v = nodes[i], nodes[i+1]
            # Use simple length
            d = self.graph.get_edge_data(u, v)[0]
            total_len += d.get('length', 0)
        return total_len

    def _calculate_smart_path(self):
        stops = [self.depot_node] + [self.orders[i].node_id for i in self.optimized_sequence] + [self.depot_node]
        full_path = []
        for i in range(len(stops) - 1):
            start = stops[i]
            end = stops[i+1]
            is_fragile = False
            if i < len(self.optimized_sequence):
                 idx = self.optimized_sequence[i]
                 is_fragile = self.orders[idx].is_fragile
            
            path_segment = self.astar_engine.get_path(start, end, is_fragile=is_fragile)
            if path_segment:
                full_path.extend(path_segment if i == 0 else path_segment[1:])
        return full_path

    def _calculate_smart_dist(self, nodes):
        # Same util as legacy but maybe checks actual edge used
        return self._calculate_path_length(nodes) 
    
    # Keep old methods for "Individual" buttons if needed, wrapping new logic
    def run_legacy_simulation(self):
         path = self._calculate_legacy_path()
         if path:
             d = self._calculate_path_length(path)
             self.map_view_legacy.animate_route(path, self.graph, lambda: messagebox.showinfo("Legacy", f"Dist: {d/1000:.2f}km"))
    
    def run_smart_simulation(self):
        # Trigger Step 2, 3, 4 individually? Or just run logic
        # For simplicity, map to the button flow
        self.step2_analyze()
        self.step3_optimize()
        self.step4_navigate()

    def step2_analyze(self):
        # (Same logic as before, just updating Smart View)
        if not self.orders: return
        for order in self.orders:
            dist = self.astar_engine.get_path_cost(self.depot_node, order.node_id, is_fragile=False)
            self.fuzzy_engine.calculate(order, dist)
            self.neural_engine.predict(order)
        self.control_panel.update_table(self.orders)
        self.map_view_smart.draw_analyzed_orders(self.orders, self.graph)

    def step3_optimize(self):
        """Optimize delivery route using Genetic Algorithm (runs in background thread)."""
        if not self.orders:
            return
        
        thread = threading.Thread(target=self._optimize_thread, daemon=True)
        thread.start()
    
    def _optimize_thread(self) -> None:
        """Background thread for route optimization."""
        try:
            def update_progress(current_gen: int, total_gens: int) -> None:
                msg = f"Otimizando... {current_gen}/{total_gens} gerações"
                self.root.after(0, lambda: self.control_panel.update_results(msg))
            
            ga = GeneticTSP(
                self.orders, 
                self.depot_node, 
                self.astar_engine,
                progress_callback=update_progress
            )
            self.optimized_sequence = ga.solve()
            
            # Update UI on main thread
            self.root.after(0, self._update_optimized_route)
            
        except Exception as e:
            error_msg = f"Erro na otimização: {str(e)}"
            self.root.after(0, lambda: messagebox.showerror("Erro", error_msg))
    
    def _update_optimized_route(self) -> None:
        """Update UI with optimized route (must run on main thread)."""
        self.map_view_smart.draw_analyzed_orders(self.orders, self.graph)
        route_nodes = [self.depot_node] + \
                     [self.orders[i].node_id for i in self.optimized_sequence] + \
                     [self.depot_node]
        self.map_view_smart.draw_optimized_route(route_nodes, self.graph)
        self.control_panel.update_results("Otimização concluída!")
        
    def step4_navigate(self):
        path = self._calculate_smart_path()
        if path:
             d = self._calculate_smart_dist(path)
             self.map_view_smart.animate_route(path, self.graph, lambda: messagebox.showinfo("Smart", f"Dist: {d/1000:.2f}km"))

    def on_close(self):
        self.running = False
        self.root.destroy()
        import sys
        sys.exit(0)

if __name__ == "__main__":
    import sys
    root = tk.Tk()
    app = LogisticsApp(root)
    root.mainloop()
