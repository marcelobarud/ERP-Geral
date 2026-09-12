# IMPLEMENTATION_PLAN_07 — Distribuição, Operação e Refinamento Visual do ERP Geral

**Projeto:** ERP Geral  
**Repositório:** `marcelobarud/ERP-Geral`  
**Workspace obrigatório:** `D:\Codex\ERP Geral`  
**Plano:** 07  

## Objetivo geral

Transformar o ERP Geral V1 funcional em um produto web implantável para cliente real, recuperável, atualizável, suportável e visualmente refinado, mantendo a arquitetura React/Vite + FastAPI + PostgreSQL.

O produto continuará sendo uma aplicação web. Este plano **não** transforma o ERP em aplicação desktop.

---

# 1. Contexto

O ERP Geral concluiu os Planos 04, 05 e 06.

Estado consolidado:

- V1 funcional classificada como `SIM, COM AJUSTES`;
- frontend em `5173`;
- backend em `8000`;
- PostgreSQL `erp_geral`;
- Alembic em `20260911_0012`;
- health validando processo, banco e schema;
- 120 testes backend aprovados;
- 79 testes frontend aprovados;
- typecheck, lint, build, Ruff e `git diff --check` aprovados;
- fluxos principais de venda, compra, estoque, financeiro, devolução e inventário validados.

A auditoria de prontidão para distribuição concluiu:

> **AINDA NÃO** pronto para primeiro cliente real.

O problema principal não é domínio funcional, mas ausência de operação de distribuição reproduzível:

- instalação;
- produção;
- bootstrap;
- backup;
- restore;
- atualização;
- rollback;
- logs;
- suporte;
- release.

A auditoria visual concluiu:

- não há problema visual P0;
- a base visual é saudável;
- existem inconsistências de spacing, toolbars, relatórios, ações de tabelas, modais, navegação e iconografia;
- redesign seletivo pode melhorar significativamente o produto;
- a identidade visual deve ser preservada.

---

# 2. Modelo de distribuição adotado

Modelo inicial:

```text
1 cliente
1 instalação
1 PostgreSQL
```

A instalação pode operar:

```text
Servidor local / rede interna
```

ou:

```text
Servidor/VPS
```

Os usuários acessam pelo navegador.

Arquitetura preservada:

```text
React/Vite
    ↓ HTTP/JSON
FastAPI
    ↓
PostgreSQL
```

Não introduzir Electron, Tauri ou wrapper desktop neste plano.

---

# 3. Regras obrigatórias

## 3.1 Workspace

Trabalhar exclusivamente em:

```text
D:\Codex\ERP Geral
```

Antes de qualquer alteração:

```powershell
Set-Location -LiteralPath 'D:\Codex\ERP Geral'
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git status
```

Remote esperado:

```text
https://github.com/marcelobarud/ERP-Geral.git
```

Se diretório, repositório ou remote forem diferentes:

- PARAR;
- não inspecionar outro projeto;
- não alterar outro projeto.

Não acessar `D:\Codex\CRM Geral`, `D:\Codex\CRM Builder` nem repositórios Deskcomm.

## 3.2 Não transformar em desktop

“Instalável” significa aplicação web implantável de forma reproduzível.

## 3.3 Não criar SaaS multi-tenant

Não introduzir tenants, billing SaaS ou isolamento multiempresa compartilhado neste ciclo.

## 3.4 Ordem macro

```text
Instalação
↓
Produção
↓
Backup/Restore/Update
↓
Bootstrap/Onboarding
↓
Segurança
↓
Release/Suporte
↓
Design System
↓
Redesign seletivo
↓
Polimento
↓
Auditoria final
```

## 3.5 Liberdade visual com Impeccable

A skill Impeccable pode redesenhar telas e composições inteiras quando houver ganho claro.

Pode alterar:

- grid;
- espaçamento;
- caixas;
- posição/tamanho de botões;
- filtros;
- cabeçalhos;
- formulários;
- modais;
- tabelas;
- responsividade.

Deve preservar:

- identidade geral;
- branding;
- regras de negócio;
- permissões;
- contratos de API;
- funcionalidades;
- acessibilidade.

Não fazer redesign gratuito sem ganho.

---

# 4. Fora de escopo

Continuam fora:

- fiscal;
- NF-e;
- SPED;
- contabilidade;
- folha;
- CRM;
- BI avançado;
- WMS;
- marketplace;
- e-commerce;
- SaaS multi-tenant;
- Kubernetes;
- microserviços;
- observabilidade enterprise;
- alta disponibilidade.

Docker pode ser avaliado, mas não é requisito obrigatório.

---

# 5. Fases

