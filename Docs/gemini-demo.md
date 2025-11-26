O plano `demo.md` que você apresentou é um **ótimo ponto de partida estrutural**. Ele cobre o essencial: backend (banco de dados, API), frontend (UI, Hooks) e a lógica de negócio básica.

No entanto, para impressionar um recrutador e demonstrar que o sistema é **"Moderno"**, **"Robusto"** e focado na **"LLM"**, o plano atual tem alguns pontos cegos. Ele foca muito na *mecânica* de criar pedidos e pouco na *visualização da inteligência*.

Aqui está uma análise crítica e sugestões para elevar o nível da demonstração:

### 1. O Principal Problema: A "Caixa Preta" da LLM
**Diagnóstico:** No plano atual, o usuário cria um pedido e as recomendações mudam "magicamente". O recrutador não vê a LLM atuando. Ele só vê o resultado final.
**Solução:** Você precisa de **"Explainability" (Explicabilidade)**. O recrutador precisa ver o *raciocínio* da IA.

**Sugestão de Melhoria:**
* **Adicione um componente "AI Insights" ou "Terminal de Pensamento":**
    * Ao lado das recomendações, mostre um box: *"Análise da IA: Detectamos que o usuário pediu 'Hambúrguer' (Fast Food/American). O interesse por 'Saladas' caiu 15%, e a confiança em 'Pizzas' subiu 10% devido à correlação de 'Comfort Food'."*
    * Isso prova que existe uma inteligência analisando os dados, e não apenas um filtro simples de banco de dados.

### 2. Redução de Fricção (A "Regra dos 30 Segundos")
**Diagnóstico:** O plano pede para o recrutador abrir um modal, selecionar restaurante, digitar valor, dar nota... Isso é trabalhoso. O recrutador tem pouco tempo.
**Solução:** Automação de Cenários (Personas).

**Sugestão de Melhoria:**
* Em vez de apenas criar pedidos manuais um por um, adicione **"Botões de Persona Rápida"** no `OrderSimulator`:
    * Botão **"Simular Perfil Fitness"**: Cria automaticamente 3 pedidos de salada/açaí em sequência.
    * Botão **"Simular Perfil Junk Food"**: Cria 3 pedidos de pizza/burger.
    * Isso permite que o recrutador veja a mudança drástica nas recomendações com **um clique**.

### 3. Gestão de Estado e "Reset"
**Diagnóstico:** O plano não menciona como limpar os dados. Se o recrutador testar, o próximo recrutador verá os dados do anterior? Ou se ele quiser testar um cenário diferente?
**Solução:** Funcionalidade de Reset.

**Sugestão de Melhoria:**
* Adicionar botão **"Resetar Simulação"** visível quando o `isDemoMode` estiver ativo.
* Isso deve chamar um endpoint `DELETE /api/orders?is_simulation=true` para limpar o histórico fictício e voltar ao "Cold Start" instantaneamente.

### 4. Visualização de Progresso (Gamificação)
**Diagnóstico:** O texto "3/5 pedidos" é funcional, mas pouco visual.
**Solução:** Barra de XP ou Evolução de Perfil.

**Sugestão de Melhoria:**
* Substitua o texto simples por uma barra de progresso visual que muda de cor:
    * 0 pedidos: Cinza ("Usuário Desconhecido")
    * 1-3 pedidos: Azul ("Aprendendo...")
    * 5+ pedidos: Verde ou Dourado ("Perfil Personalizado Identificado")

---

### Plano Revisado e Aditivo (Sugestões Concretas)

Aqui estão as adições recomendadas ao seu arquivo `demo.md` para torná-lo profissional:

#### Adicionar à Fase 1 (Backend)
* **Endpoint de Reset:** Criar `DELETE /api/simulation/reset` para apagar apenas pedidos onde `is_simulation = true`.
* **Endpoint de Insights (Opcional mas Recomendado):** Se a sua LLM gera uma explicação textual do perfil, salve isso e retorne para o frontend exibir.

#### Adicionar à Fase 2 (Frontend - Componente)
* **Modificar `OrderSimulator.tsx`:**
    * Adicionar aba "Cenários Prontos" (ex: *Vegano*, *Carnívoro*, *Doceiro*).
    * Ao clicar, dispara múltiplos pedidos simulados em batch.

#### Adicionar à Fase 3 (Frontend - Dashboard)
* **Componente `LiveAIReasoning.tsx`:**
    * Um pequeno painel (tipo "Toast" persistente ou card lateral) que anima texto digitando (efeito typewriter) após cada simulação: *"Ajustando pesos: +Italiana, -Japonesa..."*.
