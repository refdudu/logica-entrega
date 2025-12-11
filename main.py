import tkinter as tk
from tkinter import messagebox
import random
import networkx as nx
import time
import threading
from typing import List, Optional, Dict
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
        
        # Enrich map with consistent obstacles for fair comparison
        self.graph = self.map_manager.enrich_map_with_obstacles(self.graph, seed=123)
        
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
            # Import Simulator here to avoid circular dependency
            from src.core.simulator import Simulator
            
            # --- 1. RUN LEGACY SIMULATION ---
            legacy_sim = Simulator(self.graph, self.orders, self.depot_node, mode="legacy")
            legacy_res = legacy_sim.run()
                
            # --- 2. RUN SMART SIMULATION ---
            smart_sim = Simulator(self.graph, self.orders, self.depot_node, mode="smart")
            smart_res = smart_sim.run()
            
            # Update UI from thread safely
            self.root.after(0, lambda: self.control_panel.update_table(self.orders))

            # --- 3. ANIMATE BOTH (on main thread) ---
            self.root.after(0, lambda: self._display_comparison_results(legacy_res, smart_res))
            
        except Exception as e:
            error_msg = f"Erro durante otimização: {str(e)}"
            self.root.after(0, lambda: messagebox.showerror("Erro", error_msg))
        finally:
            self.root.after(0, lambda: self.root.config(cursor=""))
    
    def _display_comparison_results(self, legacy_res: Dict, smart_res: Dict) -> None:
        """Display comparison results with integrity metrics."""
        results_str = (
            f"📍 LEGACY (Sem IA):\n"
            f"   Tempo Total: {legacy_res['time_total']:.0f} min\n"
            f"   Integridade Média: {legacy_res['avg_integrity']:.1f}%\n"
            f"   Distância: {legacy_res['distance_km']:.2f} km\n"
            f"   Pedidos: {legacy_res['orders_delivered']}\n\n"
            
            f"🧠 SMART (Com IA):\n"
            f"   Tempo Total: {smart_res['time_total']:.0f} min\n"
            f"   Integridade Média: {smart_res['avg_integrity']:.1f}%\n"
            f"   Distância: {smart_res['distance_km']:.2f} km\n"
            f"   Pedidos: {smart_res['orders_delivered']}\n\n"
            f"🏆 Veredito: "
        )
        
        # Determine winner based on integrity first, then time
        integrity_diff = smart_res['avg_integrity'] - legacy_res['avg_integrity']
        time_diff = legacy_res['time_total'] - smart_res['time_total']
        
        if integrity_diff > 10:
            results_str += f"Smart Venceu (Carga {integrity_diff:.1f}% mais intacta!)"
        elif integrity_diff < -10:
            results_str += f"Legacy Venceu (Carga {-integrity_diff:.1f}% mais intacta)"
        elif time_diff > 20:
            results_str += f"Smart Venceu ({time_diff:.0f} min mais rápido!)"
        elif time_diff < -20:
            results_str += f"Legacy Venceu ({-time_diff:.0f} min mais rápido)"
        else:
            results_str += "Empate Técnico"
        
        self.control_panel.update_results(results_str)


    # --- Support Methods ---

    def _calculate_legacy_path(self):
        """Calculate legacy path using simple Dijkstra (no heuristic, just avoids blocks)."""
        sorted_orders = sorted(self.orders, key=lambda x: x.deadline)
        stops = [self.depot_node] + [o.node_id for o in sorted_orders] + [self.depot_node]
        full_path_nodes = []

        for i in range(len(stops) - 1):
            start = stops[i]
            end = stops[i+1]
            try:
                # Define weight function that penalizes (but doesn't block) obstacles
                def legacy_weight(u, v, d):
                    """Legacy routing: avoids major obstacles but no AI optimization."""
                    base = d.get('length', 100)

                    # Road blocks: Heavily penalized (15x cost) but still navigable
                    # ✅ AUMENTAR: 15x (era 8x)
                    # Legacy DEVE evitar bloqueios para comparação justa
                    if d.get('road_block', False):
                        return base * 15.0

                    # Bad pavement: Small penalty (Legacy doesn't differentiate fragile cargo)
                    if d.get('pavement_quality') == 'bad':
                        return base * 1.3  # 30% more expensive

                    return base

                # Use Dijkstra (shortest_path) with weight function
                # No heuristic = still "dumb" compared to A*
                path = nx.shortest_path(self.graph, start, end, weight=legacy_weight)
                full_path_nodes.extend(path if i == 0 else path[1:])

            except nx.NetworkXNoPath:
                print(f"  [Legacy] No path found from {start} to {end}")
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
            self.fuzzy_engine.calculate(order, dist if dist != float('inf') else 5000)
            # Use fallback distance of 5000m if path is infinite/unreachable
            self.neural_engine.predict(order, dist if dist != float('inf') else 5000)
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