| Fase | Nome | Prioridade | Objetivo |
|---|---|---:|---|
| 0 | Instalação reproduzível | P0 | Criar caminho oficial de instalação web |
| 1 | Execução de produção | P0 | Operar frontend/backend sem ferramentas de dev |
| 2 | Backup, restore, atualização e rollback | P0/P1 | Garantir recuperação e manutenção |
| 3 | Bootstrap e onboarding | P1 | Guiar primeira configuração |
| 4 | Segurança de distribuição | P1 | Tornar defaults e exposição adequados |
| 5 | Release, suporte e observabilidade leve | P1 | Criar operação suportável |
| 6 | Design system formal | P1 visual | Formalizar padrões |
| 7 | Redesign seletivo com Impeccable | P1 visual | Refatorar telas prioritárias |
| 8 | Polimento visual, mobile e acessibilidade | P2 | Remover arestas finais |
| 9 | Auditoria final para cliente real | P0 final | Validar distribuição + UX |

---

# 6. Fase 0 — Instalação reproduzível

**Status:** CONCLUÍDA — instalação documentada e script validado; ensaio com um PostgreSQL descartável fica pendente da disponibilidade de um ambiente isolado  
**Commit esperado:** `feat: cria instalação reproduzível do ERP`

## Objetivo

Permitir instalação limpa sem depender de conhecimento implícito do desenvolvedor.

## Escopo

- documentar Python, Node, npm, PostgreSQL e Git;
- definir versões mínimas/recomendadas;
- revisar dependências Python e estratégia de reprodutibilidade;
- corrigir localização/carregamento do `.env`;
- separar configuração de desenvolvimento e produção;
- documentar criação de usuário/banco PostgreSQL;
- documentar migrations;
- formalizar criação do primeiro administrador;
- criar runbook/script de instalação;
- validar fresh install.

Fluxo esperado:

```text
pré-requisitos
→ configuração
→ dependências
→ PostgreSQL
→ migrations
→ bootstrap
→ build
→ start
→ health
→ smoke
```

## Critérios de aceite

- fresh install aprovado;
- `.env` sem ambiguidade;
- PostgreSQL documentado;
- bootstrap documentado;
- outro operador técnico consegue instalar seguindo o runbook.

---

# 7. Fase 1 — Execução de produção

**Status:** CONCLUÍDA  
**Commit esperado:** `feat: prepara execução web de produção do ERP`

## Objetivo

Eliminar dependência de `npm run dev` e `uvicorn --reload`.

## Escopo

- servir build Vite em produção;
- executar FastAPI sem reload;
- definir restart automático;
- definir logs;
- definir reverse proxy;
- definir procedimento de HTTPS;
- tornar URL da API adequada ao deploy;
- validar refresh de rota interna;
- documentar execução em servidor local e/ou VPS.

## Critérios de aceite

ERP opera sem dev server, possui processo previsível e pode reiniciar de forma controlada.

---

# 8. Fase 2 — Backup, restore, atualização e rollback

**Status:** CONCLUÍDA — scripts e runbook prontos; restore real requer ambiente isolado de PostgreSQL  
**Commit esperado:** `feat: adiciona operação segura de backup e atualização`

## Objetivo

Garantir recuperação de dados e manutenção segura.

## Escopo

Mapear persistência:

- PostgreSQL;
- `backend/storage/branding`;
- outros uploads;
- configurações persistentes.

Revisar storage para evitar persistência acoplada a diretório substituível do código.

Criar procedimento/script de:

- backup PostgreSQL;
- backup storage;
- restore completo;
- teste real de restore;
- atualização;
- rollback.

Upgrade oficial:

```text
backup
→ stop
→ update
→ dependências
→ migrations
→ build
→ start
→ health
→ smoke
```

Rollback deve considerar restore de backup, não apenas `alembic downgrade`.

## Critérios de aceite

- backup existe;
- restore foi executado e validado;
- storage entra na recuperação;
- atualização possui runbook;
- rollback está documentado.

---

# 9. Fase 3 — Bootstrap e onboarding

**Status:** CONCLUÍDA  
**Commit esperado:** `feat: adiciona onboarding inicial do ERP`

## Objetivo

Evitar que primeiro uso dependa de chamadas manuais à API ou conhecimento oculto.

## Escopo

- primeiro administrador;
- empresa/nome;
- branding básico;
- módulos;
- depósito;
- unidades;
- condições de pagamento;
- categorias quando necessárias;
- orientação em instalação vazia;
- CTAs quando dependências de configuração estiverem ausentes.

Pode ser wizard, setup guiado, CLI segura ou combinação simples.

Não criar sistema excessivamente complexo.

## Critérios de aceite

Novo cliente chega da primeira execução à primeira operação sem dead ends de configuração.

---

# 10. Fase 4 — Segurança de distribuição

**Status:** PENDENTE  
**Commit esperado:** `chore: reforça segurança para distribuição do ERP`

