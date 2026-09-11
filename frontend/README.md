# Frontend do ERP Geral

Frontend administrativo construído com React, TypeScript e Vite.

## Desenvolvimento

```bash
npm install
npm run dev
```

O frontend usa `http://127.0.0.1:8000` como URL padrão do backend. Para
configurar outro endereço, copie `.env.example` para `.env.local` e ajuste:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Qualidade

```bash
npm run lint
npm run typecheck
npm run build
```

## Organização atual

- `src/app`: roteamento leve e estado técnico da aplicação;
- `src/components`: layout, navegação e estados compartilhados;
- `src/features`: páginas separadas por área da V1;
- `src/pages`: páginas transversais, como endereço não encontrado;
- `src/services`: cliente HTTP centralizado;
- `src/types`: contratos TypeScript usados pelo frontend.

As áreas de cadastros e vendas estão como placeholders nesta etapa. Os CRUDs e
a interface operacional de vendas serão implementados nas fases seguintes.
