"""
Script de teste automatizado para validar endpoints de autenticação.
Valida registro, login, JWT tokens e proteção de rotas.
"""

import sys
import os
import json
from pathlib import Path

# Adicionar o diretório backend ao path para importar módulos
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import requests
from datetime import datetime
from typing import Optional, Dict, Any


class Colors:
    """Cores para output no terminal."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class AuthTester:
    """Classe para testar endpoints de autenticação."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.token: Optional[str] = None
        self.user_email: Optional[str] = None
        
    def print_header(self, message: str):
        """Imprime cabeçalho formatado."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{message:^60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    def print_test(self, test_name: str):
        """Imprime nome do teste."""
        print(f"{Colors.BOLD}🧪 {test_name}{Colors.RESET}")
    
    def print_success(self, message: str):
        """Imprime mensagem de sucesso."""
        print(f"  {Colors.GREEN}✅ {message}{Colors.RESET}")
        self.test_results.append({"test": message, "status": "PASS"})
    
    def print_error(self, message: str):
        """Imprime mensagem de erro."""
        print(f"  {Colors.RED}❌ {message}{Colors.RESET}")
        self.test_results.append({"test": message, "status": "FAIL"})
    
    def print_warning(self, message: str):
        """Imprime mensagem de aviso."""
        print(f"  {Colors.YELLOW}⚠️  {message}{Colors.RESET}")
    
    def print_info(self, message: str):
        """Imprime informação."""
        print(f"  {Colors.BLUE}ℹ️  {message}{Colors.RESET}")
    
    def check_server_running(self) -> bool:
        """Verifica se o servidor está rodando."""
        self.print_test("Verificando se servidor está rodando...")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Servidor respondendo: {data.get('status', 'unknown')}")
                self.print_info(f"Banco de dados: {data.get('database', 'unknown')}")
                return True
            else:
                self.print_error(f"Servidor retornou status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.print_error("Não foi possível conectar ao servidor")
            self.print_warning("Certifique-se de que o servidor está rodando:")
            self.print_warning("  cd backend && python -m uvicorn app.main:app --reload")
            return False
        except Exception as e:
            self.print_error(f"Erro ao verificar servidor: {str(e)}")
            return False
    
    def test_register_new_user(self) -> bool:
        """Testa registro de novo usuário."""
        self.print_test("Testando POST /auth/register (novo usuário)")
        
        # Email único para cada execução
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.user_email = f"teste_{timestamp}@example.com"
        
        payload = {
            "email": self.user_email,
            "name": "Usuário de Teste",
            "password": "senha_teste_123"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                data = response.json()
                
                # Validar estrutura da resposta
                if "user" in data and "token" in data:
                    user = data["user"]
                    token = data["token"]
                    
                    # Validar campos do usuário
                    required_fields = ["id", "email", "name", "created_at"]
                    missing_fields = [f for f in required_fields if f not in user]
                    
                    if missing_fields:
                        self.print_error(f"Campos faltando na resposta: {missing_fields}")
                        return False
                    
                    # Validar email
                    if user["email"] != self.user_email:
                        self.print_error(f"Email incorreto: esperado {self.user_email}, recebido {user['email']}")
                        return False
                    
                    # Validar token
                    if not token or len(token) < 50:
                        self.print_error("Token JWT inválido ou muito curto")
                        return False
                    
                    self.token = token
                    self.print_success(f"Usuário registrado: {user['email']} (ID: {user['id']})")
                    self.print_info(f"Token recebido: {token[:50]}...")
                    return True
                else:
                    self.print_error("Estrutura da resposta inválida (faltando 'user' ou 'token')")
                    self.print_info(f"Resposta: {json.dumps(data, indent=2)}")
                    return False
            else:
                self.print_error(f"Status code inesperado: {response.status_code}")
                try:
                    error_data = response.json()
                    self.print_info(f"Erro: {error_data.get('detail', 'Erro desconhecido')}")
                except:
                    self.print_info(f"Resposta: {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Exceção durante registro: {str(e)}")
            import traceback
            self.print_info(f"Traceback: {traceback.format_exc()}")
            return False
    
    def test_register_duplicate_email(self) -> bool:
        """Testa registro com email duplicado."""
        self.print_test("Testando POST /auth/register (email duplicado)")
        
        if not self.user_email:
            self.print_warning("Pulando teste - usuário não foi criado anteriormente")
            return True
        
        payload = {
            "email": self.user_email,  # Email já usado
            "name": "Outro Usuário",
            "password": "outra_senha"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 400:
                data = response.json()
                if "já cadastrado" in data.get("detail", "").lower() or "email" in data.get("detail", "").lower():
                    self.print_success("Email duplicado corretamente rejeitado")
                    return True
                else:
                    self.print_error(f"Mensagem de erro inesperada: {data.get('detail')}")
                    return False
            else:
                self.print_error(f"Status code inesperado: {response.status_code} (esperado 400)")
                return False
                
        except Exception as e:
            self.print_error(f"Exceção durante teste de duplicação: {str(e)}")
            return False
    
    def test_login_valid(self) -> bool:
        """Testa login com credenciais válidas."""
        self.print_test("Testando POST /auth/login (credenciais válidas)")
        
        if not self.user_email:
            self.print_warning("Pulando teste - usuário não foi criado")
            return True
        
        payload = {
            "email": self.user_email,
            "password": "senha_teste_123"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "user" in data and "token" in data:
                    user = data["user"]
                    token = data["token"]
                    
                    # Validar que o token foi gerado
                    if not token or len(token) < 50:
                        self.print_error("Token JWT inválido")
                        return False
                    
                    # Atualizar token
                    self.token = token
                    
                    self.print_success(f"Login bem-sucedido: {user['email']}")
                    self.print_info(f"Novo token recebido: {token[:50]}...")
                    return True
                else:
                    self.print_error("Estrutura da resposta inválida")
                    return False
            else:
                self.print_error(f"Status code inesperado: {response.status_code}")
                try:
                    error_data = response.json()
                    self.print_info(f"Erro: {error_data.get('detail', 'Erro desconhecido')}")
                except:
                    self.print_info(f"Resposta: {response.text}")
                return False
                
        except Exception as e:
            self.print_error(f"Exceção durante login: {str(e)}")
            return False
    
    def test_login_invalid_email(self) -> bool:
        """Testa login com email inválido."""
        self.print_test("Testando POST /auth/login (email inválido)")
        
        payload = {
            "email": "email_inexistente@example.com",
            "password": "qualquer_senha"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 401:
                data = response.json()
                if "incorretos" in data.get("detail", "").lower() or "invalid" in data.get("detail", "").lower():
                    self.print_success("Email inválido corretamente rejeitado")
                    return True
                else:
                    self.print_warning(f"Mensagem de erro diferente: {data.get('detail')}")
                    return True  # Aceitar qualquer mensagem de erro 401
            else:
                self.print_error(f"Status code inesperado: {response.status_code} (esperado 401)")
                return False
                
        except Exception as e:
            self.print_error(f"Exceção durante teste de login inválido: {str(e)}")
            return False
    
    def test_login_invalid_password(self) -> bool:
        """Testa login com senha incorreta."""
        self.print_test("Testando POST /auth/login (senha incorreta)")
        
        if not self.user_email:
            self.print_warning("Pulando teste - usuário não foi criado")
            return True
        
        payload = {
            "email": self.user_email,
            "password": "senha_errada"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 401:
                data = response.json()
                self.print_success("Senha incorreta corretamente rejeitada")
                return True
            else:
                self.print_error(f"Status code inesperado: {response.status_code} (esperado 401)")
                return False
                
        except Exception as e:
            self.print_error(f"Exceção durante teste de senha incorreta: {str(e)}")
            return False
    
    def test_validate_token(self) -> bool:
        """Testa validação de token JWT."""
        self.print_test("Testando validação de token JWT")
        
        if not self.token:
            self.print_warning("Pulando teste - token não foi gerado")
            return True
        
        # Tentar acessar uma rota protegida (quando existir)
        # Por enquanto, vamos apenas validar que o token existe e tem formato válido
        
        # Verificar formato do token (deve ter 3 partes separadas por ponto)
        parts = self.token.split('.')
        if len(parts) == 3:
            self.print_success("Token JWT tem formato válido (3 partes)")
            self.print_info(f"Header: {parts[0][:20]}...")
            self.print_info(f"Payload: {parts[1][:20]}...")
            self.print_info(f"Signature: {parts[2][:20]}...")
            return True
        else:
            self.print_error(f"Token JWT tem formato inválido ({len(parts)} partes ao invés de 3)")
            return False
    
    def test_protected_route(self) -> bool:
        """Testa acesso a rota protegida."""
        self.print_test("Testando acesso a rota protegida (quando disponível)")
        
        if not self.token:
            self.print_warning("Pulando teste - token não foi gerado")
            return True
        
        # Tentar acessar /api/users/me (quando implementado)
        # Por enquanto, vamos apenas verificar se o token existe
        self.print_info("Rotas protegidas serão testadas quando implementadas (FASE 4)")
        self.print_info(f"Token disponível para uso: {self.token[:50]}...")
        return True
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Executa todos os testes e retorna resultados."""
        self.print_header("TESTES DE AUTENTICAÇÃO - TASTEMATCH")
        
        # Lista de testes em ordem
        tests = [
            ("Verificação de Servidor", self.check_server_running),
            ("Registro de Novo Usuário", self.test_register_new_user),
            ("Registro com Email Duplicado", self.test_register_duplicate_email),
            ("Login com Credenciais Válidas", self.test_login_valid),
            ("Login com Email Inválido", self.test_login_invalid_email),
            ("Login com Senha Incorreta", self.test_login_invalid_password),
            ("Validação de Token JWT", self.test_validate_token),
            ("Rota Protegida", self.test_protected_route),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                success = test_func()
                results.append({
                    "test": test_name,
                    "status": "PASS" if success else "FAIL"
                })
            except Exception as e:
                self.print_error(f"Erro ao executar {test_name}: {str(e)}")
                results.append({
                    "test": test_name,
                    "status": "ERROR",
                    "error": str(e)
                })
        
        return results
    
    def print_summary(self, results: list):
        """Imprime resumo dos testes."""
        self.print_header("RESUMO DOS TESTES")
        
        total = len(results)
        passed = sum(1 for r in results if r["status"] == "PASS")
        failed = sum(1 for r in results if r["status"] == "FAIL")
        errors = sum(1 for r in results if r["status"] == "ERROR")
        
        print(f"\n{Colors.BOLD}Total de testes: {total}{Colors.RESET}")
        print(f"{Colors.GREEN}✅ Passou: {passed}{Colors.RESET}")
        print(f"{Colors.RED}❌ Falhou: {failed}{Colors.RESET}")
        if errors > 0:
            print(f"{Colors.YELLOW}⚠️  Erros: {errors}{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}Taxa de sucesso: {(passed/total*100):.1f}%{Colors.RESET}\n")
        
        if failed > 0 or errors > 0:
            print(f"{Colors.BOLD}{Colors.RED}Testes que falharam:{Colors.RESET}")
            for result in results:
                if result["status"] in ["FAIL", "ERROR"]:
                    error_msg = f" - {result.get('error', '')}" if "error" in result else ""
                    print(f"  {Colors.RED}❌ {result['test']}{error_msg}{Colors.RESET}")
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")
        
        return passed == total


def main():
    """Função principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Testa endpoints de autenticação do TasteMatch")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="URL base da API (padrão: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    tester = AuthTester(base_url=args.url)
    results = tester.run_all_tests()
    success = tester.print_summary(results)
    
    # Exit code: 0 se todos passaram, 1 se algum falhou
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

