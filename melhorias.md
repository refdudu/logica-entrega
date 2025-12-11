### 1\. Ajuste no A\* (De "Muro" para "Lama")

Em vez de dizer que é _impossível_ (`inf`) passar no buraco (o que quebra a lógica se for o único caminho), vamos dizer que é **extremamente custoso**. Assim, o caminhão só passa lá se for a _única_ opção absoluta.

**Arquivo:** `src/ai/astar.py`
**Alteração:** Troque o `float('inf')` por uma penalidade massiva (ex: 5000x).

```python
# Na função weight_function ou _calculate_weight

# ... check road_block ...

# Pavement Quality & Fragility
pavement_penalty = 1.0
if d.get('pavement_quality') == 'bad':
    if is_fragile:
        # ANTES: return float('inf')
        # DEPOIS: Penalidade gigante, mas navegável se for a única opção
        pavement_penalty = 5000.0
    else:
        pavement_penalty = 1.4
```

_Isso garante que o A_ sempre retorne um caminho válido, evitando comportamentos imprevisíveis do simulador.\*

---

### 2\. A Correção Crítica no Genético (`genetic.py`)

Essa é a mudança que vai fazer o Smart vencer de lavada. Vamos ensinar o Genético a entender que **fragilidade acumula**. Se ele pegou um item frágil no começo, o resto da rota inteira precisa ser feita com cuidado (e portanto, custará mais caro).

Isso vai forçar o Genético a organizar as entregas para pegar os itens frágeis **por último** (Last In, First Out logic), minimizando o tempo de exposição ao risco.

**Arquivo:** `src/ai/genetic.py`
**Substitua o método `_calculate_fitness` por este:**

```python
    def _calculate_fitness(self, individual: List[int]) -> float:
        total_cost = 0.0
        current_node = self.depot_node
        current_load = 0.0

        # Variável para rastrear se TEMOS algo frágil no caminhão agora
        has_fragile_cargo = False

        for order_index in individual:
            order = self.orders[order_index]

            # 1. Capacidade (Lógica existente)
            if current_load + order.weight > self.truck_capacity:
                # Volta pro depósito (com o estado atual de fragilidade)
                cost_to_depot = self.astar_engine.get_path_cost(current_node, self.depot_node, is_fragile=has_fragile_cargo)
                total_cost += cost_to_depot
                current_node = self.depot_node
                current_load = 0.0
                has_fragile_cargo = False # Descarregou tudo

            # 2. Custo da viagem até o pedido
            # O pulo do gato: A viagem é frágil se o pedido NOVO é frágil OU se já temos algo frágil
            trip_is_fragile = order.is_fragile or has_fragile_cargo

            cost = self.astar_engine.get_path_cost(current_node, order.node_id, is_fragile=trip_is_fragile)

            # Se o custo for muito alto (penalidade do A*), o Genético vai punir essa rota
            total_cost += cost

            # 3. Atualiza estado do caminhão
            current_node = order.node_id
            current_load += order.weight

            # Se pegamos um frágil, o caminhão fica "infectado" com fragilidade até voltar ao depósito
            if order.is_fragile:
                has_fragile_cargo = True

        # Retorno final ao depósito
        total_cost += self.astar_engine.get_path_cost(current_node, self.depot_node, is_fragile=has_fragile_cargo)

        return 1.0 / (total_cost + 1e-6)
```

---

### 3\. Ajuste Fino no Mapa (MapManager)

Como você quer consistência nos testes, vamos reduzir a probabilidade de "caos total" para evitar que pedidos nasçam em ilhas isoladas por bloqueios.

**Arquivo:** `src/core/map_manager.py`

```python
# No método enrich_map_with_obstacles
# Reduza um pouco para garantir conectividade
if random.random() < 0.08: # 8% de ruas ruins (era 10-20%)
    data['pavement_quality'] = 'bad'

if random.random() < 0.01: # 1% de bloqueios (Mantenha baixo)
    data['road_block'] = True
```
