# IMPLEMENTATION_PLAN_06 — Integridade Operacional e Maturidade V1 do ERP Geral

**Projeto:** ERP Geral  
**Repositório:** `marcelobarud/ERP-Geral`  
**Plano:** 06  
**Data-base:** 11/09/2026  
**Objetivo:** alinhar ambiente, código e banco; validar os fluxos reais ponta a ponta; corrigir lacunas de permissões e UX; consolidar consistência de produto; e concluir o ERP Geral como uma V1 funcionalmente madura, sem expandir o escopo com novos domínios.

---

## 1. Contexto

A auditoria de produto posterior ao `GOAL_05.md` identificou que o principal problema atual não é falta de domínio funcional, mas desalinhamento entre:

- código atual;
- backend em execução;
- banco PostgreSQL principal;
- experiência real do usuário.

Estado auditado:

- código com migrations até `20260911_0011`;
- banco principal `erp_geral` observado em `20260911_0001`;
- backend ativo na porta `8000` incompatível com o frontend atual;
- `/api/health` respondendo 200 mesmo com módulos de negócio quebrados;
- Comercial, Compras, Estoque, Financeiro, Relatórios e Módulos não validáveis no ambiente principal;
- suítes automatizadas aprovadas anteriormente em PostgreSQL descartável;
- grande parte das funcionalidades já existe em backend e frontend.

Classificação da auditoria:

> **AINDA NÃO** é V1 funcional em uso real.

Resultado recomendado:

> corrigir lacunas importantes antes de qualquer nova expansão.

---

## 2. Objetivo do Plano 06

Transformar:

```text
código funcional
+
testes automatizados
+
ambiente principal desalinhado
```

em:

```text
código atual
+
backend atual
+
PostgreSQL atual
+
fluxos ponta a ponta validados
+
UX coerente
+
permissões coerentes
+
health operacional confiável
=
V1 funcional
```

---

## 3. Princípios obrigatórios

### 3.1 Não expandir escopo

Durante este plano, NÃO criar novos grandes domínios.

Ficam fora:

- fiscal;
- NF-e;
- SPED;
- folha;
- contabilidade;
- CRM;
- multiempresa completa;
- multi-tenant SaaS;
- BI avançado;
- integrações bancárias automáticas;
- marketplace;
- e-commerce;
- WMS;
- APIs públicas genéricas;
- webhooks generalizados.

### 3.2 Corrigir antes de polir

Ordem obrigatória:

```text
Ambiente
↓
Fluxos reais
↓
Erros/permissões
↓
Consistência
↓
Relatórios/acabamento
↓
Gate V1
```

### 3.3 Código, backend e banco devem representar a mesma versão

O sistema não pode ser considerado saudável quando o processo responde, mas o schema está atrasado.

### 3.4 Health deve representar saúde operacional

O health deve detectar pelo menos:

- processo backend;
- banco acessível;
- schema/migration compatível.

### 3.5 Backend continua autoridade

UX sensível a permissões não substitui autorização backend.

### 3.6 Não refazer fundações saudáveis

Preservar:

- layout;
- sistema visual;
- sidebar;
- componentes CRUD;
- paginação;
- filtros;
- branding;
- editor visual;
- campos personalizados;
- proteção backend;
- cadeia Alembic;
- estrutura modular.

---

## 4. Fases do Plano 06

| Fase | Nome | Prioridade | Objetivo |
|---|---|---:|---|
| 0 | Integridade do ambiente | P0 | Alinhar código, backend, banco e health |
| 1 | Smoke tests e correções de fluxo | P0 | Validar e corrigir cenários ponta a ponta |
| 2 | Erros, autenticação e permissões | P1 | Tornar operação e segurança coerentes na UI |
| 3 | Consistência de produto e navegação | P1 | Remover ambiguidades e consolidar UX |
| 4 | Relatórios, responsividade e acessibilidade | P2 | Refinar acabamento funcional |
| 5 | Gate de maturidade V1 | P0 final | Auditar novamente e classificar a V1 |

---

# 5. Fase 0 — Integridade do ambiente

**Status:** CONCLUÍDA em 11/09/2026  
**Commit esperado:** `fix: alinha ambiente principal ao estado atual do ERP`

## Objetivo

Garantir que frontend, backend e banco principal local executem a mesma versão.

