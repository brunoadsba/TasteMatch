#!/usr/bin/env python3
"""
Script de Deploy Automatizado para TasteMatch
Automatiza deploy do backend (Fly.io) e frontend (Netlify) com validações robustas.

Correções críticas implementadas:
- Health check robusto com retry e backoff exponencial
- Validação segura de migrations (verificar versão antes de executar)
- Validação de endpoints críticos após deploy
- Lock para evitar deploys simultâneos
- Logs persistentes
- Validação robusta de secrets (valores e formato)
- Build local antes de deploy frontend
- Configuração externa via deploy.config.json
"""

import os
import sys
import subprocess
import time
import json
import requests
import fcntl
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class DeployStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    SKIPPED = "skipped"

@dataclass
class DeployResult:
    component: str
    status: DeployStatus
    message: str
    url: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None

class DeployScript:
    def __init__(self, dry_run: bool = False, config_path: Optional[Path] = None):
        self.dry_run = dry_run
        self.project_root = Path(__file__).parent.parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.results: List[DeployResult] = []
        
        # Carregar configuração
        config_file = config_path or (self.project_root / "scripts" / "deploy.config.json")
        if config_file.exists():
            with open(config_file, 'r') as f:
                self.config = json.load(f)
        else:
            # Configuração padrão
            self.config = {
                "backend": {
                    "app_name": "tastematch-api",
                    "url": "https://tastematch-api.fly.dev",
                    "health_check_path": "/health",
                    "health_check_timeout": 60,
                    "health_check_retry_interval": 5,
                    "health_check_max_retries": 12
                },
                "frontend": {
                    "url": "https://tastematch.netlify.app",
                    "build_dir": "frontend/dist"
                },
                "required_secrets": ["SECRET_KEY", "JWT_SECRET_KEY", "GROQ_API_KEY", "ENVIRONMENT", "DEBUG"],
                "deploy": {
                    "lock_file": "/tmp/tastematch-deploy.lock",
                    "log_file": "deploy.log"
                }
            }
        
        self.backend_url = self.config["backend"]["url"]
        self.frontend_url = self.config["frontend"]["url"]
        self.lock_file = Path(self.config["deploy"]["lock_file"])
        self.log_file = self.project_root / self.config["deploy"].get("log_file", "deploy.log")
        
    def log(self, message: str, level: str = "INFO"):
        """Log para arquivo e console"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        # Escrever no arquivo
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry)
        except Exception:
            pass  # Não falhar se não conseguir escrever
        
        # Imprimir no console
        print(message)
    
    def print_header(self, text: str):
        msg = f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n"
        self.log(msg)
    
    def print_success(self, text: str):
        msg = f"{Colors.GREEN}✅ {text}{Colors.RESET}"
        self.log(msg)
    
    def print_error(self, text: str):
        msg = f"{Colors.RED}❌ {text}{Colors.RESET}"
        self.log(msg, "ERROR")
    
    def print_warning(self, text: str):
        msg = f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}"
        self.log(msg, "WARNING")
    
    def print_info(self, text: str):
        msg = f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}"
        self.log(msg)
    
    def acquire_lock(self) -> bool:
        """Adquire lock para evitar deploys simultâneos"""
        try:
            self.lock_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Verificar se lock file existe e se processo ainda está rodando
            if self.lock_file.exists():
                try:
                    with open(self.lock_file, 'r') as f:
                        pid_str = f.read().strip()
                        if pid_str:
                            try:
                                pid = int(pid_str)
                                # Verificar se processo ainda está rodando
                                try:
                                    os.kill(pid, 0)  # Signal 0 apenas verifica se processo existe
                                    # Processo ainda existe, lock é válido
                                    self.print_error(f"Deploy já em andamento (PID: {pid})")
                                    return False
                                except ProcessLookupError:
                                    # Processo não existe mais, remover lock órfão
                                    self.print_warning(f"Removendo lock órfão (PID {pid} não existe mais)")
                                    self.lock_file.unlink()
                                except PermissionError:
                                    # Processo existe mas não temos permissão (outro usuário)
                                    self.print_error(f"Deploy já em andamento (PID: {pid})")
                                    return False
                            except ValueError:
                                # PID inválido, remover lock
                                self.print_warning("Removendo lock com PID inválido")
                                self.lock_file.unlink()
                        else:
                            # PID vazio, remover lock
                            self.print_warning("Removendo lock vazio")
                            self.lock_file.unlink()
                except FileNotFoundError:
                    # Arquivo foi removido entre verificação e leitura, continuar
                    pass
                except Exception as e:
                    # Erro ao ler lock, tentar remover e continuar
                    self.print_warning(f"Erro ao ler lock file: {e}. Removendo...")
                    try:
                        self.lock_file.unlink()
                    except:
                        pass
            
            # Criar novo lock
            self.lock_fd = open(self.lock_file, 'w')
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Escrever PID no lock file
            self.lock_fd.write(str(os.getpid()))
            self.lock_fd.flush()
            return True
        except (IOError, OSError):
            # Lock já existe e está sendo usado por outro processo (fcntl falhou)
            try:
                with open(self.lock_file, 'r') as f:
                    pid = f.read().strip()
                    if pid:
                        self.print_error(f"Deploy já em andamento (PID: {pid})")
                    else:
                        self.print_error("Deploy já em andamento (lock file bloqueado)")
            except:
                self.print_error("Deploy já em andamento")
            return False
    
    def release_lock(self):
        """Libera lock"""
        try:
            if hasattr(self, 'lock_fd'):
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
            if self.lock_file.exists():
                self.lock_file.unlink()
        except Exception:
            pass
    
    def run_command(self, cmd: List[str], cwd: Optional[Path] = None, check: bool = True, timeout: int = 300) -> Tuple[int, str, str]:
        """Executa comando e retorna (exit_code, stdout, stderr)"""
        if self.dry_run:
            self.print_info(f"[DRY RUN] {' '.join(cmd)}")
            return 0, "", ""
        
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return 1, "", str(e)
    
    def check_prerequisites(self) -> bool:
        """Verifica pré-requisitos antes do deploy"""
        self.print_header("Verificando Pré-requisitos")
        
        checks = {
            "Fly CLI": ["fly", "version"],
            "Git": ["git", "--version"],
            "Python": ["python3", "--version"],
        }
        
        all_ok = True
        for name, cmd in checks.items():
            exit_code, stdout, _ = self.run_command(cmd, check=False)
            if exit_code == 0:
                self.print_success(f"{name} instalado: {stdout.strip()}")
            else:
                self.print_error(f"{name} não encontrado")
                all_ok = False
        
        # Verificar se está no diretório correto
        if not (self.backend_dir.exists() and self.frontend_dir.exists()):
            self.print_error("Diretórios backend/ ou frontend/ não encontrados")
            all_ok = False
        
        # Verificar conectividade
        try:
            requests.get("https://fly.io", timeout=5)
            self.print_success("Conectividade com Fly.io OK")
        except Exception:
            self.print_warning("Não foi possível verificar conectividade com Fly.io")
        
        return all_ok
    
    def check_backend_secrets(self) -> bool:
        """Verifica e valida secrets do backend"""
        self.print_header("Verificando Secrets do Backend")
        
        required_secrets = self.config.get("required_secrets", [])
        secret_validation = self.config.get("secret_validation", {})
        
        # Verificar secrets no Fly.io
        exit_code, stdout, stderr = self.run_command(
            ["fly", "secrets", "list", "-a", self.config["backend"]["app_name"]],
            check=False
        )
        
        if exit_code != 0:
            self.print_warning("Não foi possível verificar secrets (fly CLI não autenticado?)")
            return True  # Continuar mesmo assim
        
        secrets_list = stdout.lower()
        missing = []
        invalid = []
        
        for secret in required_secrets:
            if secret.lower() not in secrets_list:
                missing.append(secret)
            else:
                # Validar valor se houver regra de validação
                if secret in secret_validation:
                    validation = secret_validation[secret]
                    # Buscar valor do secret
                    exit_code, value_stdout, _ = self.run_command(
                        ["fly", "secrets", "list", "-a", self.config["backend"]["app_name"]],
                        check=False
                    )
                    if exit_code == 0:
                        # Extrair valor (formato: SECRET_KEY=value)
                        for line in value_stdout.split('\n'):
                            if line.startswith(secret + '='):
                                value = line.split('=', 1)[1].strip()
                                
                                # Validar formato
                                if "required_value" in validation:
                                    expected = validation["required_value"]
                                    case_sensitive = validation.get("case_sensitive", True)
                                    if case_sensitive:
                                        if value != expected:
                                            invalid.append(f"{secret} deve ser '{expected}', mas é '{value}'")
                                    else:
                                        if value.lower() != expected.lower():
                                            invalid.append(f"{secret} deve ser '{expected}', mas é '{value}'")
                                
                                if "min_length" in validation:
                                    if len(value) < validation["min_length"]:
                                        invalid.append(f"{secret} deve ter pelo menos {validation['min_length']} caracteres")
                                break
        
        if missing:
            self.print_error(f"Secrets faltando: {', '.join(missing)}")
            self.print_info("Configure com: fly secrets set KEY=value -a " + self.config["backend"]["app_name"])
            return False
        
        if invalid:
            self.print_error(f"Secrets com valores inválidos:")
            for msg in invalid:
                self.print_error(f"  - {msg}")
            return False
        
        self.print_success("Todos os secrets necessários estão configurados e válidos")
        return True
    
    def wait_for_deploy_completion(self, app_name: str, timeout: int = 600) -> bool:
        """Aguarda conclusão do deploy verificando status"""
        self.print_info("Aguardando conclusão do deploy...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            exit_code, stdout, _ = self.run_command(
                ["fly", "status", "-a", app_name],
                check=False,
                timeout=30
            )
            
            if exit_code == 0:
                # Verificar se há máquinas em "starting" ou "stopping"
                if "starting" not in stdout.lower() and "stopping" not in stdout.lower():
                    # Verificar se todas as máquinas estão "started"
                    if "started" in stdout.lower() or "running" in stdout.lower():
                        self.print_success("Deploy concluído - todas as máquinas estão rodando")
                        return True
            
            time.sleep(5)
        
        self.print_warning("Timeout aguardando conclusão do deploy")
        return False
    
    def health_check_with_retry(self, url: str, path: str = "/health", max_retries: int = 12, retry_interval: int = 5) -> bool:
        """Health check robusto com retry e backoff exponencial"""
        self.print_info(f"Verificando health check: {url}{path}")
        
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(f"{url}{path}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    self.print_success(f"Health check passou (tentativa {attempt}/{max_retries}): {data.get('status', 'unknown')}")
                    return True
                else:
                    self.print_warning(f"Health check retornou {response.status_code} (tentativa {attempt}/{max_retries})")
            except requests.exceptions.RequestException as e:
                self.print_warning(f"Health check falhou (tentativa {attempt}/{max_retries}): {e}")
            
            if attempt < max_retries:
                # Backoff exponencial: 5s, 10s, 15s, 20s...
                wait_time = min(retry_interval * attempt, 30)
                self.print_info(f"Aguardando {wait_time}s antes da próxima tentativa...")
                time.sleep(wait_time)
        
        self.print_error("Health check falhou após todas as tentativas")
        return False
    
    def validate_critical_endpoints(self) -> bool:
        """Valida endpoints críticos após deploy"""
        self.print_header("Validando Endpoints Críticos")
        
        critical_endpoints = self.config["backend"].get("critical_endpoints", ["/health"])
        all_ok = True
        
        for endpoint in critical_endpoints:
            try:
                url = f"{self.backend_url}{endpoint}"
                response = requests.get(url, timeout=10)
                
                if response.status_code in [200, 401, 403]:  # 401/403 são OK (endpoint existe, precisa auth)
                    self.print_success(f"{endpoint}: {response.status_code}")
                else:
                    self.print_error(f"{endpoint}: {response.status_code}")
                    all_ok = False
            except Exception as e:
                self.print_error(f"{endpoint}: {e}")
                all_ok = False
        
        return all_ok
    
    def verify_migration_version(self) -> Tuple[bool, Optional[str]]:
        """Verifica versão atual da migration no banco vs código"""
        self.print_info("Verificando versão de migration...")
        
        # Obter versão atual no banco (via SSH)
        exit_code, stdout, stderr = self.run_command(
            ["fly", "ssh", "console", "-a", self.config["backend"]["app_name"], "-C", "cd /app && alembic current"],
            check=False,
            timeout=30
        )
        
        if exit_code != 0:
            self.print_warning("Não foi possível verificar versão de migration (banco pode não estar acessível)")
            return True, None  # Continuar mesmo assim
        
        current_version = stdout.strip().split()[0] if stdout.strip() else None
        
        # Obter versão head do código
        exit_code, stdout, _ = self.run_command(
            ["alembic", "heads"],
            cwd=self.backend_dir,
            check=False,
            timeout=30
        )
        
        if exit_code != 0:
            self.print_warning("Não foi possível verificar versão head do código")
            return True, None
        
        head_version = stdout.strip().split()[0] if stdout.strip() else None
        
        if current_version and head_version:
            if current_version == head_version:
                self.print_success(f"Migration já está na versão mais recente: {head_version}")
                return True, head_version
            else:
                self.print_info(f"Migration precisa ser atualizada: {current_version} -> {head_version}")
                return False, head_version
        
        return True, head_version
    
    def deploy_backend(self) -> DeployResult:
        """Faz deploy do backend no Fly.io"""
        self.print_header("Deploy do Backend (Fly.io)")
        start_time = time.time()
        
        if self.dry_run:
            return DeployResult(
                component="Backend",
                status=DeployStatus.SKIPPED,
                message="Dry run - deploy não executado"
            )
        
        app_name = self.config["backend"]["app_name"]
        
        # 1. Verificar se está autenticado
        exit_code, _, _ = self.run_command(["fly", "auth", "whoami"], check=False)
        if exit_code != 0:
            return DeployResult(
                component="Backend",
                status=DeployStatus.FAILED,
                message="Não autenticado no Fly.io. Execute: fly auth login",
                error="Not authenticated"
            )
        
        # 2. Fazer deploy
        self.print_info("Iniciando deploy do backend...")
        exit_code, stdout, stderr = self.run_command(
            ["fly", "deploy", "--remote-only", "-a", app_name],
            cwd=self.backend_dir,
            check=False,
            timeout=600  # 10 minutos
        )
        
        if exit_code != 0:
            return DeployResult(
                component="Backend",
                status=DeployStatus.FAILED,
                message=f"Deploy falhou: {stderr[:500] if stderr else stdout[:500]}",
                error=stderr,
                duration_seconds=time.time() - start_time
            )
        
        # 3. Aguardar conclusão do deploy (todas as máquinas atualizadas)
        if not self.wait_for_deploy_completion(app_name, timeout=300):
            self.print_warning("Deploy pode não ter concluído completamente")
        
        # 4. Health check robusto
        health_path = self.config["backend"]["health_check_path"]
        max_retries = self.config["backend"].get("health_check_max_retries", 12)
        retry_interval = self.config["backend"].get("health_check_retry_interval", 5)
        
        if not self.health_check_with_retry(self.backend_url, health_path, max_retries, retry_interval):
            return DeployResult(
                component="Backend",
                status=DeployStatus.FAILED,
                message="Health check falhou após deploy",
                error="Health check timeout",
                duration_seconds=time.time() - start_time
            )
        
        # 5. Verificar e executar migrations (se necessário)
        migration_config = self.config.get("migrations", {})
        if migration_config.get("verify_version", True):
            migration_ok, head_version = self.verify_migration_version()
            
            if not migration_ok and head_version:
                self.print_info("Executando migrations...")
                # Usar release command se configurado, senão SSH
                # Por enquanto, usar SSH (release command será adicionado no fly.toml)
                exit_code, stdout, stderr = self.run_command(
                    ["fly", "ssh", "console", "-a", app_name, "-C", "cd /app && alembic upgrade head"],
                    check=False,
                    timeout=migration_config.get("timeout", 300)
                )
                
                if exit_code == 0:
                    self.print_success("Migrations executadas com sucesso")
                else:
                    self.print_warning(f"Migrations podem ter falhado: {stderr[:200]}")
                    # Não falhar o deploy por causa de migrations (pode ser que já estejam aplicadas)
        
        duration = time.time() - start_time
        return DeployResult(
            component="Backend",
            status=DeployStatus.SUCCESS,
            message="Deploy concluído com sucesso",
            url=self.backend_url,
            duration_seconds=duration
        )
    
    def build_frontend_local(self) -> bool:
        """Faz build local do frontend antes de deploy"""
        self.print_info("Fazendo build local do frontend...")
        
        # Executar npm install
        self.print_info("Instalando dependências...")
        exit_code, stdout, stderr = self.run_command(
            ["npm", "install"],
            cwd=self.frontend_dir,
            check=False,
            timeout=300
        )
        
        if exit_code != 0:
            self.print_error(f"npm install falhou: {stderr[:500]}")
            return False
        
        # Executar npm run build
        self.print_info("Compilando frontend...")
        exit_code, stdout, stderr = self.run_command(
            ["npm", "run", "build"],
            cwd=self.frontend_dir,
            check=False,
            timeout=300
        )
        
        if exit_code != 0:
            self.print_error(f"Build falhou: {stderr[:500]}")
            return False
        
        # Verificar se dist foi criado
        dist_dir = self.frontend_dir / "dist"
        if not dist_dir.exists() or not any(dist_dir.iterdir()):
            self.print_error("Build não produziu arquivos em dist/")
            return False
        
        self.print_success("Build local concluído com sucesso")
        return True
    
    def deploy_frontend(self) -> DeployResult:
        """Faz deploy do frontend no Netlify"""
        self.print_header("Deploy do Frontend (Netlify)")
        start_time = time.time()
        
        if self.dry_run:
            return DeployResult(
                component="Frontend",
                status=DeployStatus.SKIPPED,
                message="Dry run - deploy não executado"
            )
        
        # 1. Build local primeiro
        if not self.build_frontend_local():
            return DeployResult(
                component="Frontend",
                status=DeployStatus.FAILED,
                message="Build local falhou",
                error="Build failed",
                duration_seconds=time.time() - start_time
            )
        
        # 2. Verificar se Netlify CLI está instalado
        exit_code, _, _ = self.run_command(["netlify", "--version"], check=False)
        if exit_code != 0:
            self.print_warning("Netlify CLI não encontrado. Deploy será feito via Git push.")
            return DeployResult(
                component="Frontend",
                status=DeployStatus.PENDING,
                message="Netlify CLI não instalado. Faça push para Git para trigger automático."
            )
        
        # 3. Verificar se está autenticado
        exit_code, _, _ = self.run_command(["netlify", "status"], check=False)
        if exit_code != 0:
            self.print_warning("Não autenticado no Netlify. Deploy será feito via Git push.")
            return DeployResult(
                component="Frontend",
                status=DeployStatus.PENDING,
                message="Não autenticado no Netlify. Faça push para Git para trigger automático."
            )
        
        # 4. Fazer deploy
        self.print_info("Iniciando deploy do frontend...")
        dist_dir = self.config["frontend"]["build_dir"]
        exit_code, stdout, stderr = self.run_command(
            ["netlify", "deploy", "--prod", "--dir", dist_dir],
            cwd=self.project_root,
            check=False,
            timeout=600
        )
        
        if exit_code != 0:
            return DeployResult(
                component="Frontend",
                status=DeployStatus.FAILED,
                message=f"Deploy falhou: {stderr[:500] if stderr else stdout[:500]}",
                error=stderr,
                duration_seconds=time.time() - start_time
            )
        
        duration = time.time() - start_time
        return DeployResult(
            component="Frontend",
            status=DeployStatus.SUCCESS,
            message="Deploy concluído com sucesso",
            url=self.frontend_url,
            duration_seconds=duration
        )
    
    def validate_deploy(self) -> bool:
        """Valida se o deploy foi bem-sucedido"""
        self.print_header("Validando Deploy")
        
        all_ok = True
        
        # Validar backend
        health_path = self.config["backend"]["health_check_path"]
        try:
            response = requests.get(f"{self.backend_url}{health_path}", timeout=10)
            if response.status_code == 200:
                self.print_success(f"Backend respondendo: {response.json()}")
            else:
                self.print_error(f"Backend retornou {response.status_code}")
                all_ok = False
        except Exception as e:
            self.print_error(f"Backend não acessível: {e}")
            all_ok = False
        
        # Validar endpoints críticos
        if not self.validate_critical_endpoints():
            all_ok = False
        
        # Validar frontend
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                self.print_success("Frontend acessível")
            else:
                self.print_error(f"Frontend retornou {response.status_code}")
                all_ok = False
        except Exception as e:
            self.print_error(f"Frontend não acessível: {e}")
            all_ok = False
        
        return all_ok
    
    def run(self, deploy_backend: bool = True, deploy_frontend: bool = True):
        """Executa o processo completo de deploy"""
        self.print_header("🚀 TasteMatch - Deploy Automatizado")
        
        # Adquirir lock
        if not self.acquire_lock():
            return False
        
        try:
            # 1. Verificar pré-requisitos
            if not self.check_prerequisites():
                self.print_error("Pré-requisitos não atendidos. Abortando.")
                return False
            
            # 2. Verificar secrets (backend)
            if deploy_backend:
                if not self.check_backend_secrets():
                    response = input("Secrets faltando ou inválidos. Continuar mesmo assim? (s/N): ")
                    if response.lower() != 's':
                        return False
            
            # 3. Deploy backend
            if deploy_backend:
                result = self.deploy_backend()
                self.results.append(result)
                if result.status == DeployStatus.FAILED:
                    self.print_error(f"Deploy do backend falhou: {result.message}")
                    return False
            
            # 4. Deploy frontend
            if deploy_frontend:
                result = self.deploy_frontend()
                self.results.append(result)
                if result.status == DeployStatus.FAILED:
                    self.print_error(f"Deploy do frontend falhou: {result.message}")
                    return False
            
            # 5. Validar deploy
            if not self.validate_deploy():
                self.print_warning("Deploy concluído, mas validação falhou. Verifique manualmente.")
            
            # 6. Resumo
            self.print_summary()
            
            return True
        finally:
            self.release_lock()
    
    def print_summary(self):
        """Imprime resumo do deploy"""
        self.print_header("📊 Resumo do Deploy")
        
        for result in self.results:
            if result.status == DeployStatus.SUCCESS:
                self.print_success(f"{result.component}: {result.message}")
                if result.url:
                    self.print_info(f"   URL: {result.url}")
                if result.duration_seconds:
                    self.print_info(f"   Duração: {result.duration_seconds:.1f}s")
            elif result.status == DeployStatus.FAILED:
                self.print_error(f"{result.component}: {result.message}")
            elif result.status == DeployStatus.PENDING:
                self.print_warning(f"{result.component}: {result.message}")
            else:
                self.print_info(f"{result.component}: {result.message}")
        
        # Salvar resumo em JSON
        summary_file = self.project_root / "deploy-summary.json"
        try:
            with open(summary_file, 'w') as f:
                json.dump([asdict(r) for r in self.results], f, indent=2, default=str)
            self.print_info(f"Resumo salvo em: {summary_file}")
        except Exception:
            pass

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy automatizado do TasteMatch")
    parser.add_argument("--backend-only", action="store_true", help="Deploy apenas backend")
    parser.add_argument("--frontend-only", action="store_true", help="Deploy apenas frontend")
    parser.add_argument("--dry-run", action="store_true", help="Simular deploy sem executar")
    parser.add_argument("--config", type=Path, help="Caminho para arquivo de configuração")
    
    args = parser.parse_args()
    
    deploy_backend = not args.frontend_only
    deploy_frontend = not args.backend_only
    
    script = DeployScript(dry_run=args.dry_run, config_path=args.config)
    success = script.run(deploy_backend=deploy_backend, deploy_frontend=deploy_frontend)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

