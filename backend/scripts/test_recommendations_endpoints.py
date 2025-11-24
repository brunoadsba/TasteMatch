"""
Script de teste automatizado para os endpoints de recomendações do TasteMatch.
Testa GET /api/recommendations e GET /api/recommendations/{restaurant_id}/insight.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Cores para o terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_status(status_char, message, color=Colors.OKBLUE, info=None):
    """Imprime uma mensagem de status formatada."""
    print(f"  {color}{status_char} {Colors.ENDC}{message}")
    if info:
        print(f"  {Colors.OKBLUE}ℹ️  {Colors.ENDC}{info}")

class RecommendationsEndpointTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []

    def _record_test_result(self, test_name, passed):
        self.test_results.append({"name": test_name, "passed": passed})

    def _run_test(self, test_name, func):
        print(f"{Colors.BOLD}🧪 {test_name}{Colors.ENDC}")
        try:
            func()
            self._record_test_result(test_name, True)
        except Exception as e:
            print_status("❌", f"Exceção durante {test_name.lower()}: {e}", Colors.FAIL)
            self._record_test_result(test_name, False)
        print()  # Linha em branco

    def test_server_health(self):
        """Testa o endpoint /health."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            health_data = response.json()
            if health_data.get("status") == "healthy":
                print_status("✅", f"Servidor respondendo: {health_data['status']}", Colors.OKGREEN,
                            f"Banco de dados: {health_data.get('database')}")
                return True
            else:
                print_status("❌", f"Servidor não está healthy: {health_data.get('status')}", Colors.FAIL)
                return False
        except requests.exceptions.ConnectionError:
            print_status("❌", "Não foi possível conectar ao servidor", Colors.FAIL)
            print_status("⚠️ ", "Certifique-se de que o servidor está rodando:", Colors.WARNING)
            print_status("⚠️ ", "   cd backend && python -m uvicorn app.main:app --reload", Colors.WARNING)
            return False
        except Exception as e:
            print_status("❌", f"Erro ao verificar saúde do servidor: {e}", Colors.FAIL)
            return False

    def test_authentication(self):
        """Autentica um usuário para obter token JWT."""
        # Primeiro, tentar fazer login com um usuário de exemplo
        login_data = {
            "email": "joao@example.com",
            "password": "senha_joao"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token")
                print_status("✅", f"Login bem-sucedido: {data['user']['email']}", Colors.OKGREEN,
                            f"Token recebido: {self.auth_token[:30]}...")
                return True
            else:
                # Tentar registrar novo usuário se login falhar
                print_status("⚠️ ", "Login falhou, tentando registrar novo usuário...", Colors.WARNING)
                register_data = {
                    "email": f"teste_recomm_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
                    "name": "Usuário Teste Recomendações",
                    "password": "senha_teste_123"
                }
                response = self.session.post(f"{self.base_url}/auth/register", json=register_data)
                if response.status_code == 201:
                    data = response.json()
                    self.auth_token = data.get("token")
                    print_status("✅", f"Usuário registrado: {data['user']['email']}", Colors.OKGREEN,
                                f"Token recebido: {self.auth_token[:30]}...")
                    return True
                else:
                    print_status("❌", f"Falha ao autenticar. Status: {response.status_code}, Resposta: {response.text}", Colors.FAIL)
                    return False
        except Exception as e:
            print_status("❌", f"Erro ao autenticar: {e}", Colors.FAIL)
            return False

    def test_get_recommendations(self):
        """Testa GET /api/recommendations."""
        if not self.auth_token:
            raise Exception("Token de autenticação não disponível")

        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Teste 1: Buscar recomendações padrão
        print_status("ℹ️ ", "Buscando recomendações (limit=5)...", Colors.OKBLUE)
        response = self.session.get(
            f"{self.base_url}/api/recommendations",
            headers=headers,
            params={"limit": 5}
        )
        
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get("recommendations", [])
            count = data.get("count", 0)
            
            print_status("✅", f"Recomendações recebidas: {count}", Colors.OKGREEN)
            
            if count > 0:
                print_status("ℹ️ ", f"Primeira recomendação: {recommendations[0].get('restaurant', {}).get('name', 'N/A')}", Colors.OKBLUE)
                if recommendations[0].get("insight"):
                    insight_preview = recommendations[0]["insight"][:100] + "..." if len(recommendations[0]["insight"]) > 100 else recommendations[0]["insight"]
                    print_status("ℹ️ ", f"Insight gerado: {insight_preview}", Colors.OKBLUE)
            else:
                print_status("⚠️ ", "Nenhuma recomendação retornada (usuário pode não ter histórico suficiente)", Colors.WARNING)
            
            return True
        else:
            print_status("❌", f"Falha ao buscar recomendações. Status: {response.status_code}, Resposta: {response.text}", Colors.FAIL)
            raise Exception(f"Status {response.status_code}: {response.text}")

    def test_get_recommendations_with_refresh(self):
        """Testa GET /api/recommendations com refresh=true."""
        if not self.auth_token:
            raise Exception("Token de autenticação não disponível")

        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        print_status("ℹ️ ", "Buscando recomendações com refresh=true...", Colors.OKBLUE)
        start_time = time.time()
        
        response = self.session.get(
            f"{self.base_url}/api/recommendations",
            headers=headers,
            params={"limit": 3, "refresh": True}
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            count = data.get("count", 0)
            print_status("✅", f"Recomendações recalculadas: {count} (tempo: {elapsed:.2f}s)", Colors.OKGREEN)
            return True
        else:
            print_status("❌", f"Falha ao buscar recomendações com refresh. Status: {response.status_code}", Colors.FAIL)
            raise Exception(f"Status {response.status_code}")

    def test_get_restaurant_insight(self):
        """Testa GET /api/recommendations/{restaurant_id}/insight."""
        if not self.auth_token:
            raise Exception("Token de autenticação não disponível")

        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Primeiro, obter uma lista de restaurantes para pegar um ID
        print_status("ℹ️ ", "Buscando restaurantes disponíveis...", Colors.OKBLUE)
        response = self.session.get(
            f"{self.base_url}/api/restaurants",
            headers=headers,
            params={"limit": 1}
        )
        
        if response.status_code == 200:
            restaurants = response.json()
            if restaurants and len(restaurants) > 0:
                restaurant_id = restaurants[0]["id"]
                
                print_status("ℹ️ ", f"Testando insight para restaurante ID {restaurant_id}...", Colors.OKBLUE)
                start_time = time.time()
                
                response = self.session.get(
                    f"{self.base_url}/api/recommendations/{restaurant_id}/insight",
                    headers=headers
                )
                
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    insight = data.get("insight", "")
                    
                    print_status("✅", f"Insight gerado com sucesso (tempo: {elapsed:.2f}s)", Colors.OKGREEN)
                    if insight:
                        insight_preview = insight[:150] + "..." if len(insight) > 150 else insight
                        print_status("ℹ️ ", f"Insight: {insight_preview}", Colors.OKBLUE)
                    return True
                else:
                    print_status("❌", f"Falha ao gerar insight. Status: {response.status_code}, Resposta: {response.text}", Colors.FAIL)
                    raise Exception(f"Status {response.status_code}")
            else:
                print_status("⚠️ ", "Nenhum restaurante encontrado para testar insight", Colors.WARNING)
                return False
        else:
            print_status("❌", f"Falha ao buscar restaurantes. Status: {response.status_code}", Colors.FAIL)
            raise Exception(f"Não foi possível obter restaurantes")

    def run_all_tests(self):
        """Executa todos os testes de recomendações."""
        print(f"\n{Colors.BOLD}{Colors.OKBLUE}============================================================{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKBLUE}       TESTES DE ENDPOINTS DE RECOMENDAÇÕES               {Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKBLUE}============================================================{Colors.ENDC}\n")

        server_ok = self.test_server_health()
        if not server_ok:
            self._record_test_result("Testando GET /api/recommendations", False)
            self._record_test_result("Testando GET /api/recommendations com refresh", False)
            self._record_test_result("Testando GET /api/recommendations/{id}/insight", False)
            self.display_summary()
            return

        # Autenticar antes de testar endpoints protegidos
        auth_ok = self.test_authentication()
        if not auth_ok:
            print_status("❌", "Não foi possível autenticar. Testes protegidos serão pulados.", Colors.FAIL)
            self._record_test_result("Testando GET /api/recommendations", False)
            self._record_test_result("Testando GET /api/recommendations com refresh", False)
            self._record_test_result("Testando GET /api/recommendations/{id}/insight", False)
            self.display_summary()
            return

        self._run_test("Testando GET /api/recommendations", self.test_get_recommendations)
        self._run_test("Testando GET /api/recommendations com refresh", self.test_get_recommendations_with_refresh)
        self._run_test("Testando GET /api/recommendations/{id}/insight", self.test_get_restaurant_insight)

        self.display_summary()

    def display_summary(self):
        """Exibe o resumo dos testes."""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t["passed"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"\n{Colors.BOLD}{Colors.OKBLUE}============================================================{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKBLUE}                     RESUMO DOS TESTES                      {Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKBLUE}============================================================{Colors.ENDC}\n")

        print(f"{Colors.BOLD}Total de testes: {total_tests}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✅ Passou: {passed_tests}{Colors.ENDC}")
        print(f"{Colors.FAIL}❌ Falhou: {failed_tests}{Colors.ENDC}\n")
        print(f"{Colors.BOLD}Taxa de sucesso: {success_rate:.1f}%{Colors.ENDC}\n")

        if failed_tests > 0:
            print(f"{Colors.BOLD}{Colors.FAIL}Testes que falharam:{Colors.ENDC}")
            for test in self.test_results:
                if not test["passed"]:
                    print(f"  {Colors.FAIL}❌ {test['name']}{Colors.ENDC}")

        print(f"\n{Colors.BOLD}{Colors.OKBLUE}============================================================{Colors.ENDC}\n")
        print(f"{Colors.OKBLUE}💡 Você também pode testar manualmente no Swagger:{Colors.ENDC}")
        print(f"{Colors.OKBLUE}   {self.base_url}/docs{Colors.ENDC}\n")

        if failed_tests > 0:
            sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Testa endpoints de recomendações do TasteMatch")
    parser.add_argument("--url", default="http://localhost:8000",
                       help="URL base da API (padrão: http://localhost:8000)")
    args = parser.parse_args()

    tester = RecommendationsEndpointTester(base_url=args.url)
    tester.run_all_tests()