### 5.1 Preflight

Identificar:

- processo backend;
- PID;
- porta;
- comando;
- diretório de execução;
- frontend;
- URL da API;
- banco;
- revision Alembic.

Não encerrar processo desconhecido sem confirmar origem.

### 5.2 Backend correto

Garantir que o backend ativo venha do repositório atual.

Se houver processo antigo:

- identificar;
- encerrar com segurança;
- iniciar versão atual.

### 5.3 Banco principal local

Antes de migrar:

1. confirmar banco;
2. confirmar ambiente local;
3. realizar backup se houver dados relevantes;
4. executar `alembic current`;
5. executar `alembic history`;
6. confirmar caminho até o head atual.

Aplicar migrations pendentes somente no banco correto.

Não usar `stamp` para simular aplicação.

### 5.4 Preflight de schema

Criar mecanismo para detectar incompatibilidade de schema no startup ou health.

Preferência:

- comparar revision atual com head esperado;
- marcar estado degradado ou impedir operação de forma explícita.

### 5.5 Health operacional

Separar, quando apropriado:

```text
process
database
schema
```

O frontend não deve mostrar “API online” como sinônimo de sistema saudável se banco/schema estiverem quebrados.

### 5.6 Frontend

Confirmar:

- URL correta;
- backend correto;
- ausência de endpoint legado.

### 5.7 Smoke técnico mínimo

Validar:

- health;
- auth/config;
- modules;
- dashboard/reports;
- clientes;
- produtos;
- vendas;
- compras;
- estoque;
- financeiro.

### 5.8 Documentação

Atualizar:

- README;
- AI_CONTEXT;
- instruções locais;
- migrations;
- health/preflight.

## Critérios de aceite

- backend atual em execução;
- banco no head atual;
- health detecta banco/schema;
- módulos deixam de falhar por incompatibilidade;
- frontend aponta para API atual;
- Git limpo após commit.

### Evidências da fase

- backup lógico local criado antes da migração;
- banco `erp_geral` atualizado de `20260911_0001` para `20260911_0011`;
- backend atual reiniciado em `127.0.0.1:8000`;
- health validado com processo, banco e schema separados;
- endpoints técnicos e de negócio principais respondendo;
- backend: 118 testes aprovados no PostgreSQL de teste;
- frontend: 77 testes aprovados, typecheck e lint aprovados;
- `ruff check app` aprovado;
- `ruff check .` continua apontando 53 linhas longas preexistentes em migrations históricas.

---

# 6. Fase 1 — Smoke tests e correções de fluxo

**Status:** CONCLUÍDA em 11/09/2026  
**Commit esperado:** `fix: valida e corrige fluxos ponta a ponta do ERP`

## Objetivo

Executar no ambiente principal local os fluxos que a auditoria anterior não conseguiu validar.

Usar dados claramente artificiais.

### 6.1 Cenário A — Venda

```text
Cliente
↓
Produto
↓
Orçamento
↓
Pedido
↓
Venda
↓
Saída de estoque
↓
Conta a receber
↓
Liquidação
```

Validar:

- vínculos;
- status;
- valores;
- estoque;
- financeiro;
- auditoria;
- idempotência.

### 6.2 Cenário B — Compra

```text
Fornecedor
↓
Produto
↓
Pedido de compra
↓
Recebimento parcial
↓
Recebimento final
↓
Entrada de estoque
↓
Conta a pagar
↓
Pagamento
```

Validar:

- recebimento acumulado;
- saldo pendente;
- histórico de custo;
- estoque;
- financeiro;
- auditoria.

### 6.3 Regra de contas a pagar

A auditoria identificou geração de obrigação financeira em `create_receipt`, antes de `confirm_receipt`.

Reavaliar e corrigir.

Default recomendado:

> obrigação automática nasce na confirmação efetiva do recebimento.

Garantir:

- recebimento não confirmado não gera obrigação definitiva;
- confirmação gera uma única vez;
- idempotência;
- cancelamento/reversão coerentes.

### 6.4 Cenário C — Devolução

```text
Venda
↓
Devolução parcial
↓
Estoque
↓
Histórico
```

### 6.5 Cenário D — Inventário

```text
Saldo
↓
Inventário
↓
Contagem
↓
Diferença
↓
Confirmação
↓
Ajuste
↓
Novo saldo
```

