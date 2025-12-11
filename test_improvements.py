"""
Script de teste rápido para validar as melhorias implementadas.
"""

import sys
from pathlib import Path

def test_imports():
    """Testa se todos os módulos podem ser importados."""
    print("🔍 Testando imports...")
    
    try:
        from src.models.order import Order
        from src.models.truck import Truck
        from src.core.map_manager import MapManager
        from src.core.simulator import Simulator
        from src.ai.astar import AStarNavigator
        from src.ai.fuzzy import FuzzyPriority
        from src.ai.genetic import GeneticTSP
        print("  ✅ Todos os imports funcionando")
        return True
    except Exception as e:
        print(f"  ❌ Erro nos imports: {e}")
        return False


def test_order_integrity():
    """Testa se Order tem atributo current_integrity."""
    print("\n🔍 Testando Order.current_integrity...")
    
    try:
        from src.models.order import Order
        
        order = Order(
            id=1, 
            node_id=123, 
            deadline=60, 
            weight=5.0, 
            is_fragile=True, 
            priority_class=1
        )
        
        assert hasattr(order, 'current_integrity'), "Atributo current_integrity não existe"
        assert order.current_integrity == 100.0, "Integridade inicial deve ser 100%"
        assert hasattr(order, 'delivered'), "Atributo delivered não existe"
        
        # Testar dano
        order.current_integrity -= 10
        assert order.current_integrity == 90.0, "Dano não foi aplicado corretamente"
        
        print("  ✅ Order com current_integrity funcionando")
        return True
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


def test_truck_cargo():
    """Testa se Truck gerencia lista de Orders."""
    print("\n🔍 Testando Truck.cargo...")
    
    try:
        from src.models.truck import Truck
        from src.models.order import Order
        
        truck = Truck(capacity=30.0)
        
        # Verificar propriedade current_load
        assert hasattr(truck, 'current_load'), "Propriedade current_load não existe"
        assert truck.current_load == 0.0, "Carga inicial deve ser 0"
        
        # Verificar cargo
        assert hasattr(truck, 'cargo'), "Atributo cargo não existe"
        assert isinstance(truck.cargo, list), "Cargo deve ser uma lista"
        
        # Testar load_order
        order = Order(1, 123, 60, 5.0, True, 1)
        success = truck.load_order(order)
        assert success, "load_order deve retornar True"
        assert len(truck.cargo) == 1, "Cargo deve ter 1 pedido"
        assert truck.current_load == 5.0, "Carga deve ser 5.0 kg"
        
        # Testar get_fragile_cargo
        fragile = truck.get_fragile_cargo()
        assert len(fragile) == 1, "Deve ter 1 item frágil"
        
        # Testar unload_all
        truck.unload_all()
        assert len(truck.cargo) == 0, "Cargo deve estar vazio"
        assert truck.current_load == 0.0, "Carga deve ser 0"
        
        print("  ✅ Truck.cargo funcionando corretamente")
        return True
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


def test_map_enrich():
    """Testa se MapManager tem enrich_map_with_obstacles."""
    print("\n🔍 Testando MapManager.enrich_map_with_obstacles...")
    
    try:
        from src.core.map_manager import MapManager
        import networkx as nx
        
        # Criar grafo simples para teste
        G = nx.MultiDiGraph()
        G.add_edge(1, 2, length=100, maxspeed=50)
        G.add_edge(2, 3, length=200, maxspeed=40)
        
        manager = MapManager()
        
        # Verificar se método existe
        assert hasattr(manager, 'enrich_map_with_obstacles'), \
            "Método enrich_map_with_obstacles não existe"
        
        # Testar enriquecimento
        enriched = manager.enrich_map_with_obstacles(G, seed=42)
        
        # Verificar se atributos foram adicionados
        for u, v, k, data in enriched.edges(keys=True, data=True):
            assert 'pavement_quality' in data, "pavement_quality não foi adicionado"
            assert 'road_block' in data, "road_block não foi adicionado"
        
        print("  ✅ enrich_map_with_obstacles funcionando")
        return True
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


def test_simulator_structure():
    """Testa estrutura do novo Simulator."""
    print("\n🔍 Testando estrutura do Simulator...")
    
    try:
        from src.core.simulator import Simulator
        import inspect
        
        # Verificar assinatura do __init__
        sig = inspect.signature(Simulator.__init__)
        params = list(sig.parameters.keys())
        
        assert 'graph' in params, "Parâmetro 'graph' não existe no __init__"
        assert 'orders' in params, "Parâmetro 'orders' não existe no __init__"
        assert 'depot_node' in params, "Parâmetro 'depot_node' não existe no __init__"
        assert 'mode' in params, "Parâmetro 'mode' não existe no __init__"
        
        # Verificar métodos
        assert hasattr(Simulator, '_traverse_path'), "Método _traverse_path não existe"
        assert hasattr(Simulator, '_execute_delivery_route'), "Método _execute_delivery_route não existe"
        
        print("  ✅ Simulator com estrutura correta")
        return True
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


def main():
    """Executa todos os testes."""
    print("=" * 60)
    print("🚀 TESTE DAS MELHORIAS IMPLEMENTADAS")
    print("=" * 60)
    
    results = {
        "Imports": test_imports(),
        "Order.current_integrity": test_order_integrity(),
        "Truck.cargo": test_truck_cargo(),
        "MapManager.enrich_map_with_obstacles": test_map_enrich(),
        "Simulator Structure": test_simulator_structure()
    }
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)
    
    for component, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{component:.<45} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("=" * 60)
        print("\n📋 Próximos passos:")
        print("  1. Execute: python main.py")
        print("  2. Clique em 'Gerar Pedidos'")
        print("  3. Clique em 'Comparação Completa'")
        print("  4. Observe a nova métrica de 'Integridade Média'")
        print("\n📄 Documentação completa: IMPLEMENTACAO_COMPLETA.md")
        return 0
    else:
        print("⚠️ ALGUNS TESTES FALHARAM")
        print("=" * 60)
        print("\nRevise os componentes marcados com ❌")
        return 1


if __name__ == "__main__":
    sys.exit(main())