* **Botão de Reset:** No header do modo demo, um botão vermelho ou ícone de lixeira para "Limpar Simulação".

---

### Como apresentar isso na UI (UX Design)

Para ficar **moderno**, evite muitos modais bloqueantes. Sugiro o seguinte layout quando o "Modo Demo" é ativado:

1.  O Header ganha uma barra amarela/azul no topo: *"Modo Demonstração Ativo - Dados não serão salvos permanentemente"*.
2.  Surge uma **Barra Lateral Flutuante (Drawer) à direita** ou um painel fixo no rodapé contendo:
    * Controle de Simulação (Botões de Persona).
    * Log de Ações ("Pedido Simulado Criado").
    * **O "Cérebro" (Log da LLM explicando a mudança).**
3.  O Dashboard principal (centro) reage em tempo real a esses cliques.

### Resumo da Validação
O seu plano atual é **nota 7/10**. Ele funciona, mas é "tímido".
Com as alterações acima (Personas Rápidas, Botão de Reset e Visualização do Raciocínio da IA), ele vai para **nota 10/10**, pois mostra não só que o sistema funciona, mas que você entende de **Experiência do Usuário (UX)** e **Engenharia de Prompt/IA**.

Perfeito. Focar na **Interface (UI)** e na **Experiência (UX)** para *simular* a inteligência é uma estratégia excelente para demos. Isso garante que a apresentação seja **fluida, controlada e livre de falhas** (o famoso "efeito demo"), enquanto o backend real apenas processa os dados brutos.

Aqui está o **Plano de Atualização (Addendum)** para tornar o seu `demo.md` robusto, moderno e "sexy" aos olhos de um recrutador.

-----

# Addendum ao Plano: "AI Experience & Smart Simulation"

Este módulo expande o plano original para focar na **visualização da inteligência** e **redução de fricção**.

## 1\. Nova Funcionalidade: "Quick Personas" (Automação de Cenários)

Em vez de preencher formulários manualmente, o recrutador clica em um "Arquétipo" e o sistema gera 3-5 pedidos instantaneamente, simulando um histórico de meses em segundos.

**Componente:** `SimulationControls.tsx` (Substitui ou expande o `OrderSimulator`)

**Arquétipos Sugeridos:**

1.  **O "Marombeiro" (Fit/Saudável):**
      * *Ação:* Gera 3 pedidos (Poke, Salada, Açaí).
      * *Resultado esperado:* Recomendações de "Saudável", "Sem Glúten", "Natural".
2.  **O "Comfort Food" (Pizza/Burger):**
      * *Ação:* Gera 3 pedidos (Pizza Calabresa, X-Bacon, Milkshake).
      * *Resultado esperado:* Recomendações de "Lanches", "Brasileira", "Pizza".
3.  **O "Explorador" (Variado):**
      * *Ação:* 1 Sushi, 1 Pizza, 1 Vegano.
      * *Resultado esperado:* Recomendações híbridas/populares.

## 2\. Nova Funcionalidade: "AI Insight Terminal" (A Cereja do Bolo 🍒)

Já que não vamos puxar o raciocínio real do backend agora, criaremos um componente visual que **simula a análise em tempo real**. Isso dá a sensação de "processamento pesado" de IA.

**Componente:** `AIReasoningLog.tsx`
**Localização:** Um painel lateral ou um card flutuante no canto da tela.

**Comportamento:**
Ao clicar em uma Persona (ex: "Marombeiro"), o terminal exibe mensagens com delay (efeito *typewriter*):

> `[SYSTEM] Novos dados de consumo detectados (3 pedidos).`
> `[NLP-CORE] Analisando padrões semânticos: "Salada", "Whey", "Frango"...`
> `[INFERENCE] Categoria dominante identificada: "Saudável" (Confidence: 98%).`
> `[ADJUSTMENT] Reduzindo peso de "Fast Food" em 45%.`
> `[ADJUSTMENT] Aumentando peso de "Natural" em 60%.`
> `[FINAL] Recomendações atualizadas com sucesso.`

## 3\. Fluxo de Reset (Limpeza)

Para permitir que o recrutador brinque várias vezes, precisamos de um botão de pânico que limpa tudo.

**Backend:**

  * Endpoint: `DELETE /api/orders/simulation` (Remove apenas onde `is_simulation=true`).

