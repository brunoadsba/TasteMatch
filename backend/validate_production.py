#!/usr/bin/env python3
"""
Script de Validação de Endpoints em Produção
TasteMatch API - Fase 12
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Optional, Tuple
from urllib.parse import urljoin

# Configuração
API_BASE_URL = "https://tastematch-api.fly.dev"
TIMEOUT = 30

# Cores para output (ANSI)
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class ValidationResult:
    """Armazena resultado de uma validação."""
    def __init__(self, name: str, success: bool, message: str = "", data: Dict = None):
        self.name = name
        self.success = success
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.utcnow().isoformat()

    def __str__(self):
        status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if self.success else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        return f"{status} {self.name}: {self.message}"


class ProductionValidator:
    """Validador de endpoints em produção."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.results: list[ValidationResult] = []
        self.auth_token: Optional[str] = None
        # Usar domínio válido para email (example.com é reservado para testes)
        timestamp = int(datetime.now().timestamp())
        self.test_user_email = f"test_{timestamp}@example.com"
        self.test_user_password = "TestPassword123!"

    def validate(self, name: str, func, *args, **kwargs) -> ValidationResult:
        """Executa uma validação e armazena o resultado."""
        try:
            result = func(*args, **kwargs)
            self.results.append(result)
            print(f"{result}")
            return result
        except Exception as e:
            result = ValidationResult(name, False, f"Exception: {str(e)}")
            self.results.append(result)
            print(f"{result}")
            return result

    # ============ VALIDAÇÕES BÁSICAS ============
    
    def test_root_endpoint(self) -> ValidationResult:
        """Testa endpoint raiz."""
        try:
            response = self.session.get(
                urljoin(self.base_url, "/"),
                timeout=TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                return ValidationResult(
                    "Root Endpoint (/)",
                    True,
                    f"Status {response.status_code}",
                    {"response": data}
                )
            else:
                return ValidationResult(
                    "Root Endpoint (/)",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
        except Exception as e:
            return ValidationResult(
                "Root Endpoint (/)",
                False,
                f"Error: {str(e)}"
            )

    def test_health_endpoint(self) -> ValidationResult:
        """Testa endpoint de health check."""
        try:
            response = self.session.get(
                urljoin(self.base_url, "/health"),
                timeout=TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                db_status = data.get("database", "unknown")
                env = data.get("environment", "unknown")
                return ValidationResult(
                    "Health Check (/health)",
                    True,
                    f"Status: {data.get('status')}, DB: {db_status}, Env: {env}",
                    {"response": data}
                )
            else:
                return ValidationResult(
                    "Health Check (/health)",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
        except Exception as e:
            return ValidationResult(
                "Health Check (/health)",
                False,
                f"Error: {str(e)}"
            )

    def test_docs_endpoint(self) -> ValidationResult:
        """Testa endpoint de documentação."""
        try:
            response = self.session.get(
                urljoin(self.base_url, "/docs"),
                timeout=TIMEOUT
            )
            if response.status_code == 200:
                return ValidationResult(
                    "Documentation (/docs)",
                    True,
                    f"Status {response.status_code} - Swagger UI acessível"
                )
            else:
                return ValidationResult(
                    "Documentation (/docs)",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
        except Exception as e:
            return ValidationResult(
                "Documentation (/docs)",
                False,
                f"Error: {str(e)}"
            )

    # ============ AUTENTICAÇÃO ============
    
    def test_user_registration(self) -> ValidationResult:
        """Testa registro de novo usuário."""
        try:
            payload = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "name": "Test User"
            }
            response = self.session.post(
                urljoin(self.base_url, "/auth/register"),
                json=payload,
                timeout=TIMEOUT
            )
            if response.status_code == 201:
                data = response.json()
                return ValidationResult(
                    "User Registration (/auth/register)",
                    True,
                    f"Usuário criado: {data.get('user', {}).get('email')}",
                    {"user_id": data.get("user", {}).get("id")}
                )
            elif response.status_code == 400:
                error_msg = response.json().get("detail", "Bad Request")
                return ValidationResult(
                    "User Registration (/auth/register)",
                    False,
                    f"Status {response.status_code}: {error_msg}"
                )
            else:
                return ValidationResult(
                    "User Registration (/auth/register)",
                    False,
                    f"Expected 201, got {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            return ValidationResult(
                "User Registration (/auth/register)",
                False,
                f"Error: {str(e)}"
            )

    def test_user_login(self) -> ValidationResult:
        """Testa login de usuário."""
        try:
            payload = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            response = self.session.post(
                urljoin(self.base_url, "/auth/login"),
                json=payload,
                timeout=TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                # O endpoint retorna "token" (não "access_token")
                token = data.get("token") or data.get("access_token")
                if token:
                    self.auth_token = token
                    user_email = data.get("user", {}).get("email", "unknown")
                    return ValidationResult(
                        "User Login (/auth/login)",
                        True,
                        f"Token JWT obtido para {user_email}",
                        {"token_length": len(token)}
                    )
                else:
                    return ValidationResult(
                        "User Login (/auth/login)",
                        False,
                        f"Token não retornado na resposta. Campos disponíveis: {list(data.keys())}"
                    )
            else:
                return ValidationResult(
                    "User Login (/auth/login)",
                    False,
                    f"Expected 200, got {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            return ValidationResult(
                "User Login (/auth/login)",
                False,
                f"Error: {str(e)}"
            )

    # ============ ENDPOINTS PROTEGIDOS ============
    
    def test_protected_endpoint_without_token(self) -> ValidationResult:
        """Testa endpoint protegido sem token (deve falhar)."""
        try:
            response = self.session.get(
                urljoin(self.base_url, "/api/recommendations"),
                timeout=TIMEOUT
            )
            if response.status_code == 401 or response.status_code == 403:
                return ValidationResult(
                    "Protected Endpoint (sem token)",
                    True,
                    f"Status {response.status_code} - Acesso negado corretamente"
                )
            else:
                return ValidationResult(
                    "Protected Endpoint (sem token)",
                    False,
                    f"Expected 401/403, got {response.status_code} - Segurança comprometida!"
                )
        except Exception as e:
            return ValidationResult(
                "Protected Endpoint (sem token)",
                False,
                f"Error: {str(e)}"
            )

    def test_protected_endpoint_with_token(self) -> ValidationResult:
        """Testa endpoint protegido com token válido."""
        if not self.auth_token:
            return ValidationResult(
                "Protected Endpoint (com token)",
                False,
                "Token não disponível (login falhou)"
            )
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(
                urljoin(self.base_url, "/api/recommendations"),
                headers=headers,
                timeout=TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get("recommendations", [])
                return ValidationResult(
                    "Protected Endpoint (com token)",
                    True,
                    f"Status {response.status_code} - {len(recommendations)} recomendações retornadas",
                    {"count": len(recommendations)}
                )
            elif response.status_code == 404:
                # Sem recomendações ainda (cold start)
                return ValidationResult(
                    "Protected Endpoint (com token)",
                    True,
                    "Status 200/404 - Endpoint funcional (sem dados ainda)"
                )
            else:
                return ValidationResult(
                    "Protected Endpoint (com token)",
                    False,
                    f"Expected 200, got {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            return ValidationResult(
                "Protected Endpoint (com token)",
                False,
                f"Error: {str(e)}"
            )

    def test_restaurants_endpoint(self) -> ValidationResult:
        """Testa endpoint de restaurantes."""
        try:
            response = self.session.get(
                urljoin(self.base_url, "/api/restaurants"),
                timeout=TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                restaurants = data.get("restaurants", [])
                return ValidationResult(
                    "Restaurants Endpoint (/api/restaurants)",
                    True,
                    f"Status {response.status_code} - {len(restaurants)} restaurantes retornados",
                    {"count": len(restaurants)}
                )
            else:
                return ValidationResult(
                    "Restaurants Endpoint (/api/restaurants)",
                    False,
                    f"Expected 200, got {response.status_code}: {response.text[:200]}"
                )
        except Exception as e:
            return ValidationResult(
                "Restaurants Endpoint (/api/restaurants)",
                False,
                f"Error: {str(e)}"
            )

    # ============ INTEGRAÇÃO EXTERNA ============
    
    def test_recommendations_with_insights(self) -> ValidationResult:
        """Testa geração de recomendações com insights (integração Groq API)."""
        if not self.auth_token:
            return ValidationResult(
                "Recommendations with Insights (Groq API)",
                False,
                "Token não disponível"
            )
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(
                urljoin(self.base_url, "/api/recommendations"),
                headers=headers,
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get("recommendations", [])
                
                # Verificar se há insights gerados
                has_insights = any(
                    rec.get("insight") for rec in recommendations
                ) if recommendations else False
                
                return ValidationResult(
                    "Recommendations with Insights (Groq API)",
                    True if has_insights or len(recommendations) == 0 else False,
                    f"{len(recommendations)} recomendações, Insights: {'Sim' if has_insights else 'N/A (cold start)'}",
                    {"count": len(recommendations), "has_insights": has_insights}
                )
            elif response.status_code == 404:
                return ValidationResult(
                    "Recommendations with Insights (Groq API)",
                    True,  # Cold start é esperado
                    "Sem recomendações ainda (cold start - normal para usuário novo)"
                )
            else:
                return ValidationResult(
                    "Recommendations with Insights (Groq API)",
                    False,
                    f"Expected 200, got {response.status_code}"
                )
        except Exception as e:
            return ValidationResult(
                "Recommendations with Insights (Groq API)",
                False,
                f"Error: {str(e)}"
            )

    # ============ EXECUÇÃO PRINCIPAL ============
    
    def run_all_validations(self):
        """Executa todas as validações em ordem."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}TasteMatch API - Validação de Produção{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}URL: {self.base_url}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
        
        print(f"{Colors.BOLD}1. Validações Básicas{Colors.RESET}")
        print("-" * 70)
        self.validate("Root", self.test_root_endpoint)
        self.validate("Health", self.test_health_endpoint)
        self.validate("Docs", self.test_docs_endpoint)
        
        print(f"\n{Colors.BOLD}2. Autenticação{Colors.RESET}")
        print("-" * 70)
        self.validate("Registration", self.test_user_registration)
        self.validate("Login", self.test_user_login)
        
        print(f"\n{Colors.BOLD}3. Endpoints Protegidos{Colors.RESET}")
        print("-" * 70)
        self.validate("Protected (no token)", self.test_protected_endpoint_without_token)
        self.validate("Protected (with token)", self.test_protected_endpoint_with_token)
        self.validate("Restaurants", self.test_restaurants_endpoint)
        
        print(f"\n{Colors.BOLD}4. Integração Externa (Groq API){Colors.RESET}")
        print("-" * 70)
        self.validate("Recommendations + Insights", self.test_recommendations_with_insights)
        
        # Resumo
        self.print_summary()

    def print_summary(self):
        """Imprime resumo das validações."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}RESUMO DA VALIDAÇÃO{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed
        
        print(f"Total de testes: {total}")
        print(f"{Colors.GREEN}Passou: {passed}{Colors.RESET}")
        if failed > 0:
            print(f"{Colors.RED}Falhou: {failed}{Colors.RESET}")
            print(f"\n{Colors.BOLD}Testes que falharam:{Colors.RESET}")
            for result in self.results:
                if not result.success:
                    print(f"  {Colors.RED}✗{Colors.RESET} {result.name}: {result.message}")
        
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        if failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ TODAS AS VALIDAÇÕES PASSARAM!{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠ {failed} validação(ões) falharam. Verifique os detalhes acima.{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")
        
        return failed == 0


if __name__ == "__main__":
    validator = ProductionValidator(API_BASE_URL)
    success = validator.run_all_validations()
    sys.exit(0 if success else 1)

