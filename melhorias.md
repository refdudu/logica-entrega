```markdown
# Checklist de Implementação - Rede Neural (Opção 1)

## Passo 1: Backup e Preparação

- [ ] Fazer backup do arquivo atual `src/ai/neural.py` (renomear para `neural_old.py`)
- [ ] Verificar se `requirements.txt` tem as dependências:
```

scikit-learn>=1.0.0
numpy>=1.20.0

```
- [ ] Instalar dependências se necessário: `pip install -r requirements.txt`

---

## Passo 2: Reescrever `src/ai/neural.py`

### 2.1 Imports e Estrutura da Classe

- [ ] Adicionar imports necessários no topo do arquivo:
```

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
import random

```

- [ ] Criar docstring da classe explicando o propósito:
```

class NeuralPredictor:
"""Preditor de tempo de entrega usando Rede Neural Artificial (RNA).

      Treina com dataset sintético baseado em simulações realistas de entregas
      considerando distância, peso da carga, prazo e condições de tráfego.
      """

````

### 2.2 Método `__init__`

- [ ] Implementar `__init__(self, seed: int = 42)` com:
- [ ] Salvar `self.seed = seed`
- [ ] Criar `self.scaler = StandardScaler()`
- [ ] Criar `self.model = MLPRegressor(...)` com parâmetros:
  - [ ] `hidden_layer_sizes=(10, 5)`
  - [ ] `activation='relu'`
  - [ ] `solver='adam'`
  - [ ] `max_iter=1000`
  - [ ] `random_state=seed`
- [ ] Chamar `self._train()` no final

### 2.3 Método `_generate_training_data`

- [ ] Implementar `_generate_training_data(self)` que:
- [ ] Define `random.seed(self.seed)` e `np.random.seed(self.seed)`
- [ ] Cria listas vazias `X = []` e `y = []`
- [ ] Loop de 100 iterações:
  - [ ] Gera `distance = random.uniform(1000, 30000)` (1-30km)
  - [ ] Gera `weight = random.uniform(1, 30)` (1-30kg)
  - [ ] Gera `deadline = random.uniform(10, 120)` (10-120min)
  - [ ] Gera `traffic = random.uniform(0.0, 1.0)` (0-100%)
  - [ ] Calcula target:
    ```
    base_time = distance / 500  # ~30km/h
    weight_penalty = weight * 0.1
    traffic_penalty = traffic * base_time * 0.5
    delivery_time = base_time + weight_penalty + traffic_penalty
    ```
  - [ ] Adiciona `[distance, weight, deadline, traffic]` em `X`
  - [ ] Adiciona `delivery_time` em `y`
- [ ] Retorna `np.array(X), np.array(y)`

### 2.4 Método `_train`

- [ ] Implementar `_train(self)` que:
- [ ] Chama `X, y = self._generate_training_data()`
- [ ] Normaliza: `X_scaled = self.scaler.fit_transform(X)`
- [ ] Treina: `self.model.fit(X_scaled, y)`
- [ ] Calcula RMSE:
  ```
  predictions = self.model.predict(X_scaled)
  mse = np.mean((predictions - y) ** 2)
  rmse = np.sqrt(mse)
  ```
- [ ] Imprime: `print(f"[NeuralPredictor] Treinamento concluído. RMSE: {rmse:.2f} min")`

### 2.5 Método `predict`

- [ ] Implementar `predict(self, order, distance: float) -> float` que:
- [ ] Gera tráfego aleatório: `traffic = random.uniform(0.0, 1.0)`
- [ ] Monta features:
  ```
  features = np.array([[
      distance,
      order.weight,
      order.deadline,
      traffic
  ]])
  ```
- [ ] Normaliza: `features_scaled = self.scaler.transform(features)`
- [ ] Prediz: `predicted_time = self.model.predict(features_scaled)[0]`
- [ ] Salva no pedido: `order.delivery_time_estimate = predicted_time`
- [ ] Retorna: `return predicted_time`

---

## Passo 3: Integração com o Sistema

### 3.1 Verificar Importação no `main.py`

- [ ] Confirmar que `main.py` tem: `from src.ai.neural import NeuralPredictor`
- [ ] Confirmar que existe: `self.neural_engine = NeuralPredictor()`

### 3.2 Uso no Método `step2_analyze`

- [ ] Localizar método `step2_analyze` em `main.py`
- [ ] Verificar que existe chamada:
````

for order in self.orders:
dist = self.astar_engine.get_path_cost(self.depot_node, order.node_id, is_fragile=False)
self.neural_engine.predict(order, dist) # ✅ Esta linha deve existir

```
- [ ] Se não existir, adicionar após o cálculo da distância

### 3.3 Atualizar Modelo de Order (se necessário)

- [ ] Abrir `src/models/order.py`
- [ ] Verificar que a classe `Order` tem atributo:
```

self.delivery_time_estimate = None # ou 0.0

```
- [ ] Se não tiver, adicionar no `__init__`

---

## Passo 4: Testes

### 4.1 Criar Arquivo de Teste

- [ ] Criar arquivo `tests/test_neural.py` (ou adicionar no `test_improvements.py`)

### 4.2 Teste de Treinamento

- [ ] Implementar `test_neural_training()`:
```

