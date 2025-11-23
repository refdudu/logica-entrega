import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import numpy as np
import ai_core

class LogisticsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Integrado de Logística com IA")
        self.root.geometry("1200x800")

        # Dados
        self.orders = []
        self.depot_pos = (2, 2)
        self.optimized_sequence = []
        
        # IAs
        self.fuzzy_engine = ai_core.FuzzyPriority()
        self.neural_engine = ai_core.NeuralPredictor()
        self.astar_engine = ai_core.AStarNavigator(grid_size=20)

        # Layout
        self.setup_ui()

    def setup_ui(self):
        # Painel Esquerdo (Controles e Lista)
        left_panel = tk.Frame(self.root, width=300, bg="#f0f0f0")
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        tk.Label(left_panel, text="Painel de Controle", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=10)

        # Botões do Pipeline
        btn_style = {"font": ("Arial", 10), "width": 25, "pady": 5}
        
        tk.Button(left_panel, text="1. Gerar Pedidos", command=self.step1_generate, **btn_style, bg="#add8e6").pack(pady=5)
        tk.Button(left_panel, text="2. Analisar (Fuzzy + RNA)", command=self.step2_analyze, **btn_style, bg="#90ee90").pack(pady=5)
        tk.Button(left_panel, text="3. Otimizar Rota (Genético)", command=self.step3_optimize, **btn_style, bg="#ffd700").pack(pady=5)
        tk.Button(left_panel, text="4. Navegar (A*)", command=self.step4_navigate, **btn_style, bg="#ffcccb").pack(pady=5)

        # Tabela de Pedidos
        self.tree = ttk.Treeview(left_panel, columns=('ID', 'Pri', 'Risco'), show='headings', height=20)
        self.tree.heading('ID', text='ID')
        self.tree.heading('Pri', text='Prioridade')
        self.tree.heading('Risco', text='Risco Atraso')
        self.tree.column('ID', width=40)
        self.tree.column('Pri', width=80)
        self.tree.column('Risco', width=100)
        self.tree.pack(pady=20, fill=tk.X)

        # Painel Direito (Visualização)
        right_panel = tk.Frame(self.root)
        right_panel.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.get_tk_widget().pack(expand=True, fill=tk.BOTH)
        
        # Desenha Grid inicial
        self.draw_grid()

    def draw_grid(self):
        self.ax.clear()
        self.ax.imshow(self.astar_engine.grid, cmap='Greys', origin='lower')
        # self.ax.plot(self.depot_pos[1], self.depot_pos[0], 'ks', markersize=12, label='Depósito') # k=black, s=square

        # Alteração no método draw_grid
        self.ax.plot(self.depot_pos[1], self.depot_pos[0], 
             marker='D',      # D = Diamond (Diamante)
             color='red',     # Cor VERMELHA
             markersize=18,   # Tamanho grande
             label='Depósito',
             zorder=10)

        self.ax.set_title("Mapa da Cidade")
        self.ax.grid(True, which='both', color='lightgray', linestyle='-', linewidth=0.5)
        self.canvas.draw()

    # --- PASSO 1: GERAÇÃO ---
    def step1_generate(self):
        self.orders = []
        for i in range(5): # Gera 5 pedidos
            # Posições aleatórias no grid 20x20
            x, y = random.randint(0, 19), random.randint(0, 19)
            # Dados aleatórios: Espera(0-120min), Peso(0.5-30kg), Chuva(0/1)
            order = ai_core.Order(i+1, x, y, random.randint(10, 120), random.uniform(1, 30), random.choice([0, 1]))
            self.orders.append(order)
        
        self.update_table()
        self.draw_orders()
        messagebox.showinfo("Passo 1", "Pedidos gerados! Observe os pontos no mapa.")

    def draw_orders(self):
        self.draw_grid()
        for o in self.orders:
            self.ax.plot(o.y, o.x, 'bo', markersize=8) # b=blue, o=circle
            self.ax.text(o.y+0.3, o.x+0.3, f"P{o.id}", color="blue")
        self.canvas.draw()

    def update_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for o in self.orders:
            self.tree.insert('', 'end', values=(o.id, f"{o.priority:.1f}", o.delay_risk))

    # --- PASSO 2: ANÁLISE (FUZZY + RNA) ---
    def step2_analyze(self):
        if not self.orders: return
        
        for order in self.orders:
            # 1. Fuzzy: Define prioridade baseado em local e tempo
            order = self.fuzzy_engine.calculate(order, self.depot_pos)
            
            # 2. Neural: Usa a prioridade Fuzzy + Peso + Chuva para prever atraso
            order = self.neural_engine.predict(order)

        self.update_table()
        
        # Redesenha com cores baseadas no Risco
        self.draw_grid()
        for o in self.orders:
            color = 'red' if o.delay_risk == "ALTO" else 'green'
            self.ax.plot(o.y, o.x, marker='o', color=color, markersize=10)
            self.ax.text(o.y+0.3, o.x+0.3, f"P{o.id}\nPri:{o.priority:.1f}", fontsize=8)
        self.canvas.draw()
        messagebox.showinfo("Passo 2", "Análise Completa!\nVermelho = Alto Risco de Atraso\nVerde = Baixo Risco")

    # --- PASSO 3: OTIMIZAÇÃO (GENÉTICO) ---
    def step3_optimize(self):
        if not self.orders: return
        
        ga = ai_core.GeneticTSP(self.orders, self.depot_pos)
        best_indices = ga.solve()
        self.optimized_sequence = best_indices
        
        # Desenha linhas retas (sequência lógica)
        self.step2_analyze() # Redesenha pontos
        
        # Desenha linhas aéreas da rota
        route_points = [self.depot_pos] + [(self.orders[i].x, self.orders[i].y) for i in best_indices] + [self.depot_pos]
        ys, xs = zip(*route_points)
        self.ax.plot(xs, ys, 'k--', alpha=0.5, label='Sequência Lógica')
        self.ax.legend()
        self.canvas.draw()
        
        seq_str = " -> ".join([f"P{self.orders[i].id}" for i in best_indices])
        messagebox.showinfo("Passo 3", f"Melhor sequência encontrada pelo Genético:\nDepósito -> {seq_str} -> Depósito")

    # --- PASSO 4: NAVEGAÇÃO (A*) ---
    def step4_navigate(self):
        if not self.optimized_sequence: return
        
        full_path_x = []
        full_path_y = []
        
        # Lista de coordenadas na ordem otimizada: Dep -> P1 -> P2... -> Dep
        stops = [self.depot_pos] + [(self.orders[i].x, self.orders[i].y) for i in self.optimized_sequence] + [self.depot_pos]
        
        for i in range(len(stops)-1):
            start = (int(stops[i][0]), int(stops[i][1]))
            end = (int(stops[i+1][0]), int(stops[i+1][1]))
            
            # Calcula rota física desviando de obstáculos
            path = self.astar_engine.get_path(start, end)
            
            if path:
                px, py = zip(*path)
                self.ax.plot(py, px, linewidth=2, color='blue') # Plota segmento
        
        self.ax.set_title("Rota Final Executável (A*)")
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = LogisticsApp(root)
    root.mainloop()