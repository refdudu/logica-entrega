1. A Nova Lógica de Negócio
   Integridade da Carga: Cada pedido começa com 100% de "vida". Se um caminhão com carga frágil passa em "asfalto ruim", a integridade cai.

Penalidade de Tempo: Bloqueios na via não impedem a passagem, mas adicionam +2 horas de atraso (simulando trânsito/acidente).

2. Arquitetura Técnica Definida
   MapManager (O Criador de Mundos):

Responsável por injetar o caos (buracos e bloqueios) no grafo usando uma SEED fixa (ex: 123). Isso garante consistência.

Simulator (O Juiz Imparcial):

Recebe o mapa já pronto (Injeção de Dependência).

Não altera o mapa, apenas o percorre.

Simula passo a passo: Carregar -> Viajar (Calcula Dano/Tempo) -> Descarregar.

Truck (O Caminhão Inteligente):

Agora sabe o que está carregando (List[Order]), permitindo verificar se há itens frágeis a bordo no momento exato que passa num buraco.

3. O Fluxo de Comparação (O "Show")
   Cenário: O sistema gera um mapa onde o caminho mais curto (reta) está cheio de buracos e tem um bloqueio.

Execução Legacy: O algoritmo ingênuo escolhe a reta. Resultado: 10km percorridos, mas carga destruída (40% integridade) e 3 horas de atraso.

Execução Smart: O A\* percebe o custo alto dos obstáculos e faz um desvio. Resultado: 15km percorridos, mas carga intacta (100%) e chegada em 30 minutos.

Veredito: O painel mostra que eficiência não é só distância, e o Smart vence por entregar valor real.