**Frontend:**

  * Botão "Reiniciar Demo" no topo.
  * Ao clicar: Limpa o banco, limpa o cache do React Query, reseta o Terminal de IA para "Aguardando input...".

-----

## Estrutura Atualizada da UI (Mockup Mental)

Imagine a tela do Dashboard com o **Modo Demo Ativo**:

1.  **Top Bar (Aviso de Demo):**

      * Faixa colorida (Indigo/Roxo) no topo: *"🛠️ Modo Demonstração - Simulador de IA Ativo"*
      * Botão à direita: `🔄 Resetar Simulação`

2.  **Área de Controle (Sidebar ou Drawer):**

      * Título: **Gerar Perfil de Consumo**
      * Botões Grandes (Cards clicáveis):
          * [🥦 **Modo Fit**]
          * [🍔 **Modo Junk**]
          * [🍣 **Modo Exótico**]
      * *Nota:* O formulário manual antigo fica colapsado em um "Opções Avançadas", caso ele queira testar algo específico.

3.  **Área de Insights (Abaixo dos botões ou Flutuante):**

      * Visual de "Terminal" (fundo escuro, letra verde/branca monospaced).
      * Mostra o log falso de raciocínio assim que ele clica.

4.  **Grid de Recomendações (Centro):**

      * Os cards de restaurantes reagem e se reordenam assim que o "Terminal" finaliza o processamento.

-----

## Ajustes nos Arquivos (Checklist Técnico)

### 1\. `frontend/src/data/simulationScenarios.ts` (Novo Arquivo)

Crie um arquivo estático com os dados para "enganar" a UI de forma inteligente.

```typescript
export const SCENARIOS = {
  FIT: {
    label: "Estilo de Vida Saudável",
    orders: [
      { restaurant: "Green House", items: ["Salada Caesar", "Suco Verde"], total: 45.0, category: "Saudável" },
      { restaurant: "Poke Life", items: ["Poke Salmão", "Água de Coco"], total: 60.0, category: "Japonesa" },
      { restaurant: "Roots", items: ["Wrap de Frango"], total: 30.0, category: "Lanches" }
    ],
    aiLogs: [
      "Detectando padrão de baixa caloria...",
      "Identificando preferência por ingredientes frescos...",
      "Cluster 'Saudável' ativado como prioritário."
    ]
  },
  JUNK: {
    label: "Fast Food Lover",
    orders: [ ... ],
    aiLogs: [
      "Alto teor calórico detectado...",
      "Preferência por Comfort Food validada...",
      "Priorizando hamburguerias e pizzarias."
    ]
  }
}
```

### 2\. `frontend/src/hooks/useSimulationRunner.ts` (Novo Hook)

Orquestra a "mágica".

  * Recebe o cenário escolhido.
  * Dispara o `loading`.
  * Itera sobre os `orders` do cenário e faz os POSTs para a API (para salvar no banco e a recomendação real funcionar).
  * Enquanto faz os POSTs, vai atualizando o estado `logs` para o componente de terminal exibir.
  * No final, invalida a query de recomendações para atualizar a tela.

### 3\. Atualização no `Dashboard.tsx`

  * Inserir o `DemoToolbar` (Reset + Toggle).
  * Inserir o `SimulationDrawer` (Botões de Persona + Terminal).

-----

## Por que isso é "Robusto e Moderno"?

1.  **Storytelling:** Você não mostra apenas dados; você conta uma história ("Veja como a IA pensa").
2.  **Interatividade:** O recrutador é ativo, mas com barreiras de proteção (botões prontos vs inputs manuais propensos a erro).
3.  **Polimento:** O uso de logs simulados ("fake logs") é uma técnica comum em demos de produtos SaaS enterprise para tornar tangível algoritmos invisíveis.

Aqui está o "Kit de Demonstração de IA" completo.

Ele consiste em três partes:

1.  **Os Dados (`simulationScenarios.ts`):** O "roteiro" que a IA vai seguir.
2.  **O Visual (`AIReasoningLog.tsx`):** O componente que faz a mágica visual acontecer.
3.  **A Lógica (`useSimulationRunner.ts`):** O hook que conecta os dois, enviando dados para a API e atualizando o terminal.

-----

### 1\. Dados dos Cenários

Crie este arquivo para centralizar a lógica das "Personas".

**Arquivo:** `frontend/src/data/simulationScenarios.ts`

