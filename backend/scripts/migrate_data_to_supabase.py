"""
Script para migrar dados do Fly.io Postgres para Supabase
"""
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Adicionar backend ao path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings

# Connection strings
# Fly.io - usar proxy local (localhost:5432) ou connection string direta
FLY_DB_URL = os.getenv(
    "FLY_DB_URL",
    "postgresql://postgres:E1bZuLmm1nEwx5k@localhost:5432/tastematch_api"
)

# Supabase - usar connection string direta (porta 5432)
# Nota: Senha precisa estar percent-encoded: #@Br88080187 -> %23%40Br88080187
# Formato: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
SUPABASE_URL = os.getenv(
    "SUPABASE_URL",
    "postgresql://postgres:%23%40Br88080187@db.efwdyzngrzpgbckrtgvx.supabase.co:5432/postgres?sslmode=require"
)


def get_table_columns(session, table_name):
    """Obtém lista de colunas de uma tabela"""
    inspector = inspect(session.bind)
    columns = inspector.get_columns(table_name)
    return [col['name'] for col in columns]


def escape_value(value):
    """Escapa valores para SQL"""
    if value is None:
        return 'NULL'
    elif isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    elif isinstance(value, (int, float)):
        return str(value)
    else:
        # Escapar aspas simples
        escaped = str(value).replace("'", "''")
        return f"'{escaped}'"


def migrate_table(table_name, source_session, target_session, batch_size=100):
    """Migra uma tabela do source para target"""
    print(f"\n🔄 Migrando tabela: {table_name}")
    
    try:
        # Contar registros
        count_result = source_session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count = count_result.scalar()
        print(f"   📊 Total de registros: {count}")
        
        if count == 0:
            print(f"   ⚠️  Tabela vazia, pulando...")
            return 0
        
        # Obter colunas
        source_columns = get_table_columns(source_session, table_name)
        target_columns = get_table_columns(target_session, table_name)
        
        # Intersecção de colunas (apenas colunas que existem em ambos)
        columns = [col for col in source_columns if col in target_columns]
        print(f"   📋 Colunas a migrar: {len(columns)}")
        
        # Limpar tabela destino (CUIDADO - apenas se não for alembic_version)
        if table_name != 'alembic_version':
            target_session.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
            target_session.commit()
            print(f"   🗑️  Tabela destino limpa")
        
        # Migrar em lotes
        offset = 0
        migrated = 0
        
        while offset < count:
            # Buscar lote
            columns_str = ', '.join(columns)
            query = f"SELECT {columns_str} FROM {table_name} ORDER BY id LIMIT {batch_size} OFFSET {offset}"
            rows = source_session.execute(text(query)).fetchall()
            
            if not rows:
                break
            
            # Inserir no destino usando COPY ou INSERT
            for row in rows:
                values = [escape_value(value) for value in row]
                values_str = ', '.join(values)
                columns_str_quoted = ', '.join([f'"{col}"' for col in columns])
                
                # Usar ON CONFLICT para evitar duplicatas
                insert_sql = f"""
                    INSERT INTO {table_name} ({columns_str_quoted}) 
                    VALUES ({values_str})
                    ON CONFLICT DO NOTHING
                """
                
                try:
                    target_session.execute(text(insert_sql))
                except Exception as e:
                    print(f"   ⚠️  Erro ao inserir registro: {e}")
                    # Continuar com próximo registro
                    continue
            
            target_session.commit()
            migrated += len(rows)
            offset += batch_size
            print(f"   ✅ Migrados {migrated}/{count} registros...")
        
        print(f"   ✅ Tabela {table_name} migrada com sucesso! ({migrated} registros)")
        return migrated
        
    except Exception as e:
        print(f"   ❌ Erro ao migrar {table_name}: {e}")
        target_session.rollback()
        raise


def main():
    """Função principal"""
    print("🚀 Iniciando migração de dados para Supabase...")
    print("=" * 60)
    
    # Verificar se connection strings estão configuradas
    if SUPABASE_URL == "postgresql://postgres:%23%40Br88080187@db.efwdyzngrzpgbckrtgvx.supabase.co:5432/postgres?sslmode=require":
        print("\n⚠️  Usando connection strings padrão.")
        print("   Se houver problemas de conexão, configure via variáveis de ambiente:")
        print("   export SUPABASE_URL='sua_connection_string_aqui'")
        print("   export FLY_DB_URL='sua_connection_string_aqui'")
        print()
    
    # Criar engines
    print("\n📡 Conectando aos bancos...")
    try:
        source_engine = create_engine(FLY_DB_URL, pool_pre_ping=True)
        # Forçar IPv4 e adicionar parâmetros SSL para Supabase
        target_engine = create_engine(
            SUPABASE_URL,
            pool_pre_ping=True,
            connect_args={
                "sslmode": "require",
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
            }
        )
        
        # Testar conexões
        with source_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("   ✅ Conexão com Fly.io OK")
        
        with target_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("   ✅ Conexão com Supabase OK")
        
    except Exception as e:
        print(f"   ❌ Erro ao conectar: {e}")
        return 1
    
    # Criar sessions
    SourceSession = sessionmaker(bind=source_engine)
    TargetSession = sessionmaker(bind=target_engine)
    
    source_session = SourceSession()
    target_session = TargetSession()
    
    # Ordem de migração (respeitando foreign keys)
    tables = [
        'users',
        'restaurants', 
        'orders',
        'recommendations',
        'user_preferences',
        'chat_messages',
        'llm_metrics',
        'alembic_version'
    ]
    
    total_migrated = 0
    
    try:
        for table in tables:
            try:
                migrated = migrate_table(table, source_session, target_session)
                total_migrated += migrated if migrated else 0
            except Exception as e:
                print(f"\n❌ Erro crítico ao migrar {table}: {e}")
                print("   Continuando com próxima tabela...")
                continue
        
        print("\n" + "=" * 60)
        print(f"✅ Migração completa! Total: {total_migrated} registros migrados")
        
        # Validar migração
        print("\n🔍 Validando migração...")
        for table in tables:
            if table == 'alembic_version':
                continue
            source_count = source_session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            target_count = target_session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            status = "✅" if source_count == target_count else "⚠️"
            print(f"   {status} {table}: {source_count} → {target_count}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Erro na migração: {e}")
        return 1
    finally:
        source_session.close()
        target_session.close()
        source_engine.dispose()
        target_engine.dispose()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