### 6.6 Cenário E — Módulos

```text
Ativo
↓
Desativado
↓
Menu
↓
Rota direta
↓
API
↓
Reativado
```

### 6.7 Cenário F — Segurança operacional

Validar:

- login;
- logout;
- sessão válida;
- sessão inválida/expirada;
- usuário ativo;
- usuário inativo;
- acesso permitido;
- acesso negado.

### 6.8 Regressões

Criar testes automatizados para bugs encontrados.

## Critérios de aceite

Cenários A–F concluídos sem inconsistência de dados.

## Evidências da execução

- cenário A executado com orçamento, pedido, venda, conta a receber, saída de
  estoque e liquidação;
- cenário B executado com recebimentos parcial e final, entradas de estoque,
  histórico de custo e títulos a pagar criados somente na confirmação;
- confirmação repetida de recebimento permaneceu idempotente, sem duplicar
  movimento ou obrigação financeira;
- cenário C executado com devolução parcial aprovada e entrada compensatória no
  estoque;
- cenário D executado com inventário confirmado e ajuste de saldo;
- cenário E validado com desativação temporária de Relatórios, bloqueio visual
  da rota direta, API preservada sob autenticação/permissões e restauração do
  módulo;
- cenário F coberto pela suíte de autenticação e autorização, incluindo
  administrador, operador, usuário inativo, login inválido, logout e acesso
  negado;
- backend PostgreSQL: `118 passed`;
- frontend: `77 passed`, lint, typecheck e build aprovados;
- `ruff check app` e `git diff --check` aprovados.

O produto ficou com dados artificiais de validação identificáveis no banco
principal; nenhum dado existente foi removido.

---

# 7. Fase 2 — Erros, autenticação e permissões

**Status:** CONCLUÍDA em 11/09/2026  
**Commit esperado:** `feat: melhora permissões e tratamento de erros do ERP`

## Objetivo

Alinhar experiência do usuário às regras backend.

### 7.1 Erros no frontend

Distinguir:

- backend indisponível;
- 401;
- 403;
- 404;
- 409;
- 422;
- 500;
- schema/health degradado.

Evitar mensagem genérica para toda falha.

### 7.2 Mensagens de domínio

Não expor:

- `IntegrityError`;
- SQL;
- FK violation;
- stack trace;
- detalhes sensíveis.

### 7.3 UI sensível a papéis

Consumir papel/permissões atuais.

Ações incompatíveis devem ser:

- ocultadas quando apropriado;
- ou desabilitadas com explicação.

Backend continua sendo autoridade.

### 7.4 Administração de usuários

Criar tela baseada nas APIs existentes.

Escopo mínimo:

- listar;
- criar quando suportado;
- ativar/inativar;
- alterar papel;
- visualizar vínculo com funcionário quando existir.

Não criar IAM complexo.

### 7.5 Permissões

Se roles forem fixas, não inventar permission builder genérico.

### 7.6 Sessão

Revisar UX de:

- login;
- logout;
- expiração;
- 401;
- revogação.

### 7.7 Rotas diretas

Validar:

- sem login;
- sem permissão;
- módulo desativado;
- entidade inexistente.

## Critérios de aceite

Usuário entende por que uma ação falhou e a UI não oferece sistematicamente ações incompatíveis.

## Evidências da execução

- mensagens HTTP foram diferenciadas por indisponibilidade, sessão inválida,
  falta de permissão, entidade inexistente, conflito, validação e falha do
  servidor;
- detalhes técnicos de banco, SQL, stack trace e violações de constraint são
  substituídos por mensagens seguras;
- 401 com token existente limpa a sessão local, emite o evento de expiração e
  devolve a aplicação à tela de login;
- Configurações → Usuários foi implementado sobre as APIs existentes, com
  listagem, criação, edição de papel, vínculo com funcionário e ativação ou
  inativação;
- a navegação de Usuários é sensível ao papel atual, mantendo o backend como
  autoridade para autorização;
- a suíte de autenticação validou administrador, operador, login inválido,
  usuário inativo, logout, acesso sem token e acesso negado;
- frontend: `79 passed`, typecheck, build e lint aprovados (lint mantém apenas
  avisos preexistentes de efeitos React).

---

# 8. Fase 3 — Consistência de produto e navegação

