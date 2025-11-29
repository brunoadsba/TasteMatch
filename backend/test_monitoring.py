"""
Script de teste para verificar se o monitoramento LLM está funcionando.
Simula uma chamada ao Chef Virtual e verifica se as métricas são coletadas.
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório do backend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.base import get_db
from app.core.rag_service import RAGService
from app.core.chef_chat import get_chef_response
from app.core.llm_monitoring import get_llm_metrics_summary
from app.database import crud
from app.config import settings
from sqlalchemy import text


def test_chef_virtual_monitoring():
    """Testa o monitoramento do Chef Virtual."""
    
    print("=" * 60)
    print("TESTE DE MONITORAMENTO LLM - CHEF VIRTUAL")
    print("=" * 60)
    print()
    
    # 1. Verificar estado inicial
    print("1️⃣ Verificando estado inicial das métricas...")
    db = next(get_db())
    try:
        result = db.execute(text('SELECT COUNT(*) FROM llm_metrics'))
        initial_count = result.scalar()
        print(f"   ✅ Registros iniciais: {initial_count}")
    except Exception as e:
        print(f"   ❌ Erro ao verificar métricas iniciais: {e}")
        return False
    finally:
        db.close()
    
    print()
    
    # 2. Fazer uma chamada ao Chef Virtual
    print("2️⃣ Fazendo chamada ao Chef Virtual...")
    print("   Pergunta: 'Quero uma pizza'")
    
    db = next(get_db())
    try:
        # Inicializar RAG Service (precisa de db e connection_string)
        connection_string = settings.DATABASE_URL
        rag_service = RAGService(db=db, connection_string=connection_string)
        
        # Inicializar vector store se necessário
        try:
            rag_service.initialize_vector_store()
        except Exception as e:
            print(f"   ⚠️ Aviso ao inicializar vector store: {e}")
            print("   Continuando mesmo assim...")
        
        # Fazer chamada (sem user_id para teste simples)
        print("   ⏳ Aguardando resposta do LLM...")
        response = get_chef_response(
            question="Quero uma pizza",
            rag_service=rag_service,
            user_id=None,  # Teste sem usuário
            db=db  # Passar db para salvar métricas
        )
        
        print(f"   ✅ Resposta recebida: {response['answer'][:100]}...")
        print(f"   ✅ Validação: {response['validation']}")
        
    except Exception as e:
        print(f"   ❌ Erro ao fazer chamada: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    print()
    
    # 3. Verificar se métricas foram coletadas
    print("3️⃣ Verificando se métricas foram coletadas...")
    db = next(get_db())
    try:
        # Contar métricas após a chamada
        result = db.execute(text('SELECT COUNT(*) FROM llm_metrics'))
        final_count = result.scalar()
        
        if final_count > initial_count:
            print(f"   ✅ Métricas coletadas! ({initial_count} → {final_count})")
            
            # Buscar última métrica
            result = db.execute(text("""
                SELECT 
                    id, model, input_tokens, output_tokens, total_tokens,
                    latency_ms, estimated_cost_usd, response_length, error, created_at
                FROM llm_metrics 
                ORDER BY created_at DESC 
                LIMIT 1
            """))
            metric = result.fetchone()
            
            if metric:
                print()
                print("   📊 Última métrica coletada:")
                print(f"      - ID: {metric[0]}")
                print(f"      - Modelo: {metric[1]}")
                print(f"      - Tokens (input/output/total): {metric[2]}/{metric[3]}/{metric[4]}")
                print(f"      - Latência: {metric[5]}ms")
                print(f"      - Custo estimado: ${metric[6]:.6f} USD")
                print(f"      - Tamanho da resposta: {metric[7]} caracteres")
                print(f"      - Erro: {metric[8] or 'Nenhum'}")
                print(f"      - Data: {metric[9]}")
        else:
            print(f"   ⚠️ Nenhuma nova métrica coletada ({initial_count} → {final_count})")
            print("   Verifique se o monitoramento está integrado corretamente.")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro ao verificar métricas: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    print()
    
    # 4. Testar função de resumo
    print("4️⃣ Testando função de resumo de métricas...")
    db = next(get_db())
    try:
        summary = get_llm_metrics_summary(db, user_id=None, days=7)
        print(f"   ✅ Resumo dos últimos 7 dias:")
        print(f"      - Total de chamadas: {summary['total_calls']}")
        print(f"      - Total de tokens: {summary['total_tokens']}")
        print(f"      - Custo total: ${summary['total_cost_usd']:.6f} USD")
        print(f"      - Latência média: {summary['avg_latency_ms']}ms")
        print(f"      - Taxa de erro: {summary['error_rate']}%")
    except Exception as e:
        print(f"   ❌ Erro ao obter resumo: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    print()
    print("=" * 60)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("=" * 60)
    print()
    print("📝 Próximos passos:")
    print("   1. Verificar logs estruturados no console")
    print("   2. Testar endpoint /api/llm/summary")
    print("   3. Fazer mais chamadas para acumular métricas")
    
    return True


if __name__ == "__main__":
    success = test_chef_virtual_monitoring()
    sys.exit(0 if success else 1)