```typescript
export type SimulationScenarioKey = 'FIT' | 'COMFORT' | 'EXPENSIVE';

export interface OrderPayload {
  restaurant_id?: string; // Opcional, o backend pode escolher aleatório se não passar
  restaurant_name_hint: string; // Para buscar ou criar mock
  items: string[];
  total_amount: number;
  category_hint: string;
}

export interface Scenario {
  id: SimulationScenarioKey;
  label: string;
  icon: string; // Emoji
  description: string;
  orders: OrderPayload[];
  aiLogs: string[];
}

export const SIMULATION_SCENARIOS: Record<SimulationScenarioKey, Scenario> = {
  FIT: {
    id: 'FIT',
    label: 'Vida Saudável',
    icon: '🥗',
    description: 'Simula um usuário focado em alimentação natural e low-carb.',
    orders: [
      { restaurant_name_hint: "Green Life", items: ["Salada Caesar", "Suco Detox"], total_amount: 45.0, category_hint: "Saudável" },
      { restaurant_name_hint: "Poke Wave", items: ["Poke Salmão sem Arroz"], total_amount: 62.0, category_hint: "Japonesa" },
      { restaurant_name_hint: "Natural Roots", items: ["Wrap de Frango", "Smoothie Proteico"], total_amount: 38.0, category_hint: "Lanches" }
    ],
    aiLogs: [
      "[DATA_INGESTION] Processando lote de 3 novos pedidos...",
      "[NLP_ANALYSIS] Termos extraídos: 'Salada', 'Detox', 'Proteico', 'Sem Arroz'.",
      "[SEMANTIC_MATCH] Forte correlação detectada com cluster: SAÚDE_BEM_ESTAR.",
      "[INFERENCE] Reduzindo score de 'Fast Food' (-45%).",
      "[INFERENCE] Aumentando score de 'Natural' e 'Japonesa' (+60%).",
      "[OPTIMIZATION] Recalculando ordenação da Home...",
      "[SUCCESS] Perfil 'FIT' atualizado com confiança de 98%."
    ]
  },
  COMFORT: {
    id: 'COMFORT',
    label: 'Comfort Food',
    icon: '🍔',
    description: 'Simula um usuário que prefere fast food e refeições calóricas.',
    orders: [
      { restaurant_name_hint: "Big Burger", items: ["X-Bacon Duplo", "Batata Grande"], total_amount: 55.0, category_hint: "Hamburgueria" },
      { restaurant_name_hint: "Pizza Express", items: ["Pizza Calabresa", "Coca-Cola 2L"], total_amount: 70.0, category_hint: "Pizza" },
      { restaurant_name_hint: "Doceria Mágica", items: ["Milkshake Chocolate", "Brownie"], total_amount: 35.0, category_hint: "Doces" }
    ],
    aiLogs: [
      "[DATA_INGESTION] Processando lote de 3 novos pedidos...",
      "[NLP_ANALYSIS] Termos extraídos: 'Bacon', 'Pizza', 'Chocolate', 'Duplo'.",
      "[SEMANTIC_MATCH] Identificado padrão: HIGH_CALORIE / COMFORT.",
      "[INFERENCE] Aumentando prioridade para categorias: Pizza, Hamburguer, Sobremesas.",
      "[CONTEXT_AWARE] Detectado possível consumo noturno ou fim de semana.",
      "[OPTIMIZATION] Ajustando vitrine para ofertas indulgentes.",
      "[SUCCESS] Perfil 'COMFORT' atualizado com confiança de 96%."
    ]
  },
  EXPENSIVE: {
    id: 'EXPENSIVE',
    label: 'Gourmet / Premium',
    icon: '🍷',
    description: 'Simula um usuário com ticket médio alto e gosto refinado.',
    orders: [
      { restaurant_name_hint: "Le Bistro", items: ["Risoto de Funghi", "Vinho Tinto"], total_amount: 180.0, category_hint: "Francesa" },
      { restaurant_name_hint: "Sushi Gold", items: ["Omakase", "Sake Premium"], total_amount: 250.0, category_hint: "Japonesa" },
      { restaurant_name_hint: "Steakhouse Prime", items: ["Ancho Angus", "Aspargos"], total_amount: 140.0, category_hint: "Carnes" }
    ],
    aiLogs: [
      "[DATA_INGESTION] Processando lote de 3 novos pedidos...",
      "[METRIC_ANALYSIS] Ticket médio calculado: R$ 190,00 (Alto Padrão).",
      "[NLP_ANALYSIS] Termos: 'Risoto', 'Omakase', 'Angus', 'Premium'.",
      "[INFERENCE] Filtrando restaurantes populares/econômicos.",
      "[INFERENCE] Priorizando selo 'Gourmet' e avaliações > 4.8.",
      "[OPTIMIZATION] Refinando recomendações para experiência premium.",
      "[SUCCESS] Perfil 'GOURMET' atualizado com confiança de 99%."
    ]
  }
};
```