**Status:** CONCLUÍDA em 11/09/2026
**Commit esperado:** `refactor: consolida navegação e consistência do ERP`

## Objetivo

Eliminar ambiguidades e consolidar padrões.

### 8.1 Dashboard

Resolver sobreposição entre Dashboard operacional e Dashboard ERP.

Preferência:

> um Dashboard principal com visão ERP modular.

### 8.2 Vendas x Comercial

Eliminar ambiguidade.

Estrutura preferencial:

```text
Comercial
├── Orçamentos
├── Pedidos
├── Vendas
└── Devoluções
```

### 8.3 IDs técnicos

Substituir exibição dominante de IDs por nomes reconhecíveis.

### 8.4 Categorias e unidades

Expor claramente em Cadastros, Configurações ou submenu de Produtos.

### 8.5 Configurações

Agrupar de forma coerente.

Exemplo conceitual:

```text
Sistema
├── Módulos
├── Usuários
└── Permissões

Operação
├── Depósitos
├── Condições de pagamento
├── Categorias
└── Unidades

Personalização
├── Aparência
└── Campos personalizados
```

### 8.6 Padrões de tela

Alinhar:

- cabeçalhos;
- botões;
- filtros;
- tabelas;
- detalhes;
- formulários;
- modais;
- confirmações;
- estados vazios.

### 8.7 Formatação

Padronizar:

- moeda;
- quantidade;
- datas;
- horários;
- percentuais;
- status;
- documentos.

### 8.8 Nomenclatura

Remover:

- inglês desnecessário;
- labels técnicas;
- termos legados de CRM;
- pluralização inconsistente.

## Critérios de aceite

Navegação e telas equivalentes seguem padrões previsíveis.

### Evidências da execução

- o menu foi consolidado em uma única área `Comercial`, com Nova venda,
  Vendas, Orçamentos, Pedidos e Devoluções;
- a entrada duplicada `Vendas comerciais` foi removida do menu, mantendo a
  rota direta existente para compatibilidade;
- as listas de Comercial e Compras passaram a exibir nomes de clientes e
  fornecedores, usando o identificador técnico somente como fallback;
- cabeçalhos, ações, filtros, tabelas, detalhes e estados vazios foram
  preservados em um padrão coerente entre telas equivalentes;
- frontend: `79 passed`, typecheck e build aprovados.

---

# 9. Fase 4 — Relatórios, responsividade e acessibilidade

**Status:** CONCLUÍDA em 11/09/2026
**Commit esperado:** `fix: refina relatórios responsividade e acessibilidade`

## Objetivo

Concluir acabamento funcional.

### 9.1 Identificadores visuais

Relatórios não devem compartilhar indevidamente o mesmo `pageId`.

### 9.2 Relatórios

Revisar:

- filtros;
- período;
- estado vazio;
- totalizadores;
- data de atualização quando útil;
- exportação.

CSV pode permanecer.

Adicionar XLSX apenas se houver infraestrutura razoável.

### 9.3 Mobile

Validar aproximadamente:

- 360px;
- tablet;
- desktop.

Priorizar:

- sidebar/drawer;
- tabelas;
- filtros;
- formulários;
- modais;
- financeiro;
- estoque;
- relatórios.

### 9.4 Menu mobile

Reduzir densidade se necessário.

### 9.5 Acessibilidade

Corrigir:

- IDs duplicados;
- `aria-label`;
- foco;
- teclado;
- labels;
- headings;
- contraste necessário.

### 9.6 Performance percebida

Revisar requests duplicados e carregamentos.

Otimizar somente com evidência.

## Critérios de aceite

Sem bloqueadores de mobile/acessibilidade nos fluxos principais.

### Evidências da execução

- cada relatório passou a usar um `pageId` visual próprio, com a migration
  `20260911_0012` aplicada no banco principal e no banco de testes;
- os relatórios mantiveram filtros, exportação CSV e totalizadores, além de
  apresentar estado vazio real quando não há dados;
- os controles de período permanecem rotulados e os botões de ação seguem
  acessíveis por teclado;
- a estrutura responsiva cobre sidebar/drawer, filtros, tabelas, formulários
  e modais nos breakpoints de mobile, tablet e desktop;
- backend: `120 passed`; frontend: `79 passed`, typecheck e build aprovados;
- health principal: `ok`, banco `ok`, schema `ok`, migration atual e esperada
  em `20260911_0012`.

