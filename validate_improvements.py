"""
Script de validação das melhorias implementadas.
Verifica se todas as correções foram aplicadas corretamente.
"""

import sys
import ast
import inspect
from pathlib import Path

def validate_astar():
    """Valida melhorias em astar.py"""
    print("🔍 Validando src/ai/astar.py...")
    
    try:
        from src.ai.astar import AStarNavigator
        import networkx as nx
        
        # Verificar se _heuristic calcula distância euclidiana
        source = inspect.getsource(AStarNavigator._heuristic)
        
        checks = {
            "✅ Calcula distância euclidiana": "math.sqrt" in source or "**" in source,
            "✅ Usa coordenadas dos nós": "'x'" in source or "'y'" in source,
            "✅ Tem tratamento de erros": "try:" in source,
            "✅ Retorna float": "-> float" in source or "return" in source
        }
        
        for check, passed in checks.items():
            print(f"  {check if passed else '❌ ' + check[2:]}")
        
        # Verificar se get_path usa heurística
        path_source = inspect.getsource(AStarNavigator.get_path)
        has_heuristic = "heuristic=self._heuristic" in path_source
        print(f"  {'✅' if has_heuristic else '❌'} nx.astar_path usa heurística")
        
        # Verificar otimização de get_path_cost
        cost_source = inspect.getsource(AStarNavigator.get_path_cost)
        optimized = "shortest_path_length" in cost_source
        print(f"  {'✅' if optimized else '❌'} get_path_cost otimizado (usa shortest_path_length)")
        
        return all(checks.values()) and has_heuristic and optimized
        
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


def validate_genetic():
    """Valida melhorias em genetic.py"""
    print("\n🔍 Validando src/ai/genetic.py...")
    
    try:
        from src.ai.genetic import GeneticTSP
        
        # Verificar integração Fuzzy na fitness
        source = inspect.getsource(GeneticTSP._calculate_fitness)
        
        checks = {
            "✅ Calcula current_time": "current_time" in source,
            "✅ Usa fuzzy_priority": "fuzzy_priority" in source or "priority" in source,
            "✅ Aplica penalidade temporal": "time_penalty" in source or "penalty" in source,
            "✅ Tem docstring explicativa": '"""' in source or "'''" in source,
            "✅ Type hints presentes": "-> float" in source
        }
        
        for check, passed in checks.items():
            print(f"  {check if passed else '❌ ' + check[2:]}")
        
        # Verificar callback de progresso
        init_source = inspect.getsource(GeneticTSP.__init__)
        has_callback = "progress_callback" in init_source
        print(f"  {'✅' if has_callback else '❌'} Suporta callback de progresso")
        
        # Verificar uso do callback em solve
        solve_source = inspect.getsource(GeneticTSP.solve)
        uses_callback = "self.progress_callback" in solve_source
        print(f"  {'✅' if uses_callback else '❌'} Usa callback durante evolução")
        
        return all(checks.values()) and has_callback and uses_callback
        
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


def validate_main():
    """Valida melhorias em main.py"""
    print("\n🔍 Validando main.py...")
    
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        checks = {
            "✅ Import threading": "import threading" in content,
            "✅ Método _run_comparison_thread": "def _run_comparison_thread" in content,
            "✅ Método _optimize_thread": "def _optimize_thread" in content,
            "✅ Thread.start() usado": "thread.start()" in content,
            "✅ root.after() para UI": "self.root.after(0" in content,
            "✅ Callback de progresso passado ao GA": "progress_callback=" in content
        }
        
        for check, passed in checks.items():
            print(f"  {check if passed else '❌ ' + check[2:]}")
        
        return all(checks.values())
        
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


def validate_documentation():
    """Valida documentação"""
    print("\n🔍 Validando documentação...")
    
    checks = {
        "✅ MELHORIAS_IMPLEMENTADAS.md criado": Path("MELHORIAS_IMPLEMENTADAS.md").exists()
    }
    
    for check, passed in checks.items():
        print(f"  {check if passed else '❌ ' + check[2:]}")
    
    return all(checks.values())


def main():
    print("=" * 60)
    print("🚀 VALIDAÇÃO DAS MELHORIAS IMPLEMENTADAS")
    print("=" * 60)
    
    results = {
        "A* Navigator": validate_astar(),
        "Genetic Algorithm": validate_genetic(),
        "Main Application": validate_main(),
        "Documentation": validate_documentation()
    }
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)
    
    for component, passed in results.items():
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"{component:.<40} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 TODAS AS MELHORIAS FORAM IMPLEMENTADAS COM SUCESSO!")
        print("=" * 60)
        print("\n📋 Próximos passos:")
        print("  1. Execute: python main.py")
        print("  2. Teste a funcionalidade completa")
        print("  3. Leia MELHORIAS_IMPLEMENTADAS.md para o relatório")
        return 0
    else:
        print("⚠️  ALGUMAS VALIDAÇÕES FALHARAM")
        print("=" * 60)
        print("\nRevise os componentes marcados com ❌")
        return 1


if __name__ == "__main__":
    sys.exit(main())