-----

### 2\. O Componente Visual (`AIReasoningLog.tsx`)

Este componente simula um terminal. Usei `framer-motion` para suavidade, mas se não tiver instalado, pode usar CSS simples.

**Pré-requisito:** `npm install lucide-react` (ícones) e `framer-motion` (opcional, removi do código abaixo para simplificar e garantir que funcione direto, usando CSS puro para animação).

**Arquivo:** `frontend/src/components/features/AIReasoningLog.tsx`

```tsx
import React, { useEffect, useRef } from 'react';
import { Terminal, Cpu, Activity, CheckCircle2 } from 'lucide-react';

interface AIReasoningLogProps {
  logs: string[];
  isProcessing: boolean;
  isVisible: boolean;
}

export const AIReasoningLog: React.FC<AIReasoningLogProps> = ({ logs, isProcessing, isVisible }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll para o final quando novos logs chegam
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  if (!isVisible) return null;

  return (
    <div className="w-full max-w-md bg-slate-900 rounded-lg overflow-hidden shadow-2xl border border-slate-700 font-mono text-xs sm:text-sm my-4 transition-all duration-500 ease-in-out">
      {/* Header do Terminal */}
      <div className="bg-slate-800 px-4 py-2 flex items-center justify-between border-b border-slate-700">
        <div className="flex items-center gap-2">
          <Terminal size={16} className="text-purple-400" />
          <span className="text-slate-300 font-semibold">AI Neural Engine</span>
        </div>
        <div className="flex items-center gap-2">
          {isProcessing ? (
            <>
              <Activity size={14} className="text-yellow-400 animate-pulse" />
              <span className="text-yellow-400">Processing...</span>
            </>
          ) : logs.length > 0 ? (
            <>
              <CheckCircle2 size={14} className="text-green-400" />
              <span className="text-green-400">Idle</span>
            </>
          ) : (
            <span className="text-slate-500">Standby</span>
          )}
        </div>
      </div>

      {/* Corpo do Log */}
      <div 
        ref={scrollRef}
        className="h-64 overflow-y-auto p-4 space-y-2 scroll-smooth"
      >
        {logs.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-slate-600 gap-2">
            <Cpu size={32} className="opacity-20" />
            <p>Aguardando input de simulação...</p>
          </div>
        )}

        {logs.map((log, index) => {
          // Colorir partes do log para parecer técnico
          const isError = log.includes("ERROR");
          const isSuccess = log.includes("SUCCESS");
          const isData = log.includes("DATA");

          let colorClass = "text-slate-300";
          if (isError) colorClass = "text-red-400";
          else if (isSuccess) colorClass = "text-green-400 font-bold";
          else if (isData) colorClass = "text-blue-300";

          return (
            <div key={index} className={`${colorClass} animate-fade-in`}>
              <span className="opacity-50 mr-2">{new Date().toLocaleTimeString('pt-BR', {hour12: false})}</span>
              <span className="typing-effect">{log}</span>
            </div>
          );
        })}
        
        {isProcessing && (
          <div className="text-purple-400 animate-pulse">_</div>
        )}
      </div>
    </div>
  );
};
```

-----

### 3\. O Hook de Orquestração (`useSimulationRunner.ts`)

Este hook gerencia o tempo. Ele não joga os logs de uma vez; ele os adiciona sequencialmente para criar suspense.

**Arquivo:** `frontend/src/hooks/useSimulationRunner.ts`

