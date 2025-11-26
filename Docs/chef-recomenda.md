# Plano de Implementação: Chef Recomenda

## Objetivo

Implementar feature "Chef Recomenda" que analisa o perfil do usuário e faz uma recomendação única e direta, substituindo o Terminal de Raciocínio da IA no Dashboard por uma funcionalidade mais útil e acionável.

## Estrutura do Plano

### Fase 1: Backend - Endpoint e Lógica de Recomendação

#### 1.1 Criar endpoint `/api/recommendations/chef-choice`

**Arquivo:** `backend/app/api/routes/recommendations.py`

**Ações:**
- Adicionar novo endpoint `GET /api/recommendations/chef-choice`
- Endpoint deve retornar uma única recomendação escolhida inteligentemente
- Resposta deve incluir: restaurante, score de similaridade, explicação gerada por LLM, razões da escolha

**Lógica de escolha:**
1. Obter top 3 recomendações usando `generate_recommendations(limit=3)`
2. Escolher a melhor baseada em:
   - Similaridade (peso 40%)
   - Rating do restaurante (peso 20%)
   - Novidade (não pedido recentemente) (peso 20%)
   - Match com padrões do usuário (peso 20%)
3. Gerar explicação personalizada via LLM explicando por que essa foi escolhida

**Model de resposta:**
```python
class ChefRecommendationResponse(BaseModel):
    restaurant: RestaurantResponse
    similarity_score: float
    explanation: str  # Explicação gerada por LLM
    reasoning: List[str]  # Lista de razões (ex: "Você costuma pedir comida vegetariana")
    confidence: float  # Confiança da recomendação (0.0 a 1.0)
    generated_at: datetime
```

#### 1.2 Criar função de geração de explicação

**Arquivo:** `backend/app/core/llm_service.py`

**Ações:**
- Adicionar função `generate_chef_explanation()` que:
  - Recebe contexto do usuário, restaurante recomendado, e razões
  - Gera explicação natural e personalizada em português
  - Explica por que esse restaurante foi escolhido especificamente para o usuário
  - Formato: "Baseado no seu histórico de pedidos vegetarianos e sua preferência por opções saudáveis às 19h, eu recomendaria..."

#### 1.3 Criar função de seleção inteligente

**Arquivo:** `backend/app/core/recommender.py`

**Ações:**
- Adicionar função `select_chef_recommendation()` que:
  - Recebe lista de recomendações e contexto do usuário
  - Aplica algoritmo de scoring ponderado
  - Retorna a melhor recomendação com razões

### Fase 2: Frontend - Componentes e Integração

#### 2.1 Criar componente ChefRecommendationCard

**Arquivo:** `frontend/src/components/features/ChefRecommendationCard.tsx`

**Funcionalidades:**
- Card destacado mostrando a recomendação única do Chef
- Exibir: nome do restaurante, rating, tipo de culinária, explicação
- Botão "Ver Recomendação Completa" (abre modal com detalhes)
- Botão "Ver Outras Opções" (scroll para grid de recomendações)
- Botão "Ver Raciocínio" (opcional, mostra terminal em modal)
- Badge de confiança (ex: "95% de confiança")
- Ícone/título "Chef Recomenda" ou "🎯 Chef Recomenda"

**Design:**
- Card maior e mais destacado que RestaurantCard normal
- Cores/bordas que chamem atenção (ex: borda dourada ou destaque)
- Responsivo (mobile-first)

#### 2.2 Criar hook useChefRecommendation

**Arquivo:** `frontend/src/hooks/useChefRecommendation.ts`

**Funcionalidades:**
- Hook para buscar recomendação do Chef
- Estados: `chefRecommendation`, `loading`, `error`
- Função `refresh()` para atualizar recomendação
- Integração com API

#### 2.3 Adicionar método no cliente API

**Arquivo:** `frontend/src/lib/api.ts`

**Ações:**
- Adicionar método `async getChefRecommendation(): Promise<ChefRecommendation>`
- Chamar endpoint `GET /api/recommendations/chef-choice`

#### 2.4 Adicionar tipos TypeScript

**Arquivo:** `frontend/src/types/index.ts`

**Ações:**
- Adicionar interface `ChefRecommendation`:
```typescript
export interface ChefRecommendation {
  restaurant: Restaurant;
  similarity_score: number;
  explanation: string;
  reasoning: string[];
  confidence: number;
  generated_at: string;
}
```

#### 2.5 Criar modal para mostrar raciocínio (terminal opcional)

**Arquivo:** `frontend/src/components/features/ChefReasoningModal.tsx`

**Funcionalidades:**
- Modal que mostra o terminal de raciocínio da IA
- Exibe logs de como o Chef chegou à recomendação
- Reutilizar `AIReasoningLogComponent` dentro do modal
- Botão "Fechar" e opção de limpar logs

