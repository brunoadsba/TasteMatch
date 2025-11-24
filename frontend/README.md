# TasteMatch - Frontend

Frontend do TasteMatch desenvolvido com React + Vite + TypeScript + Shadcn/UI.

## Estrutura do Projeto

```
frontend/
├── src/
│   ├── assets/           # Imagens, logos (padrão do Vite)
│   ├── components/       
│   │   ├── ui/           # Componentes do Shadcn (Button, Input, Card)
│   │   └── features/     # Componentes de negócio (RestaurantCard, ProtectedRoute)
│   ├── hooks/            # Custom hooks (useAuth, useRecommendations)
│   ├── lib/              # Cliente API (api.ts) e utils.ts do Shadcn
│   ├── pages/            # Telas (Login, Dashboard)
│   ├── types/            # Interfaces TypeScript
│   ├── App.tsx           # Rotas e configuração principal
│   └── main.tsx          # Entry point
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Instalação

```bash
cd frontend
npm install
```

## Configuração

Crie um arquivo `.env` na raiz do projeto frontend:

```env
VITE_API_URL=http://localhost:8000
```

## Executar

```bash
npm run dev
```

O frontend estará disponível em `http://localhost:5173`

## Funcionalidades Implementadas

- ✅ Autenticação (Login/Registro)
- ✅ Dashboard com recomendações
- ✅ Listagem de restaurantes recomendados
- ✅ Cards de restaurantes com insights
- ✅ Integração com API backend
- ✅ Proteção de rotas
- ✅ Interface responsiva com Shadcn/UI

## Tecnologias

- **React 19**: Biblioteca UI
- **Vite**: Build tool
- **TypeScript**: Tipagem estática
- **Shadcn/UI**: Componentes UI
- **Tailwind CSS**: Estilização
- **React Router**: Roteamento
- **Axios**: Cliente HTTP
- **Lucide React**: Ícones