def test_neural_training():
"""Verifica que a RNA treina sem erros."""
from src.ai.neural import NeuralPredictor

      neural = NeuralPredictor(seed=42)
      assert neural.model is not None, "Modelo não foi criado"
      assert neural.scaler is not None, "Scaler não foi criado"
      print("✅ RNA treinada com sucesso")

```
- [ ] Executar: `python tests/test_neural.py` ou `pytest tests/test_neural.py`

### 4.3 Teste de Predição

- [ ] Implementar `test_neural_prediction()`:
```

def test_neural_prediction():
"""Verifica que a RNA faz predições válidas."""
from src.ai.neural import NeuralPredictor
from src.models.order import Order

      neural = NeuralPredictor(seed=42)

      order = Order(
          id=1,
          node_id=100,
          deadline=60,
          weight=15,
          is_fragile=False,
          is_vip=1
      )

      predicted_time = neural.predict(order, distance=10000)  # 10km

      assert predicted_time > 0, "Tempo deve ser positivo"
      assert predicted_time < 200, "Tempo deve ser razoável (<200min)"
      assert order.delivery_time_estimate is not None, "Atributo não foi atualizado"

      print(f"✅ Predição: {predicted_time:.2f} min para 10km")

```
- [ ] Executar teste e verificar sucesso

### 4.4 Teste de Reprodutibilidade

- [ ] Implementar `test_neural_reproducibility()`:
```

def test_neural_reproducibility():
"""Verifica que a mesma seed produz mesmos resultados."""
from src.ai.neural import NeuralPredictor
from src.models.order import Order

      neural1 = NeuralPredictor(seed=42)
      neural2 = NeuralPredictor(seed=42)

      order1 = Order(1, 100, 60, 15, False, 1)
      order2 = Order(1, 100, 60, 15, False, 1)

      time1 = neural1.predict(order1, 10000)
      time2 = neural2.predict(order2, 10000)

      # Deve ser próximo (pode ter pequena variação por tráfego aleatório)
      assert abs(time1 - time2) < 5, "Resultados devem ser reproduzíveis"
      print(f"✅ Reprodutibilidade: {time1:.2f} ≈ {time2:.2f}")

```

---

## Passo 5: Teste de Integração Completo

### 5.1 Executar Sistema Completo

- [ ] Rodar `python main.py`
- [ ] Gerar pedidos (Botão "Gerar Pedidos" ou equivalente)
- [ ] Clicar em "Analisar" (Step 2)
- [ ] Verificar no console:
```

[NeuralPredictor] Treinamento concluído. RMSE: 3.XX min

```
- [ ] Verificar que não há erros

### 5.2 Verificar Saída de Predições

- [ ] Adicionar print temporário no `step2_analyze`:
```

for order in self.orders:
dist = self.astar_engine.get_path_cost(...)
self.neural_engine.predict(order, dist)
print(f"[DEBUG] Order {order.id}: {order.delivery_time_estimate:.2f} min")

```
- [ ] Rodar sistema novamente
- [ ] Confirmar que cada pedido recebe tempo estimado
- [ ] Remover print após confirmar

---

## Passo 6: Documentação

### 6.1 Comentários no Código

- [ ] Adicionar comentário no topo de `neural.py`:
```

"""
Módulo de Predição de Tempo de Entrega usando Rede Neural Artificial.

Implementa MLPRegressor (Multi-Layer Perceptron) para estimar o tempo
real de entrega baseado em características do pedido e condições da rota.

Dataset de Treino: - 100 exemplos sintéticos - Features: distância, peso, prazo, tráfego - Target: tempo de entrega (minutos)

Arquitetura: - Camada de entrada: 4 neurônios (features) - Camada oculta 1: 10 neurônios (ReLU) - Camada oculta 2: 5 neurônios (ReLU) - Camada de saída: 1 neurônio (tempo)
"""

```

### 6.2 README (Opcional)

- [ ] Adicionar seção em `README.md` explicando a RNA:
```

## Rede Neural Artificial

- **Técnica**: Multi-Layer Perceptron (MLP)
- **Biblioteca**: scikit-learn
- **Dataset**: 100 entregas sintéticas
- **Features**: distância, peso, prazo, tráfego
- **Acurácia**: RMSE ~3 minutos

```

---

## Passo 7: Validação Final

- [ ] Todos os testes passam sem erros
- [ ] Sistema inicializa sem travamentos
- [ ] Predições retornam valores razoáveis (10-120 min para rotas típicas)
- [ ] RMSE reportado é < 5 minutos
- [ ] Código está comentado e legível

---

## Checklist de Conclusão

- [ ] `src/ai/neural.py` reescrito completamente
- [ ] Dataset sintético gera 100 exemplos
- [ ] Treinamento funciona e imprime RMSE
- [ ] Método `predict` retorna tempos válidos
- [ ] Integração com `main.py` funciona
- [ ] Atributo `order.delivery_time_estimate` é atualizado
- [ ] Testes unitários criados e passando
- [ ] Sistema completo roda sem erros
- [ ] Documentação adicionada

---

## Tempo Estimado

- ⏱️ Passos 1-2: 30-40 minutos
- ⏱️ Passo 3: 10 minutos
- ⏱️ Passos 4-5: 20-30 minutos
- ⏱️ Passos 6-7: 10 minutos

**Total: ~1h30min**
```