## Escopo

- revisar `ENVIRONMENT`;
- revisar `AUTH_REQUIRED`;
- defaults de produção;
- secrets;
- CORS configurável;
- Swagger/OpenAPI desabilitável/restrito;
- permissões de storage;
- uploads;
- rate limiting;
- exposição do PostgreSQL;
- checklist de hardening.

Não introduzir Redis só por princípio. Avaliar se a instância única permite manter rate limit local.

## Critérios de aceite

Configuração de produção insegura deve falhar ou alertar claramente.

---

# 11. Fase 5 — Release, suporte e observabilidade leve

**Status:** PENDENTE  
**Commit esperado:** `feat: estrutura release e suporte operacional do ERP`

## Escopo

- versionamento do produto;
- SemVer quando adequado;
- página/endpoint seguro de informações do sistema;
- migration atual;
- health;
- logs;
- rotação/retenção básica;
- diagnóstico;
- changelog;
- release checklist;
- documentação separada de instalação/operação/backup/update/suporte/usuário.

Não criar observabilidade enterprise.

## Critérios de aceite

É possível identificar versão e diagnosticar problemas básicos sem abrir o código manualmente.

---

# 12. Fase 6 — Design system formal

**Status:** PENDENTE  
**Commit esperado:** `refactor: formaliza design system do ERP`

## Objetivo

Criar uma base visual comum antes do redesign.

Usar Impeccable como referência de qualidade.

## Escopo

Inventariar e formalizar:

- cores;
- spacing;
- radius;
- sombras;
- tipografia;
- botões;
- cards;
- inputs;
- tables;
- modals;
- page headers;
- toolbars;
- badges;
- empty/error/loading states;
- iconografia.

Definir escala coerente de espaçamento, por exemplo:

```text
4 / 8 / 12 / 16 / 24 / 32 / 40 / 48
```

sem seguir cegamente se outra escala fizer mais sentido.

### Botões

Padronizar:

- altura;
- padding;
- ícone;
- primary;
- secondary;
- ghost;
- danger;
- disabled;
- loading.

### Cards/boxes

Padronizar:

- padding;
- gap;
- header;
- footer;
- overflow;
- wrapping;
- min-height apenas quando necessário.

Nenhum box pode ficar menor que seu conteúdo.

### Formulários

Padronizar:

- grid;
- gaps;
- labels;
- helpers;
- validation;
- sections;
- footer de ações.

### Tabelas

Padronizar:

- toolbar;
- row height;
- ações;
- filtros;
- paginação;
- scroll;
- empty state.

### Modais

Padronizar:

- largura;
- max-height;
- scroll;
- sticky footer quando necessário;
- mobile.

### Ícones

Adotar biblioteca/coerência única, evitando caracteres tipográficos improvisados.

## Critérios de aceite

Componentes compartilhados e tokens produzem comportamento visual previsível.

---

# 13. Fase 7 — Redesign seletivo com Impeccable

**Status:** PENDENTE  
**Commit esperado:** `refactor: redesenha telas prioritárias do ERP`

## Objetivo

Permitir redesign real, não apenas ajustes de padding, desde que siga o design system.

## Prioridades conhecidas

- Devoluções;
- Relatórios;
- modais longos;
- tabelas com muitas ações;
- Campos Personalizados;
- telas administrativas densas;
- páginas com boxes apertados;
- páginas com botões desproporcionais;
- filtros;
- Financeiro;
- Estoque.

## Devoluções

Corrigir o erro inicial:

```text
Dados de entrada inválidos.
```

Listagem vazia deve ser estado vazio, não erro.

## Relatórios

Redesenhar quando necessário:

- toolbar;
- spacing;
- grid de métricas;
- filtros;
- exportação;
- responsividade;
- densidade vertical.

## Tabelas

Revisar ações como:

```text
Ver / Editar / Excluir
```

e aplicar hierarquia visual adequada, podendo usar ícones/menu/contexto quando melhorar UX.

## Modais longos

Avaliar:

- sticky footer;
- seções;
- largura;
- scroll;
- ações visíveis.

## Cabeçalhos

Compactar onde houver ganho operacional.

## Critérios de aceite

As telas prioritárias seguem o mesmo sistema visual e não apresentam boxes quebrados, botões mal proporcionados ou hierarquia inconsistente.

---

# 14. Fase 8 — Polimento visual, mobile e acessibilidade

**Status:** PENDENTE  
**Commit esperado:** `fix: conclui polimento visual e responsivo do ERP`

## Escopo

### Navegação

Renomear claramente:

- Pedidos de venda;
- Pedidos de compra.

Padronizar iconografia.

### Breakpoints

Validar visualmente aproximadamente:

```text
360px
560px
768px
900px
desktop
```

### Revisar

