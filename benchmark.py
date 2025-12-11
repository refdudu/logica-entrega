"""
Benchmark Script - Automated Performance Testing

Compares Legacy vs Smart simulation modes across multiple scenarios.
Generates a detailed report file with results.
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.map_manager import MapManager
from src.core.simulator import Simulator
from src.utils.order_generator import generate_test_orders


def run_benchmark():
    """Execute comprehensive benchmark comparing Legacy vs Smart modes."""
    print("🚀 Iniciando Bateria de Testes Automatizados...")
    print("=" * 60)

    # Configuration
    test_cases =  list(range(2, 21))  # Number of orders per scenario
   
    map_seed = 123   # Fixed seed for obstacles (fair comparison)
    order_seed = 999  # Fixed seed for orders

    # Load map once (expensive operation)
    print("\n📍 Carregando mapa...")
    mm = MapManager()
    base_graph = mm.load_graph()

    # Prepare report
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("RELATÓRIO DE PERFORMANCE: LEGACY vs SMART")
    report_lines.append(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 60)
    report_lines.append("")

    results_summary = []

    for n_orders in test_cases:
        print(f"\n🧪 Executando cenário com {n_orders} pedidos...")

        # 1. Prepare terrain (always the same for fair comparison)
        graph = mm.enrich_map_with_obstacles(base_graph, seed=map_seed)
        orders_legacy = generate_test_orders(mm, n_orders, seed=order_seed)
        orders_smart = generate_test_orders(mm, n_orders, seed=order_seed)

        # Get depot node (first node in graph)
        depot_node = list(graph.nodes())[0]

        # 2. Run Legacy simulation
        print("   🔄 Executando simulação Legacy...")
        sim_legacy = Simulator(graph, orders_legacy, depot_node, mode="legacy")
        res_legacy = sim_legacy.run()

        # 3. Run Smart simulation
        print("   🤖 Executando simulação Smart...")
        sim_smart = Simulator(graph, orders_smart, depot_node, mode="smart")
        res_smart = sim_smart.run()

        # 4. Determine winner
        winner = "Smart"
        # Primary: Higher integrity wins
        if res_legacy['avg_integrity'] > res_smart['avg_integrity']:
            winner = "Legacy"
        elif res_legacy['avg_integrity'] == res_smart['avg_integrity']:
            # Tiebreaker: Lower time wins
            if res_legacy['time_total'] < res_smart['time_total']:
                winner = "Legacy"

        # 5. Format results
        block_text = (
            f"\n--- CENÁRIO: {n_orders} PEDIDOS ---\n"
            f"LEGACY -> Integridade: {res_legacy['avg_integrity']:.1f}% | "
            f"Tempo: {res_legacy['time_total']:.0f}min | "
            f"Distância: {res_legacy['distance_km']:.2f}km\n"
            f"SMART  -> Integridade: {res_smart['avg_integrity']:.1f}% | "
            f"Tempo: {res_smart['time_total']:.0f}min | "
            f"Distância: {res_smart['distance_km']:.2f}km\n"
            f"🏆 Vencedor: {winner}\n"
            f"-----------------------------------"
        )
        report_lines.append(block_text)
        
        results_summary.append({
            'orders': n_orders,
            'winner': winner,
            'legacy': res_legacy,
            'smart': res_smart
        })

        print(f"   ✅ Concluído (Vencedor: {winner})")

    # Generate summary statistics
    report_lines.append("\n\n" + "=" * 60)
    report_lines.append("RESUMO GERAL")
    report_lines.append("=" * 60)
    
    smart_wins = sum(1 for r in results_summary if r['winner'] == 'Smart')
    legacy_wins = len(results_summary) - smart_wins
    
    report_lines.append(f"Vitórias Smart:  {smart_wins}")
    report_lines.append(f"Vitórias Legacy: {legacy_wins}")
    report_lines.append(f"Taxa de sucesso Smart: {smart_wins/len(results_summary)*100:.0f}%")
    report_lines.append("\n" + "=" * 60)

    # Save report file
    filename = "resultado_testes.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"\n{'=' * 60}")
    print(f"📄 Relatório salvo com sucesso em: {os.path.abspath(filename)}")
    print(f"{'=' * 60}")
    
    # Print summary to console
    print(f"\n📊 RESUMO: Smart venceu {smart_wins}/{len(results_summary)} cenários ({smart_wins/len(results_summary)*100:.0f}%)")
    
    return results_summary


if __name__ == "__main__":
    run_benchmark()
