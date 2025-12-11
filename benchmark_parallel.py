"""
Benchmark Script - PARALLEL VERSION (Safe & Optimized)

Compares Legacy vs Smart simulation modes using multiprocessing.
Uses 50-75% of CPU cores to prevent system freeze.
"""

import os
import sys
from datetime import datetime
from multiprocessing import Pool, cpu_count
from functools import partial

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.map_manager import MapManager
from src.core.simulator import Simulator
from src.utils.order_generator import generate_test_orders


def run_single_scenario(n_orders, map_seed, order_seed):
    """Execute a single benchmark scenario (runs in separate process).
    
    Args:
        n_orders: Number of orders in this scenario
        map_seed: Random seed for map obstacles
        order_seed: Random seed for order generation
        
    Returns:
        Dictionary with scenario results
    """
    print(f"   🔄 Processando cenário com {n_orders} pedidos...")
    
    # Load map (each process loads independently)
    mm = MapManager()
    base_graph = mm.load_graph()
    graph = mm.enrich_map_with_obstacles(base_graph, seed=map_seed)
    
    # Generate orders
    orders_legacy = generate_test_orders(mm, n_orders, seed=order_seed)
    orders_smart = generate_test_orders(mm, n_orders, seed=order_seed)
    
    depot_node = list(graph.nodes())[0]
    
    # Run simulations
    sim_legacy = Simulator(graph, orders_legacy, depot_node, mode="legacy")
    res_legacy = sim_legacy.run()
    
    sim_smart = Simulator(graph, orders_smart, depot_node, mode="smart")
    res_smart = sim_smart.run()
    
    # Determine winner
    winner = "Smart"
    if res_legacy['avg_integrity'] > res_smart['avg_integrity']:
        winner = "Legacy"
    elif res_legacy['avg_integrity'] == res_smart['avg_integrity']:
        if res_legacy['time_total'] < res_smart['time_total']:
            winner = "Legacy"
    
    print(f"   ✅ Concluído: {n_orders} pedidos (Vencedor: {winner})")
    
    return {
        'orders': n_orders,
        'winner': winner,
        'legacy': res_legacy,
        'smart': res_smart
    }


def run_benchmark_parallel():
    """Execute benchmark using multiprocessing for speed."""
    print("🚀 Iniciando Bateria de Testes Automatizados (PARALELO)")
    print("=" * 60)
    
    # Configuration
    test_cases = list(range(5, 21))  # 2 to 20 orders
    map_seed = 123
    order_seed = 999
    
    # ✅ FIX 1: Safe CPU core detection
    n_cores = cpu_count()
    if n_cores is None or n_cores < 1:
        n_cores = 2  # Fallback to 2 cores
    
    # ✅ FIX 2: Use only 50-75% of cores to prevent system freeze
    # This leaves resources for OS and other processes
    n_workers = max(1, int(n_cores * 0.6))  # Use 60% of cores
    
    print(f"💻 Detectados {n_cores} núcleos de CPU")
    print(f"⚙️  Usando {n_workers} workers (para não travar o sistema)")
    print(f"🧪 Executando {len(test_cases)} cenários em paralelo...\n")
    
    # ✅ FIX 3: Use context manager properly
    try:
        with Pool(processes=n_workers) as pool:
            # Create partial function with fixed seeds
            run_scenario = partial(run_single_scenario, 
                                  map_seed=map_seed, 
                                  order_seed=order_seed)
            
            # Map scenarios to pool (returns results in order)
            results_summary = pool.map(run_scenario, test_cases)
        
        print(f"\n✅ Todos os cenários concluídos!\n")
        
    except Exception as e:
        print(f"\n❌ Erro durante execução paralela: {e}")
        print("💡 Tente executar o benchmark.py normal se o erro persistir")
        return None
    
    # Generate report
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("RELATÓRIO DE PERFORMANCE: LEGACY vs SMART")
    report_lines.append(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 60)
    report_lines.append("")
    
    for result in results_summary:
        block_text = (
            f"\n--- CENÁRIO: {result['orders']} PEDIDOS ---\n"
            f"LEGACY -> Integridade: {result['legacy']['avg_integrity']:.1f}% | "
            f"Tempo: {result['legacy']['time_total']:.0f}min | "
            f"Distância: {result['legacy']['distance_km']:.2f}km\n"
            f"SMART  -> Integridade: {result['smart']['avg_integrity']:.1f}% | "
            f"Tempo: {result['smart']['time_total']:.0f}min | "
            f"Distância: {result['smart']['distance_km']:.2f}km\n"
            f"🏆 Vencedor: {result['winner']}\n"
            f"-----------------------------------"
        )
        report_lines.append(block_text)
    
    # Summary statistics
    report_lines.append("\n\n" + "=" * 60)
    report_lines.append("RESUMO GERAL")
    report_lines.append("=" * 60)
    
    smart_wins = sum(1 for r in results_summary if r['winner'] == 'Smart')
    legacy_wins = len(results_summary) - smart_wins
    
    report_lines.append(f"Vitórias Smart:  {smart_wins}")
    report_lines.append(f"Vitórias Legacy: {legacy_wins}")
    report_lines.append(f"Taxa de sucesso Smart: {smart_wins/len(results_summary)*100:.0f}%")
    report_lines.append("\n" + "=" * 60)
    
    # Save report
    filename = "resultado_testes.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    
    print(f"{'=' * 60}")
    print(f"📄 Relatório salvo em: {os.path.abspath(filename)}")
    print(f"{'=' * 60}")
    print(f"\n📊 RESUMO: Smart venceu {smart_wins}/{len(results_summary)} cenários ({smart_wins/len(results_summary)*100:.0f}%)")
    
    return results_summary


if __name__ == "__main__":
    # ✅ FIX 4: Windows multiprocessing protection
    # Required on Windows to prevent infinite process spawning
    from multiprocessing import freeze_support
    freeze_support()
    
    run_benchmark_parallel()