### Fase 3: Integração no Dashboard

#### 3.1 Substituir Terminal por Chef Recomenda

**Arquivo:** `frontend/src/pages/Dashboard.tsx`

**Modificações:**
- Remover import e uso de `AIReasoningLogComponent` da sidebar
- Adicionar import e uso de `ChefRecommendationCard`
- Manter `useChefRecommendation()` hook
- Layout no modo demo:
  - Grid: LLM Insight Panel (3 cols) + Chef Recomenda (1 col)
  - Chef Recomenda substitui o Terminal na sidebar direita

**Layout:**
```tsx
{isDemoMode && (
  <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
    <div className="lg:col-span-3">
      <LLMInsightPanel refreshTrigger={ordersRefreshTrigger} />
    </div>
    <div className="lg:col-span-1">
      <ChefRecommendationCard 
        refreshTrigger={ordersRefreshTrigger}
        onViewReasoning={() => setReasoningModalOpen(true)}
      />
    </div>
  </div>
)}
```

#### 3.2 Adicionar modal de raciocínio opcional

**Arquivo:** `frontend/src/pages/Dashboard.tsx`

**Modificações:**
- Estado para controlar modal de raciocínio: `const [reasoningModalOpen, setReasoningModalOpen] = useState(false)`
- Renderizar `ChefReasoningModal` com logs do `useAIReasoning()`
- Modal pode ser aberto via botão "Ver Raciocínio" no ChefRecommendationCard

### Fase 4: Tratamento de Edge Cases

#### 4.1 Cold Start (sem pedidos)

**Comportamento:**
- Se usuário não tem pedidos, mostrar mensagem especial:
  - "Ainda estou aprendendo seus gostos! Faça alguns pedidos para receber recomendações personalizadas."
  - Botão para simular pedidos (se modo demo)

#### 4.2 Sem recomendações disponíveis

**Comportamento:**
- Mostrar mensagem: "Não encontrei recomendações no momento. Tente novamente em instantes."
- Botão "Atualizar"

#### 4.3 Loading state

**Comportamento:**
- Mostrar skeleton/shimmer enquanto carrega
- Spinner discreto

### Fase 5: Melhorias e Polimento

#### 5.1 Cache e atualização

- Cachear recomendação do Chef por 5 minutos
- Atualizar automaticamente quando pedidos são criados
- Usar `refreshTrigger` do Dashboard para sincronizar

#### 5.2 Acessibilidade

- ARIA labels apropriados
- Navegação por teclado
- Contraste de cores adequado

#### 5.3 Responsividade

- Card se adapta a mobile
- Grid responsivo no Dashboard
- Modal responsivo

## Arquivos a Criar

1. `backend/app/api/routes/recommendations.py` - Adicionar endpoint chef-choice
2. `backend/app/core/recommender.py` - Adicionar função select_chef_recommendation
3. `backend/app/core/llm_service.py` - Adicionar função generate_chef_explanation
4. `frontend/src/components/features/ChefRecommendationCard.tsx` - Novo componente
5. `frontend/src/components/features/ChefReasoningModal.tsx` - Novo componente modal
6. `frontend/src/hooks/useChefRecommendation.ts` - Novo hook

## Arquivos a Modificar

1. `backend/app/api/routes/recommendations.py` - Adicionar endpoint e models
2. `backend/app/core/llm_service.py` - Adicionar função de explicação
3. `backend/app/core/recommender.py` - Adicionar função de seleção
4. `frontend/src/lib/api.ts` - Adicionar método getChefRecommendation
5. `frontend/src/types/index.ts` - Adicionar interface ChefRecommendation
6. `frontend/src/pages/Dashboard.tsx` - Substituir Terminal por Chef Recomenda

## Ordem de Implementação Recomendada

1. Backend: Endpoint e lógica de escolha (Fase 1)
2. Frontend: Tipos e API client (Fase 2.3, 2.4)
3. Frontend: Hook useChefRecommendation (Fase 2.2)
4. Frontend: Componente ChefRecommendationCard (Fase 2.1)
5. Frontend: Integração no Dashboard (Fase 3)
6. Frontend: Modal de raciocínio opcional (Fase 2.5, 3.2)
7. Edge cases e polimento (Fase 4, 5)

## Critérios de Sucesso

- Chef Recomenda aparece no Dashboard substituindo o Terminal
- Recomendação é única e personalizada baseada no perfil
- Explicação é clara e em português natural
- Funciona corretamente em Cold Start
- Terminal de raciocínio acessível via modal (opcional)
- Interface responsiva e acessível
- Performance adequada (carregamento < 2s)

## Notas Técnicas

- Reutilizar infraestrutura existente (LLM service, recommender)
- Manter compatibilidade com código existente
- Terminal não é removido completamente, apenas movido para modal opcional
- Chef Recomenda atualiza automaticamente quando pedidos são criados
