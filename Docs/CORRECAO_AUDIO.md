# Correção: Problema de Áudio no Endpoint /api/chat/

> **Data:** 29 de Novembro de 2025  
> **Status:** ✅ Corrigido

---

## Problema Identificado

O áudio não estava funcionando no endpoint `/api/chat/` por dois motivos:

1. **Caminho incorreto do endpoint de áudio**
   - O endpoint está registrado em `/api/chat/audio/{filename}` (router tem prefixo `/api/chat`)
   - O código estava gerando URLs como `/api/audio/{filename}` (caminho errado)

2. **Erros sendo silenciados**
   - Exceções no TTS eram logadas mas não visíveis
   - Falta de logging detalhado para debug

---

## Correções Aplicadas

### 1. Correção do Caminho do Endpoint

**Arquivo:** `backend/app/api/routes/chat.py` (linha 233)

**Antes:**
```python
audio_url = f"/api/audio/{audio_filename}"
```

**Depois:**
```python
audio_url = f"/api/chat/audio/{audio_filename}"
```

**Motivo:** O router `chat` tem prefixo `/api/chat`, então o endpoint completo é `/api/chat/audio/{filename}`.

---

### 2. Melhoria no Logging de Erros

**Arquivo:** `backend/app/api/routes/chat.py` (linhas 224-248)

**Melhorias:**
- Logging antes de gerar áudio
- Logging após sucesso
- Logging detalhado de erros com traceback
- Garantir que `audio_url = None` em caso de erro

**Código:**
```python
if audio is not None:
    audio_service = get_audio_service()
    try:
        logger.info(f"Gerando áudio para resposta do usuário {current_user.id}")
        
        # Gerar áudio da resposta usando Edge-TTS
        audio_path = audio_service.text_to_speech(response["answer"])
        
        logger.info(f"Áudio gerado com sucesso: {audio_path}")
        
        audio_filename = Path(audio_path).name
        audio_url = f"/api/chat/audio/{audio_filename}"  # ← Corrigido
        
        logger.info(f"Audio URL gerada: {audio_url}")
        
        # Atualizar última mensagem do assistente com audio_url
        # ...
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(
            f"Erro ao gerar áudio da resposta: {str(e)}\n{error_traceback}",
            exc_info=True
        )
        audio_url = None  # Garantir que audio_url seja None em caso de erro
```

---

## Estrutura do Endpoint de Áudio

### Registro do Router

**Arquivo:** `backend/app/main.py` (linha 235)

```python
app.include_router(chat.router)
```

### Router de Chat

**Arquivo:** `backend/app/api/routes/chat.py` (linha 24)

```python
router = APIRouter(prefix="/api/chat", tags=["chat"])
```

### Endpoint de Áudio

**Arquivo:** `backend/app/api/routes/chat.py` (linhas 312-343)

```python
@router.get("/audio/{filename}")
async def get_audio_file(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """
    Serve arquivos de áudio gerados pelo TTS
    """
    from fastapi.responses import FileResponse
    from app.core.audio_service import get_audio_service
    
    audio_service = get_audio_service()
    audio_path = audio_service.temp_dir / filename
    
    # Validar que o arquivo existe
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo de áudio não encontrado")
    
    return FileResponse(
        path=str(audio_path),
        media_type="audio/mpeg",
        filename=filename
    )
```

**URL completa:** `/api/chat/audio/{filename}`

---

## Fluxo Completo de Áudio

### 1. Recebimento de Áudio do Usuário

1. Usuário envia arquivo de áudio via POST `/api/chat/`
2. Arquivo é validado (formato, tamanho)
3. Áudio é convertido em texto usando Groq Whisper (STT)
4. Texto é processado normalmente

### 2. Geração de Áudio da Resposta

1. Após gerar resposta do Chef Virtual
2. Se usuário enviou áudio, gera áudio da resposta usando Edge-TTS
3. Salva arquivo em `temp_dir` (diretório temporário)
4. Gera URL: `/api/chat/audio/{filename}`
5. Salva URL no banco de dados (campo `audio_url` da mensagem)

### 3. Servir Arquivo de Áudio

1. Frontend faz requisição GET para `/api/chat/audio/{filename}`
2. Endpoint valida autenticação do usuário
3. Retorna arquivo de áudio via `FileResponse`

---

## Verificações Realizadas

- ✅ Sintaxe Python: OK
- ✅ Linter: Sem erros
- ✅ Caminho do endpoint: Corrigido
- ✅ Logging: Melhorado

---

## Próximos Passos

1. **Reiniciar backend** para aplicar correções
2. **Testar envio de áudio** via POST `/api/chat/`
3. **Verificar logs** para confirmar que áudio está sendo gerado
4. **Testar acesso ao arquivo** via GET `/api/chat/audio/{filename}`

---

## Possíveis Problemas Adicionais

Se o áudio ainda não funcionar após essas correções, verificar:

1. **Edge-TTS funcionando?**
   ```bash
   pip list | grep edge-tts
   python -c "from edge_tts import Communicate; print('OK')"
   ```

2. **Diretório temporário existe?**
   - Verificar se `temp_dir` está sendo criado
   - Verificar permissões de escrita

3. **Arquivo sendo salvo?**
   - Verificar se arquivo está sendo criado em `temp_dir`
   - Verificar se nome do arquivo está correto

4. **Endpoint acessível?**
   - Testar diretamente: `GET /api/chat/audio/teste.mp3`
   - Verificar autenticação (requer token)

---

## Logs Esperados

### Sucesso
```
INFO - Gerando áudio para resposta do usuário {user_id}
INFO - Áudio gerado com sucesso: /tmp/tastematch_audio/tts_xxxxx.mp3
INFO - Audio URL gerada: /api/chat/audio/tts_xxxxx.mp3
INFO - Audio URL salva no banco de dados para mensagem do assistente
```

### Erro
```
ERROR - Erro ao gerar áudio da resposta: {erro}
[Traceback completo...]
```

---

**Última atualização:** 29/11/2025 17:50

