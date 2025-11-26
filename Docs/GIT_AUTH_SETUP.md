# Configuração de Autenticação Git para GitHub

## Problema
```
remote: Invalid username or token. Password authentication is not supported for Git operations.
fatal: Authentication failed
```

## Soluções

### Opção 1: GitHub CLI (Recomendado - Mais Fácil)

```bash
# 1. Reautenticar
gh auth login -h github.com

# 2. Configurar Git para usar GitHub CLI
gh auth setup-git

# 3. Fazer push
git push origin feature/mobile-first-refactor
```

**Vantagens:**
- ✅ Mais fácil e seguro
- ✅ Gerencia tokens automaticamente
- ✅ Não precisa copiar/colar tokens

---

### Opção 2: Personal Access Token (PAT)

#### Passo 1: Criar Token
1. Acesse: https://github.com/settings/tokens
2. Clique em "Generate new token" → "Generate new token (classic)"
3. Nome: `TasteMatch Local Dev`
4. Escopo: Marque `repo` (todas as permissões)
5. Clique em "Generate token"
6. **COPIE O TOKEN** (você só verá uma vez!)

#### Passo 2: Usar Token no Push
```bash
git push origin feature/mobile-first-refactor
# Username: brunoadsba
# Password: [cole o token aqui]
```

**Nota:** O Git pode salvar o token no credential helper para não pedir novamente.

---

### Opção 3: SSH (Mais Seguro - Longo Prazo)

#### Passo 1: Gerar Chave SSH
```bash
ssh-keygen -t ed25519 -C "seu-email@example.com"
# Pressione Enter para aceitar local padrão
# Digite uma senha (opcional, mas recomendado)
```

#### Passo 2: Adicionar Chave ao GitHub
```bash
# Copiar chave pública
cat ~/.ssh/id_ed25519.pub
```

1. Acesse: https://github.com/settings/keys
2. Clique em "New SSH key"
3. Título: `TasteMatch Local Dev`
4. Cole a chave pública
5. Clique em "Add SSH key"

#### Passo 3: Mudar Remote para SSH
```bash
cd /home/brunoadsba/ifood/tastematch
git remote set-url origin git@github.com:brunoadsba/TasteMatch.git
```

#### Passo 4: Testar e Fazer Push
```bash
# Testar conexão
ssh -T git@github.com

# Fazer push
git push origin feature/mobile-first-refactor
```

**Vantagens:**
- ✅ Mais seguro (chave privada nunca sai do seu computador)
- ✅ Não expira (diferente de tokens)
- ✅ Padrão da indústria

---

## Verificar Configuração Atual

```bash
# Ver remote atual
git remote -v

# Verificar autenticação GitHub CLI
gh auth status

# Verificar chaves SSH
ls -la ~/.ssh/
```

---

## Troubleshooting

### GitHub CLI não autentica
```bash
# Logout e login novamente
gh auth logout -h github.com
gh auth login -h github.com
```

### SSH não funciona
```bash
# Verificar se ssh-agent está rodando
eval "$(ssh-agent -s)"

# Adicionar chave ao ssh-agent
ssh-add ~/.ssh/id_ed25519

# Testar novamente
ssh -T git@github.com
```

### Token não funciona
- Verifique se o token tem escopo `repo`
- Verifique se o token não expirou
- Crie um novo token se necessário

---

**Última atualização:** 26/11/2025