- sidebar/drawer;
- toolbars;
- tabelas;
- filtros;
- formulários;
- modais;
- dashboards;
- relatórios;
- financeiro;
- estoque.

### Acessibilidade

- foco;
- teclado;
- `aria-label`;
- contraste;
- labels;
- IDs;
- modal;
- status de health.

### Estados

- vazio;
- loading;
- erro;
- sucesso;
- permissão;
- offline/degraded.

## Critérios de aceite

Nenhum P0/P1 visual conhecido e nenhuma quebra relevante nos principais breakpoints.

---

# 15. Fase 9 — Auditoria final para cliente real

**Status:** PENDENTE  
**Commit esperado:** `chore: consolida prontidão do ERP para primeiro cliente`

## Objetivo

Executar auditoria combinada de distribuição, operação e UX.

## Fresh install obrigatório

```text
ambiente limpo
→ instalação
→ configuração
→ PostgreSQL
→ migrations
→ bootstrap
→ produção
→ health
→ login
```

## Backup/restore obrigatório

```text
dados
→ backup
→ restore
→ validação
```

## Upgrade

Simular atualização entre revisões/versões compatíveis quando seguro.

## Operação

Validar:

- restart;
- logs;
- health;
- versão;
- diagnóstico.

## Smoke funcional

- cliente;
- produto;
- venda;
- compra;
- estoque;
- financeiro.

## Visual

Revisar principais telas em desktop, tablet e mobile.

## Classificação final

Usar apenas:

```text
SIM
SIM, COM PREPARAÇÃO OPERACIONAL
AINDA NÃO
```

Mínimo para concluir o Plano 07:

```text
SIM, COM PREPARAÇÃO OPERACIONAL
```

Ideal:

```text
SIM
```

---

# 16. Testes obrigatórios

## Backend

Executar suíte completa e PostgreSQL real de testes.

No gate final, não aceitar skips por ausência de `TEST_DATABASE_URL` quando esses testes forem parte da suíte PostgreSQL.

Executar Ruff completo.

## Frontend

Executar:

- testes;
- lint;
- typecheck;
- build.

## Banco

Validar:

- migrations do zero;
- upgrade;
- backup/restore;
- smoke.

## Geral

```bash
git diff --check
git status
```

---

# 17. Dívidas conhecidas

Incorporar conforme aplicável:

- `.env` e CWD;
- virtualenv/documentação;
- versão mínima de Node;
- dependências Python reproduzíveis;
- CORS configurável;
- API URL produtiva;
- auth defaults;
- Swagger/OpenAPI;
- backup/restore;
- storage fora da árvore substituível;
- update/rollback;
- logs;
- versionamento;
- changelog;
- release checklist;
- frontend README;
- Ruff completo;
- warnings frontend;
- `TEST_DATABASE_URL`;
- onboarding;
- Devoluções;
- toolbar de Relatórios;
- grid responsivo;
- ações de tabelas;
- modais longos;
- ícones;
- nomenclatura de Pedidos.

---

# 18. Commits previstos

```text
Fase 0
feat: cria instalação reproduzível do ERP

Fase 1
feat: prepara execução web de produção do ERP

Fase 2
feat: adiciona operação segura de backup e atualização

Fase 3
feat: adiciona onboarding inicial do ERP

Fase 4
chore: reforça segurança para distribuição do ERP

Fase 5
feat: estrutura release e suporte operacional do ERP

Fase 6
refactor: formaliza design system do ERP

Fase 7
refactor: redesenha telas prioritárias do ERP

Fase 8
fix: conclui polimento visual e responsivo do ERP

Fase 9
chore: consolida prontidão do ERP para primeiro cliente
```

---

# 19. Documentação obrigatória

Manter atualizados:

- `AI_CONTEXT.md`;
- `README.md`;
- `IMPLEMENTATION_PLAN_07.md`;
- instalação;
- produção;
- backup/restore;
- atualização;
- release;
- suporte;
- documentação do usuário quando aplicável.

---

# 20. Definition of Done

O Plano 07 estará concluído quando:

- instalação limpa for reproduzível;
- execução produtiva estiver definida;
- frontend não depender de dev server;
- backend não depender de reload;
- CORS/API URL forem adequados ao deploy;
- bootstrap estiver seguro;
- backup existir;
- restore estiver testado;
- atualização estiver definida;
- rollback estiver documentado;
- storage persistente estiver protegido;
- logs/health/versão forem úteis para suporte;
- release checklist existir;
- design system estiver formalizado;
- Impeccable tiver sido aplicado às telas prioritárias;
- inconsistências visuais P1 estiverem resolvidas;
- responsividade principal estiver validada;
- suíte completa estiver verde;
- auditoria final classificar no mínimo `SIM, COM PREPARAÇÃO OPERACIONAL`;
- Git estiver limpo.