---

# 10. Fase 5 — Gate de maturidade V1

**Status:** EM ANDAMENTO
**Commit esperado:** `chore: consolida marco funcional v1 do ERP`

## Objetivo

Reexecutar auditoria prática final e decidir se o ERP Geral pode ser tratado como V1 funcional.

Esta fase não deve introduzir nova feature relevante.

### 10.1 Ambiente

Confirmar:

- backend;
- banco;
- migration head;
- health;
- frontend.

### 10.2 Fluxos obrigatórios

#### Venda

```text
Cliente → Orçamento → Pedido → Venda → Estoque → A receber → Liquidação
```

#### Compra

```text
Fornecedor → Pedido → Recebimento parcial/final → Estoque → A pagar → Pagamento
```

#### Devolução

```text
Venda → Devolução → Estoque
```

#### Inventário

```text
Inventário → Diferença → Ajuste
```

#### Permissões

Ao menos dois papéis.

#### Módulos

Ativar/desativar + menu + rota + API.

### 10.3 UX essencial

Validar:

- mensagens;
- navegação;
- nomes;
- dashboard;
- configurações;
- mobile.

### 10.4 Suítes

Executar backend, frontend, migrations, lint e build.

### 10.5 Classificação final

Usar apenas:

```text
SIM
SIM, COM AJUSTES
AINDA NÃO
```

Para encerrar o Plano 06 com sucesso, mínimo esperado:

> **SIM, COM AJUSTES**

Se permanecer `AINDA NÃO`, documentar bloqueadores reais.

### 10.6 Marco V1

Se aprovado:

- atualizar README;
- atualizar AI_CONTEXT;
- registrar marco V1.

Não criar tag, release ou deploy sem autorização explícita.

---

# 11. Testes obrigatórios por fase

## Backend

```bash
pytest
ruff check .
```

ou equivalentes reais.

## Frontend

```bash
npm test
npm run lint
npm run typecheck
npm run build
```

ou equivalentes reais.

## PostgreSQL

Quando aplicável:

- migrations;
- constraints;
- testes transacionais.

## Geral

```bash
git diff --check
git status
```

---

# 12. Dados de teste

Usar registros artificiais, por exemplo:

```text
Cliente Teste Plano 06
Fornecedor Teste Plano 06
Produto Teste Plano 06
```

Não usar CPF/CNPJ reais.

Não apagar dados existentes.

---

# 13. Migrations

Criar somente quando necessária para problema real.

Nunca editar migration histórica aplicada.

---

# 14. Commits previstos

```text
Fase 0
fix: alinha ambiente principal ao estado atual do ERP

Fase 1
fix: valida e corrige fluxos ponta a ponta do ERP

Fase 2
feat: melhora permissões e tratamento de erros do ERP

Fase 3
refactor: consolida navegação e consistência do ERP

Fase 4
fix: refina relatórios responsividade e acessibilidade

Fase 5
chore: consolida marco funcional v1 do ERP
```

---

# 15. Documentação obrigatória

Ao final de cada fase:

- atualizar `AI_CONTEXT.md`;
- atualizar este plano;
- atualizar README quando necessário;
- registrar migrations;
- registrar configurações;
- registrar limitações reais.

---

# 16. Fora de escopo

Continuam fora:

- novo grande módulo;
- fiscal;
- NF-e;
- SPED;
- contabilidade;
- folha;
- CRM;
- multiempresa completa;
- SaaS multi-tenant;
- BI avançado;
- integrações bancárias automáticas;
- WMS;
- marketplace;
- e-commerce.

---

# 17. Definition of Done

O Plano 06 estará concluído quando:

- ambiente principal estiver alinhado;
- banco estiver no head correto;
- health detectar incompatibilidade;
- fluxos A–F funcionarem no ambiente principal;
- geração financeira estiver no momento correto;
- UI respeitar permissões;
- administração de usuários existir;
- dashboards não forem ambíguos;
- navegação estiver consolidada;
- IDs técnicos não dominarem a UX;
- relatórios estiverem coerentes;
- mobile/acessibilidade não tiverem bloqueadores;
- suítes estiverem verdes;
- auditoria final classificar o ERP no mínimo como **SIM, COM AJUSTES**;
- Git estiver limpo.
