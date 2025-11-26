import tkinter as tk
from tkinter import ttk

class ControlPanel(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f0f0f0")
        self.controller = controller

        tk.Label(self, text="Painel de Controle", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=10)

        # Frame de Geração de Pedidos
        generation_frame = tk.Frame(self, bg="#f0f0f0")
        generation_frame.pack(pady=5, fill=tk.X)
        tk.Label(generation_frame, text="Número de Pedidos:", font=("Arial", 10), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        self.order_count_input = tk.Spinbox(generation_frame, from_=1, to=20, width=5, font=("Arial", 10))
        self.order_count_input.delete(0, "end")
        self.order_count_input.insert(0, "5")
        self.order_count_input.pack(side=tk.LEFT, padx=5)

        # Botões do Pipeline
        btn_style = {"font": ("Arial", 10), "width": 25, "pady": 5}
        
        tk.Button(self, text="1. Gerar Pedidos", command=self.controller.step1_generate, **btn_style, bg="#add8e6").pack(pady=5)
        tk.Button(self, text="2. Analisar (Fuzzy + RNA)", command=self.controller.step2_analyze, **btn_style, bg="#90ee90").pack(pady=5)
        tk.Button(self, text="3. Otimizar Rota (Genético)", command=self.controller.step3_optimize, **btn_style, bg="#ffd700").pack(pady=5)
        
        self.nav_button = tk.Button(self, text="4. Navegar (A*)", command=self.controller.step4_navigate, **btn_style, bg="#ffcccb")
        self.nav_button.pack(pady=5)

        tk.Frame(self, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, padx=5, pady=10)
        tk.Button(self, text="Limpar Simulação", command=self.controller.reset_simulation, **btn_style, bg="#D3D3D3").pack(pady=5)
        tk.Frame(self, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, padx=5, pady=10)

        # Tabela de Pedidos
        self.tree = ttk.Treeview(self, columns=('ID', 'Pri', 'Risco'), show='headings', height=15)
        self.tree.heading('ID', text='ID')
        self.tree.heading('Pri', text='Prioridade')
        self.tree.heading('Risco', text='Risco Atraso')
        self.tree.column('ID', width=40)
        self.tree.column('Pri', width=80)
        self.tree.column('Risco', width=100)
        self.tree.pack(pady=20, fill=tk.X)

    def get_order_count(self):
        try:
            num_orders = int(self.order_count_input.get())
            if not (1 <= num_orders <= 20):
                raise ValueError("Número de pedidos fora do intervalo (1-20).")
            return num_orders
        except (ValueError, tk.TclError):
            return None # Retorna None se a entrada for inválida

    def update_table(self, orders):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for o in orders:
            self.tree.insert('', 'end', values=(o.id, f"{o.priority:.1f}", o.delay_risk))

    def set_nav_button_state(self, state):
        self.nav_button.config(state=state)