```typescript
import { useState } from 'react';
import { SIMULATION_SCENARIOS, SimulationScenarioKey } from '../data/simulationScenarios';
// Importe aqui sua função de API real
// import { createOrder } from '../api/orders'; 

export const useSimulationRunner = (onSimulationComplete?: () => void) => {
  const [logs, setLogs] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const runScenario = async (scenarioKey: SimulationScenarioKey) => {
    setIsProcessing(true);
    setLogs([]); // Limpa logs anteriores
    
    const scenario = SIMULATION_SCENARIOS[scenarioKey];
    
    // Passo 1: Mostrar início
    addLog(`[SYSTEM] Iniciando protocolo de simulação: ${scenario.label}`);
    await delay(800);

    // Passo 2: Simular criação de pedidos (Loop fake + API real se quiser)
    for (const order of scenario.orders) {
      // TODO: Aqui você chamaria sua API real:
      // await createOrder({ ...order, is_simulation: true });
      
      addLog(`[API] POST /orders { item: "${order.items[0]}", value: ${order.total_amount} } - 201 Created`);
      await delay(400); // Pequeno delay entre pedidos para realismo
    }

    // Passo 3: Exibir logs da "IA" sequencialmente
    for (const aiLog of scenario.aiLogs) {
      await delay(Math.random() * 800 + 400); // Delay variável para parecer "pensamento"
      addLog(aiLog);
    }

    setIsProcessing(false);
    
    if (onSimulationComplete) {
      onSimulationComplete();
    }
  };

  const clearSimulation = () => {
    setLogs([]);
    setIsProcessing(false);
    // TODO: Chamar API de reset
    addLog("[SYSTEM] Memória de simulação limpa com sucesso.");
  };

  const addLog = (message: string) => {
    setLogs(prev => [...prev, message]);
  };

  // Utilitário de delay
  const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  return {
    logs,
    isProcessing,
    runScenario,
    clearSimulation
  };
};
```

-----

### 4\. Como Integrar no `Dashboard.tsx`

Agora, basta montar as peças na sua página principal.

```tsx
// Imports
import { useSimulationRunner } from '../hooks/useSimulationRunner';
import { AIReasoningLog } from '../components/features/AIReasoningLog';
import { SIMULATION_SCENARIOS, SimulationScenarioKey } from '../data/simulationScenarios';

// Dentro do componente Dashboard
const Dashboard = () => {
  const [isDemoMode, setIsDemoMode] = useState(false);
  
  // Hook runner
  const { logs, isProcessing, runScenario, clearSimulation } = useSimulationRunner(() => {
    // Callback chamado quando a simulação termina
    // Ex: refetchRecommendations();
    console.log("Simulação finalizada, atualizando recomendações...");
  });

  return (
    <div className="p-6">
      {/* Header com Toggle */}
      <div className="flex justify-between items-center mb-6">
        <h1>Restaurantes</h1>
        <button onClick={() => setIsDemoMode(!isDemoMode)}>
           {isDemoMode ? 'Sair do Modo Demo' : 'Modo Demo'}
        </button>
      </div>

      {/* ÁREA DE DEMO */}
      {isDemoMode && (
        <div className="mb-8 border border-indigo-200 bg-indigo-50 rounded-xl p-6">
          <div className="flex flex-col md:flex-row gap-6">
            
            {/* Coluna 1: Controles */}
            <div className="flex-1">
              <h3 className="text-lg font-bold text-indigo-900 mb-4">Gerar Perfil de Consumo</h3>
              <p className="text-sm text-indigo-700 mb-4">
                Selecione um arquétipo para treinar a IA instantaneamente:
              </p>
              
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {Object.values(SIMULATION_SCENARIOS).map((scenario) => (
                  <button
                    key={scenario.id}
                    disabled={isProcessing}
                    onClick={() => runScenario(scenario.id as SimulationScenarioKey)}
                    className="p-4 bg-white border border-indigo-200 rounded-lg hover:shadow-md transition-all text-left group disabled:opacity-50"
                  >
                    <div className="text-2xl mb-2">{scenario.icon}</div>
                    <div className="font-bold text-slate-800 group-hover:text-indigo-600">
                      {scenario.label}
                    </div>
                  </button>
                ))}
              </div>

              <button 
                onClick={clearSimulation}
                className="mt-4 text-xs text-red-500 hover:underline"
              >
                Resetar Memória da IA
              </button>
            </div>

            {/* Coluna 2: O Cérebro (Terminal) */}
            <div className="flex-1">
               <AIReasoningLog 
                 logs={logs} 
                 isProcessing={isProcessing} 
                 isVisible={true} 
               />
            </div>
          </div>
        </div>
      )}

      {/* Resto do Dashboard (Lista de Restaurantes) */}
      {/* ... */}
    </div>
  );
};
```

### Por que isso funciona?

1.  **Imediatismo:** O recrutador clica no botão "Vida Saudável" e vê *coisas acontecendo* (logs subindo, status piscando).
2.  **Transparência Simulada:** Os logs explicam *por que* a tela vai mudar ("Reduzindo score de Fast Food"), educando o recrutador sobre o valor do seu sistema.
3.  **Modernidade:** O design escuro do terminal contrasta com o app claro, dando uma sensação "High Tech".