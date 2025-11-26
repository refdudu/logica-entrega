# Relatório Técnico: Sistema Integrado de Logística com IA

## 1. Introdução e Definição do Problema

O presente trabalho aborda o problema da **otimização de logística de entrega "last-mile"**, um desafio comum e de grande impacto para empresas que trabalham com distribuição de produtos. O objetivo é desenvolver um sistema inteligente capaz de gerenciar um conjunto de pedidos, desde a sua priorização até a definição da rota física de entrega, de forma eficiente e automatizada.

A solução visa:
- **Reduzir custos operacionais** ao encontrar as rotas mais curtas.
- **Aumentar a satisfação do cliente** ao priorizar entregas mais urgentes.
- **Gerenciar riscos** ao prever potenciais atrasos com base nas condições do pedido.

Para atingir esses objetivos, o sistema integra quatro técnicas de Inteligência Artificial em um pipeline lógico e visual.

## 2. Arquitetura do Software

Após um processo de refatoração, o código foi organizado de forma modular para separar as responsabilidades, seguindo boas práticas de engenharia de software:

- **`main.py`**: Ponto de entrada da aplicação. Contém a classe principal `LogisticsApp`, que atua como o **controlador (Controller)**, orquestrando a interação entre a interface do usuário e os modelos de IA.

- **`ui/`**: Pasta que contém os componentes da **visão (View)**.
    - `control_panel.py`: Define o painel de controle esquerdo, com todos os botões e interações do usuário.
    - `map_view.py`: Define o painel direito, responsável por toda a renderização e animação do mapa.

- **`ai_models/`**: Pasta que contém os modelos de **IA (Model)**. Cada arquivo representa uma técnica específica, tornando o sistema modular e fácil de estender.
    - `data_structures.py`: Define a estrutura de dados `Order`.
    - `fuzzy_logic.py`: Implementação da Lógica Fuzzy.
    - `neural_network.py`: Implementação da Rede Neural.
    - `genetic_algorithm.py`: Implementação do Algoritmo Genético.
    - `a_star_search.py`: Implementação do algoritmo de busca A*.

## 3. O Pipeline de Inteligência Artificial

O sistema opera em um pipeline de 4 passos, onde o resultado de uma etapa serve de entrada para a seguinte.

### Passo 1: Geração de Pedidos
Nesta etapa, o cenário do problema é criado, com pedidos sendo distribuídos aleatoriamente no mapa.

### Passo 2: Análise de Prioridade e Risco

Aqui, duas técnicas de IA analisam cada pedido individualmente.

#### **Técnica 1: Lógica Fuzzy (`FuzzyPriority`)**
- **Objetivo:** Definir um nível de **prioridade** numérico para cada entrega, simulando o "bom senso" humano.
- **Entradas (Antecedentes):** `Tempo de Espera` do cliente e `Distância` da entrega ao depósito.
- **Regras:** O sistema utiliza regras linguísticas como: "**SE** o tempo de espera for `longo` **OU** a distância for `perta`, **ENTÃO** a prioridade é `alta`."
- **Saída:** Um valor de prioridade de 0 a 10, que é exibido na interface e utilizado na próxima etapa.

#### **Técnica 2: Rede Neural Artificial (`NeuralPredictor`)**
- **Objetivo:** **Prever o risco de atraso** da entrega, classificando-o como `ALTO` ou `BAIXO`.
- **Entradas (Features):** Para cada pedido, a rede analisa: o `Peso` do pacote, a `Condição de Chuva` (0 ou 1) e a **`Prioridade` calculada pela Lógica Fuzzy**. A integração entre as técnicas é um ponto-chave aqui.
- **Saída:** Uma classificação de risco, que é usada para colorir os pedidos no mapa (vermelho para alto risco, verde para baixo risco), fornecendo um feedback visual imediato.
- **Observação:** Atualmente, a rede é treinada com dados simulados ("mock") para fins de demonstração.

### Passo 3: Otimização da Rota (Sequenciamento)

#### **Técnica 3: Algoritmo Genético (`GeneticTSP`)**
- **Objetivo:** Encontrar a **sequência de entregas mais eficiente**, resolvendo o Problema do Caixeiro Viajante (TSP).
- **Funcionamento:** O algoritmo cria uma "população" de rotas aleatórias e as evolui ao longo de várias "gerações".
    - A **Função de Fitness** avalia cada rota calculando sua distância total. Rotas mais curtas são consideradas "mais aptas".
    - Através de **Seleção**, **Cruzamento** (crossover) e **Mutação**, as rotas mais promissoras geram "descendentes" cada vez melhores.
- **Saída:** A melhor sequência de entregas encontrada (a rota lógica), que minimiza a distância total percorrida.

### Passo 4: Navegação no Mapa (Caminho Físico)

#### **Técnica 4: Algoritmo A\* (`AStarNavigator`)**
- **Objetivo:** Traçar o **caminho físico real** no mapa entre cada parada da rota otimizada, desviando de obstáculos (prédios/bloqueios).
- **Funcionamento:** O A\* é um algoritmo de busca de caminho inteligente. Ele explora o mapa a partir de um ponto inicial, utilizando uma **heurística** (no nosso caso, a "distância de Manhattan") para estimar o quão promissor é cada próximo passo em direção ao destino. Isso o torna muito mais eficiente do que uma busca por força bruta.
- **Saída:** Uma lista de coordenadas que representa o caminho exato a ser seguido, que é então desenhado de forma animada na interface.

## 4. Como Executar a Aplicação

1.  **Instalar as dependências:**
    ```bash
    pip install numpy scikit-learn scikit-fuzzy matplotlib
    ```

2.  **Executar o programa:**
    ```bash
    python main.py
    ```

## 5. Conclusão

Este projeto demonstra com sucesso a aplicação de quatro técnicas distintas de Inteligência Artificial para resolver um problema complexo e relevante do mundo real. A integração das técnicas em um pipeline, onde a saída de uma alimenta a outra, cria uma solução robusta e multifacetada, indo desde a análise estratégica de pedidos até o planejamento tático de rotas. A interface visual e a organização do código facilitam a compreensão, a análise dos resultados e a demonstração prática do poder da IA na otimização de processos logísticos.
