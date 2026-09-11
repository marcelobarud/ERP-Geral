# IMPLEMENTATION_PLAN_04 — Evolução do ERP Geral

**Projeto:** ERP Geral  
**Repositório:** `marcelobarud/ERP-Geral`  
**Plano:** 04  
**Data-base:** 11/09/2026  
**Objetivo:** evoluir a fundação administrativa-transacional atual para um ERP genérico, modular e coerente, preservando o que já funciona e evitando expansão prematura para fiscal, contabilidade ou CRM.

---

## 1. Contexto e decisão de produto

O projeto anteriormente chamado **CRM Geral** foi oficialmente reposicionado como **ERP Geral**.

O produto deve ser tratado como uma plataforma genérica de gestão administrativa e operacional. O **CRM será um produto separado** e não deve ser reincorporado ao ERP por conveniência.

O ERP Geral já possui uma base funcional relevante:

- clientes;
- produtos;
- fornecedores;
- funcionários;
- vendas;
- itens de venda;
- preços históricos;
- fornecedor histórico por item;
- buscas e filtros;
- dashboard administrativo;
- campos personalizados;
- branding;
- personalização visual;
- FastAPI;
- SQLAlchemy;
- Alembic;
- PostgreSQL;
- React;
- TypeScript;
- Vite;
- testes frontend e backend.

A evolução deve aproveitar essa base, sem reescrever o produto do zero.

---

## 2. Princípios obrigatórios

### 2.1 Venda continua sendo transação final

`Venda` não deve virar orçamento, pedido ou oportunidade.

A semântica oficial será:

```text
Orçamento
    ↓ conversão
Pedido de venda
    ↓ conclusão/faturamento operacional
Venda
```

- **Orçamento:** proposta comercial, sem efeitos definitivos.
- **Pedido:** compromisso operacional/comercial.
- **Venda:** transação concluída e histórica.

### 2.2 Estoque é baseado em movimentações

Não implementar controle principal por simples mutação de um campo como:

```text
produto.estoque -= quantidade
```

A fonte de verdade deve ser uma estrutura de movimentações rastreáveis.

### 2.3 Histórico não deve ser destruído

Documentos transacionais consolidados não devem desaparecer por exclusão física comum.

Preferir:

- cancelamento;
- reversão;
- estorno;
- devolução;
- trilha de auditoria.

### 2.4 Funcionário e usuário são conceitos diferentes

- **Funcionário:** pessoa do domínio operacional da empresa.
- **Usuário:** identidade autenticada capaz de operar o sistema.

Eles podem se relacionar, mas não devem ser a mesma entidade por conveniência.

### 2.5 Regras de negócio pertencem ao backend

Frontend não é fonte de autoridade para:

- permissões;
- totais;
- integridade;
- estoque;
- status;
- transições;
- cancelamentos;
- financeiro.

### 2.6 Dinheiro e quantidade continuam exatos

Preservar uso de `Decimal`/`NUMERIC`.

Não utilizar ponto flutuante binário em valores monetários ou quantidades do domínio.

### 2.7 Personalização existente é patrimônio do produto

Preservar:

- branding;
- aparência;
- editor visual;
- campos personalizados;
- filtros;
- responsividade;
- componentes reutilizáveis.

Novas páginas devem integrar-se aos mecanismos existentes em vez de criar uma segunda linguagem visual.

### 2.8 Um produto-base para múltiplos clientes

Diferenças comuns entre clientes devem ser resolvidas preferencialmente por:

1. configuração;
2. módulos;
3. campos personalizados;
4. permissões;
5. extensões específicas somente quando realmente inevitáveis.

Não criar forks permanentes por cliente como estratégia padrão.

### 2.9 Modularidade sem microserviços prematuros

O ERP pode crescer por domínios internos bem separados, mantendo a aplicação atual.

Não introduzir microserviços, mensageria distribuída ou infraestrutura complexa sem necessidade concreta.

---

## 3. Fora de escopo deste plano

Este plano **não** deve implementar neste momento:

- CRM;
- leads;
- oportunidades;
- funil comercial de CRM;
- WhatsApp Inbox;
- campanhas;
- marketing;
- NF-e;
- NFS-e;
- NFC-e;
- SPED;
- escrituração fiscal;
- contabilidade;
- folha de pagamento;
- MRP;
- manufatura;
- logística avançada;
- marketplace;
- e-commerce próprio;
- integração bancária automática;
- conciliação bancária avançada;
- multiempresa completo;
- arquitetura SaaS multi-tenant;
- BI avançado;
- data warehouse.

Esses itens podem ser tratados em planos futuros.

---

# 4. Legenda de status

Cada fase deste documento possui um campo `Status`.

Valores permitidos:

- `PENDENTE`
- `EM ANDAMENTO`
- `CONCLUÍDA`
- `BLOQUEADA`

O executor deve alterar apenas o status da fase que estiver executando.

---

# 5. Visão geral das fases

| Fase | Nome | Prioridade | Objetivo principal |
|---|---|---:|---|
| 0 | Fundação ERP | P0 | Preparar ciclo transacional, histórico, paginação e agregações |
| 1 | Segurança e auditoria | P0 | Criar autenticação, usuários, papéis e trilha mínima |
| 2 | Catálogo ERP | P0 | Estruturar produto para estoque, compras e pedidos |
| 3 | Comercial | P1 | Adicionar orçamento e pedido sem deformar Venda |
| 4 | Fundação de estoque | P1 | Criar movimentações, saldo, ajustes e inventário |
| 5 | Compras e recebimentos | P1 | Criar pedido de compra e entrada operacional |
| 6 | Integração operacional e devoluções | P1 | Integrar vendas/compras ao estoque com reversões |
| 7 | Financeiro | P2 | Contas a pagar/receber, parcelas, liquidações e caixa |
| 8 | Relatórios e dashboard ERP | P2 | Consolidar indicadores e relatórios dos novos domínios |
| 9 | Modularidade por cliente | P2 | Consolidar ativação de módulos e configuração genérica |

---

# 6. Fase 0 — Fundação ERP

**Status:** CONCLUÍDA
**Commit esperado:** `refactor: prepara fundação transacional do ERP`

## Objetivo

Eliminar dívidas que ficariam caras depois da criação de pedidos, estoque, compras e financeiro.

## Escopo

### 6.1 Ciclo de vida da venda

Adicionar um ciclo de vida explícito para vendas sem transformar `Venda` em pedido.

Estado mínimo recomendado:

- `CONCLUIDA`
- `CANCELADA`

Regras:

- novas vendas continuam sendo criadas como concluídas;
- venda concluída pode ser cancelada conforme regra explícita;
- não permitir exclusão física comum de venda consolidada pela interface/API pública;
- cancelamento deve preservar `Venda` e `VendaItem`;
- registrar data de cancelamento e motivo opcional;
- preparar estrutura para futura reversão de efeitos operacionais.

Se existir endpoint de exclusão, substituir o fluxo funcional por cancelamento. Qualquer exclusão administrativa excepcional deve ser explicitamente separada e protegida.

### 6.2 Timestamps

Adicionar de forma consistente, quando ainda ausentes:

- `created_at`;
- `updated_at`.

Priorizar entidades operacionais principais.

Não reescrever migrations históricas. Criar nova migration.

### 6.3 Observações

Adicionar campo de observação à venda se não existir.

### 6.4 Paginação

Listagens operacionais não devem carregar indefinidamente todos os registros.

Criar paginação backend-driven para:

- clientes;
- fornecedores;
- funcionários;
- produtos;
- vendas.

Preservar:

- busca;
- filtros;
- ordenação existente;
- semântica AND atual.

Definir contrato consistente:

```text
items
page
page_size
total
total_pages
```

ou equivalente coerente com o projeto.

### 6.5 Dashboard agregado

Criar endpoint próprio para indicadores.

Não buscar listas inteiras apenas para contar registros.

O endpoint deve calcular no backend pelo menos os indicadores atualmente apresentados.

### 6.6 Efeito colateral em GET de aparência

Revisar a criação automática da configuração padrão durante `GET`.

Sempre que tecnicamente viável:

- leitura deve permanecer leitura;
- inicialização/default deve ocorrer de maneira explícita ou idempotente sem surpresa operacional.

Não quebrar instalações existentes.

## Backend

- migration;
- models;
- schemas;
- services;
- rotas;
- regras transacionais;
- paginação;
- agregações.

## Frontend

- atualização das tabelas/listagens para paginação;
- estados de loading/erro/vazio;
- cancelamento de venda;
- status;
- observações;
- dashboard usando endpoint agregado.

## Testes mínimos

- venda cancelada permanece consultável;
- itens permanecem preservados;
- exclusão física comum deixa de ocorrer pelo fluxo público;
- paginação respeita filtros;
- total da paginação é correto;
- dashboard não depende de carregar listas;
- timestamps são gerados corretamente;
- migração upgrade/downgrade em banco descartável quando disponível.

## Critério de aceite

A base deve estar pronta para receber novos documentos transacionais sem depender de exclusões destrutivas ou listagens ilimitadas.

### Resultado da execução

- migration `20260911_0002_erp_foundation` criada com upgrade/downgrade;
- vendas passaram a usar `CONCLUIDA`/`CANCELADA`, com motivo, data e preservação do histórico;
- timestamps foram adicionados às entidades operacionais principais;
- clientes, fornecedores, funcionários, produtos e vendas passaram a usar paginação backend-driven;
- dashboard passou a usar endpoint agregado;
- leitura de aparência deixou de persistir configuração padrão;
- frontend integrado ao novo contrato, com testes, build e estados de paginação/cancelamento;
- suíte PostgreSQL não executada nesta máquina por ausência de `TEST_DATABASE_URL`.

---

# 7. Fase 1 — Segurança e auditoria

**Status:** CONCLUÍDA
**Commit esperado:** `feat: adiciona segurança e auditoria operacional`

## Objetivo

Preparar o ERP para uso real por múltiplas pessoas antes que o domínio cresça.

## Escopo

### 7.1 Usuários

Criar entidade de usuário separada de funcionário.

Campos mínimos:

- id;
- nome;
- email/login único;
- senha armazenada com hash seguro;
- ativo;
- role;
- timestamps.

### 7.2 Papéis

Começar simples.

Papéis mínimos sugeridos:

- `ADMIN`
- `MANAGER`
- `OPERATOR`

Antes de implementar, confirmar que esses papéis atendem às operações existentes.

A autorização deve ser backend-first.

### 7.3 Autenticação

Implementar mecanismo seguro e coerente com FastAPI.

Requisitos:

- credenciais nunca em texto puro;
- sessão/token com expiração;
- logout;
- proteção das APIs operacionais;
- tratamento de usuário inativo;
- CORS coerente;
- segredo configurável por ambiente.

Registrar a decisão técnica em documentação/ADR se necessário.

### 7.4 Matriz de permissões

Definir permissões mínimas por operação.

Exemplo conceitual:

- leitura;
- criação;
- edição;
- cancelamento;
- configurações;
- gestão de usuários.

Evitar espalhar `if role == ...` sem política central.

### 7.5 Auditoria mínima

Criar log append-only para ações críticas, inicialmente:

- login relevante;
- criação/alteração de usuários;
- mudança de papel;
- cancelamento de venda;
- alteração de configurações sensíveis;
- operações transacionais futuras.

Registrar:

- usuário;
- ação;
- entidade;
- id da entidade;
- data/hora;
- metadata segura.

Não gravar senha, token ou segredo.

### 7.6 Funcionário x usuário

Permitir vínculo opcional entre usuário e funcionário quando fizer sentido.

Não exigir que todo funcionário tenha login.

Não exigir que todo usuário seja funcionário.

## Testes mínimos

- autenticação válida/inválida;
- usuário inativo;
- autorização por papel;
- endpoint protegido;
- impossibilidade de confiar em papel enviado pelo frontend;
- auditoria de operação crítica;
- segredo ausente em produção deve falhar de forma segura.

## Gate operacional

A partir desta fase, nenhuma nova rota mutável de módulo operacional deve ser criada sem autenticação/autorização compatível, salvo se o projeto estiver explicitamente executando em modo de desenvolvimento controlado.

### Resultado da execução

- migration `20260911_0003_security_audit` criada com usuários, sessões e logs;
- autenticação por token assinado, expiração, revogação e logout implementada;
- senhas armazenadas com PBKDF2 e nunca em texto puro;
- papéis `ADMIN`, `MANAGER` e `OPERATOR` e matriz central de permissões
  aplicados às rotas operacionais;
- bootstrap seguro do primeiro administrador disponível;
- auditoria de login, logout, usuários, cancelamento de venda e aparência;
- frontend integrado com login, sessão persistida e logout;
- em produção, secrets ausentes ou fracos fazem a configuração falhar;
- suíte PostgreSQL não executada nesta máquina por ausência de
  `TEST_DATABASE_URL`.

---

# 8. Fase 2 — Catálogo ERP

**Status:** CONCLUÍDA
**Commit esperado:** `feat: expande catálogo operacional do ERP`

## Objetivo

Preparar produtos para estoque, compras, pedidos e relatórios.

## 8.1 Produto

Adicionar/normalizar:

- SKU/código interno único;
- código de barras opcional;
- unidade de medida;
- ativo/inativo;
- estoque mínimo;
- categoria estruturada.

Preservar:

- preço de custo;
- preço de venda;
- fornecedor existente;
- campos personalizados.

### 8.2 Unidades de medida

Criar catálogo próprio simples.

Exemplos:

- UN;
- KG;
- G;
- L;
- ML;
- M;
- M²;
- CX.

Não criar motor complexo de conversão de unidades nesta fase, salvo necessidade já existente.

### 8.3 Categorias estruturadas

Substituir gradualmente categoria textual livre por entidade estruturada.

Migração deve preservar dados existentes.

Evitar perda de categorias atuais.

### 8.4 Produto ativo/inativo

Produto inativo:

- continua aparecendo em histórico;
- não deve entrar em novas operações por padrão.

### 8.5 Múltiplos fornecedores

Criar relação produto-fornecedor separada.

Possíveis campos:

- fornecedor;
- produto;
- código do fornecedor;
- custo de referência;
- fornecedor preferencial;
- ativo.

Se hoje existir `supplier_id` em produto, migrar com compatibilidade e sem apagar a semântica atual antes da nova relação estar validada.

### 8.6 Histórico de custo

Preparar registro histórico de custos sem substituir o snapshot histórico já existente em `VendaItem`.

## Testes mínimos

- SKU único;
- barcode opcional;
- produto inativo não entra em operação nova;
- categorias legadas preservadas;
- unidade obrigatória conforme decisão de domínio;
- múltiplos fornecedores;
- fornecedor preferencial único por produto quando aplicável.

## Resultado da execução

Implementado na migration `20260911_0004`: SKU único com geração compatível,
código de barras opcional, unidades de medida catalogadas, categorias
estruturadas com preservação da categoria textual legada, produto ativo/inativo,
estoque mínimo, relação produto-fornecedor com fornecedor preferencial único e
histórico de custos. Produtos inativos são rejeitados em novas vendas, enquanto
o snapshot histórico de `VendaItem` permanece preservado. A relação do
fornecedor atual continua sincronizada com o catálogo novo.

Validação local: `41 passed`, `60 skipped` por ausência de
`TEST_DATABASE_URL`; Ruff, testes estruturais, lint, typecheck e build do
frontend aprovados. Os testes PostgreSQL reais não foram declarados como
aprovados nesta máquina.

---

# 9. Fase 3 — Comercial: orçamento e pedido de venda

**Status:** CONCLUÍDA
**Commit esperado:** `feat: adiciona orçamentos e pedidos de venda`

## Objetivo

Criar camada comercial pré-venda sem transformar `Venda` em documento genérico.

## 9.1 Orçamento

Entidades próprias:

- orçamento;
- itens do orçamento.

Campos mínimos:

- número/identificador;
- cliente;
- funcionário responsável quando aplicável;
- itens;
- quantidade;
- preço;
- desconto/acréscimo quando definido;
- validade;
- observações;
- status;
- timestamps.

Estados mínimos:

- `RASCUNHO`
- `ENVIADO`
- `APROVADO`
- `RECUSADO`
- `EXPIRADO`
- `CANCELADO`

### 9.2 Pedido de venda

Entidades próprias:

- pedido;
- itens do pedido.

Estados mínimos:

- `RASCUNHO`
- `CONFIRMADO`
- `CONCLUIDO`
- `CANCELADO`

Avaliar nomenclatura final no código mantendo PT-BR na UI.

### 9.3 Conversões

Fluxos:

```text
Orçamento aprovado
        ↓
Pedido de venda
```

e:

```text
Pedido confirmado/concluído
        ↓
Venda
```

Conversões devem:

- copiar snapshots necessários;
- evitar duplicação acidental;
- preservar vínculo com documento de origem;
- ser idempotentes quando aplicável.

### 9.4 Descontos, acréscimos e frete

Definir modelagem explícita.

Não armazenar apenas total final sem explicar sua composição.

### 9.5 Formas e condições de pagamento

Criar catálogo operacional simples suficiente para pedidos e futura integração financeira.

Não criar ainda liquidação financeira completa.

### 9.6 Exportação/impressão

Fornecer uma saída apresentável de orçamento/pedido utilizando mecanismo simples e sustentável.

Evitar motor de templates excessivamente complexo nesta fase.

## Regra importante

Orçamento e pedido **não movimentam estoque definitivamente** nesta fase.

Reserva poderá ser planejada depois.

## Testes mínimos

- estados válidos;
- transições inválidas bloqueadas;
- orçamento converte uma única vez de forma controlada;
- pedido gera venda corretamente;
- venda mantém snapshots históricos;
- valores monetários exatos;
- cancelamento preserva histórico.

## Resultado da execução

Implementadas as entidades próprias de condições de pagamento, orçamento,
itens de orçamento, pedido de venda e itens de pedido na migration
`20260911_0005`. Os itens preservam snapshots de produto, SKU, fornecedor,
quantidade e preço; descontos, acréscimos e frete permanecem discriminados no
documento. As transições de status são validadas, a conversão de orçamento
aprovado para pedido é idempotente e a conversão de pedido confirmado/concluído
para venda preserva os preços históricos. Foram adicionadas rotas de consulta,
criação, transição, conversão e impressão HTML.

Validação local: `43 passed`, `61 skipped` por ausência de `TEST_DATABASE_URL`;
Ruff e validações estruturais aprovados. A suíte PostgreSQL real não foi
declarada como aprovada nesta máquina.

---

# 10. Fase 4 — Fundação de estoque

**Status:** CONCLUÍDA
**Commit esperado:** `feat: adiciona controle de estoque por movimentações`

## Objetivo

Criar estoque rastreável, baseado em eventos operacionais.

## 10.1 Depósitos

Começar com suporte simples.

Criar entidade de depósito/local de estoque com um depósito padrão.

Isso permite evolução futura sem exigir múltiplos depósitos na UX inicial.

## 10.2 Movimentação de estoque

Criar entidade append-oriented.

Campos mínimos:

- produto;
- depósito;
- tipo;
- quantidade;
- data;
- origem;
- documento de origem;
- usuário responsável;
- observação;
- chave/idempotência quando necessária.

Tipos iniciais:

- `ENTRADA`
- `SAIDA`
- `AJUSTE_ENTRADA`
- `AJUSTE_SAIDA`
- `DEVOLUCAO_ENTRADA`
- `DEVOLUCAO_SAIDA`
- `REVERSAO`

Nomenclatura pode ser refinada.

## 10.3 Saldo

Saldo deve ser calculável a partir das movimentações.

Se for criado cache/materialização de saldo por desempenho:

- movimentações permanecem fonte de verdade;
- atualização deve ser transacional;
- criar testes de reconciliação.

## 10.4 Estoque negativo

Definir configuração explícita.

Default recomendado:

- impedir saída que gere saldo negativo.

Se existir opção de permitir:

- deve ser configuração administrativa explícita;
- operação deve permanecer auditável.

## 10.5 Ajustes

Permitir ajuste manual com:

- motivo obrigatório;
- usuário;
- data;
- quantidade;
- sentido.

## 10.6 Inventário

Criar inventário simples:

- contagem;
- diferença;
- confirmação;
- geração de ajuste.

## 10.7 Estoque mínimo

Utilizar campo definido no catálogo para sinalizações.

## Fora desta fase

- lote;
- validade;
- serial;
- endereço logístico;
- picking;
- WMS;
- reserva avançada.

## Testes mínimos

- saldo por movimentações;
- concorrência/transação;
- estoque negativo;
- ajuste;
- inventário;
- reversão;
- integridade de origem.

## Resultado da execução

Implementada a migration `20260911_0006` com depósito padrão, configuração
explícita de saldo negativo, movimentações append-oriented, reversões por
movimento de origem e inventário com confirmação. O saldo é calculado a partir
dos eventos, saídas são bloqueadas quando gerariam saldo negativo por padrão,
chaves de idempotência evitam duplicações e o estoque mínimo do catálogo é
exposto nas consultas de saldo.

Validação local: `45 passed`, `62 skipped` por ausência de `TEST_DATABASE_URL`;
Ruff e validações estruturais aprovados. A suíte PostgreSQL real não foi
declarada como aprovada nesta máquina.

---

# 11. Fase 5 — Compras e recebimentos

**Status:** CONCLUÍDA
**Commit esperado:** `feat: adiciona compras e recebimentos`

## Objetivo

Criar processo de aquisição conectado a fornecedores, produtos e estoque.

## 11.1 Pedido de compra

Entidades:

- pedido de compra;
- itens.

Campos mínimos:

- fornecedor;
- número;
- status;
- itens;
- quantidades;
- custos;
- previsão;
- observação;
- timestamps.

Estados sugeridos:

- `RASCUNHO`
- `EMITIDO`
- `PARCIALMENTE_RECEBIDO`
- `RECEBIDO`
- `CANCELADO`

## 11.2 Recebimento

Recebimento deve ser entidade/registro próprio.

Permitir:

- recebimento total;
- recebimento parcial;
- divergência de quantidade;
- custo efetivo;
- data;
- responsável.

## 11.3 Estoque

Recebimento confirmado gera `ENTRADA` de estoque.

Reprocessamento não pode duplicar entrada.

## 11.4 Histórico de custo

Recebimentos alimentam histórico de custo do produto.

Avaliar cálculo de custo médio somente após base transacional correta.

## 11.5 Cotação

Cotação de compra não é obrigatória nesta fase.

Pode ser backlog P2 caso não seja necessária para o fluxo principal.

## Testes mínimos

- pedido parcial;
- recebimento total;
- entrada de estoque idempotente;
- cancelamento antes/depois de recebimento conforme regras;
- custo histórico;
- fornecedor/produto íntegros.

## Resultado da execução

Implementados pedidos de compra, itens com snapshot de produto e custo,
recebimentos parciais ou totais e confirmação transacional. A confirmação gera
uma entrada idempotente no depósito padrão, atualiza a quantidade recebida,
avança o status do pedido e registra o custo no histórico de produtos. Pedidos
com recebimento não podem ser cancelados sem uma operação compensatória futura.

Validação local: `47 passed`, `63 skipped` por ausência de `TEST_DATABASE_URL`;
Ruff e validações estruturais aprovados. A suíte PostgreSQL real não foi
declarada como aprovada nesta máquina.

---

# 12. Fase 6 — Integração operacional e devoluções

**Status:** CONCLUÍDA
**Commit esperado:** `feat: integra vendas compras e estoque`

## Objetivo

Fechar o ciclo entre documentos e estoque.

## 12.1 Venda → estoque

Ao consolidar venda:

- gerar saída de estoque;
- executar de forma transacional;
- impedir duplicação;
- validar saldo conforme política.

## 12.2 Cancelamento de venda

Venda com efeito em estoque não pode simplesmente apagar saída.

Deve gerar reversão compensatória quando permitido.

## 12.3 Devolução de venda

Criar documento/registro de devolução.

Permitir devolução:

- total;
- parcial;
- por item;
- com motivo.

Devolução aprovada pode gerar entrada de estoque conforme condição do item.

## 12.4 Compra → estoque

Garantir que apenas recebimento confirmado gere entrada.

Cancelamentos/reversões devem gerar movimentos compensatórios, não apagar histórico.

## 12.5 Idempotência

Toda integração documento → estoque deve ser protegida contra execução duplicada.

## Testes mínimos

- venda gera saída única;
- cancelamento gera reversão correta;
- devolução parcial;
- recebimento gera entrada única;
- saldo final reconciliado;
- falha no meio da transação não deixa documento e estoque divergentes.

## Resultado da execução

Implementada a postagem explícita de vendas no estoque com idempotência,
reversão compensatória automática no cancelamento e devoluções parciais ou
totais com aprovação. Devoluções aprovadas geram entradas de estoque e a
quantidade devolvida é limitada ao snapshot vendido. As integrações usam o
depósito padrão, mantêm os eventos históricos e não apagam movimentos.

Validação local: `49 passed`, `64 skipped` por ausência de `TEST_DATABASE_URL`;
Ruff e validações estruturais aprovados. A suíte PostgreSQL real não foi
declarada como aprovada nesta máquina.

---

# 13. Fase 7 — Financeiro

**Status:** PENDENTE  
**Commit esperado:** `feat: adiciona gestão financeira do ERP`

## Objetivo

Adicionar financeiro operacional sem entrar em contabilidade formal ou integração bancária avançada.

## 13.1 Estruturas base

Criar:

- categorias financeiras;
- contas/caixas;
- formas de pagamento;
- condições de pagamento quando aplicável.

## 13.2 Contas a receber

Venda pode gerar títulos a receber.

Suportar:

- parcela única;
- parcelamento;
- vencimento;
- valor;
- status;
- cliente;
- origem;
- pagamentos parciais quando definido.

Estados:

- `ABERTO`
- `PARCIAL`
- `PAGO`
- `VENCIDO`
- `CANCELADO`

## 13.3 Contas a pagar

Compra/recebimento pode gerar títulos a pagar.

Relacionar:

- fornecedor;
- documento de origem;
- vencimentos;
- parcelas;
- liquidações.

## 13.4 Pagamentos e recebimentos

Não sobrescrever saldo do título arbitrariamente.

Criar registros de liquidação.

Permitir reversão controlada.

## 13.5 Caixa

Registrar entradas e saídas financeiras confirmadas.

Evitar contabilidade de dupla entrada nesta fase.

## 13.6 Fluxo de caixa

Distinguir:

- realizado;
- previsto.

## 13.7 Inadimplência

Derivar de títulos vencidos e não liquidados.

## Fora desta fase

- OFX;
- PIX automático;
- CNAB;
- boleto bancário;
- Open Finance;
- conciliação automática;
- DRE contábil formal.

## Testes mínimos

- parcelamento exato;
- pagamentos parciais;
- reversão;
- título vencido;
- origem em venda/compra;
- fluxo previsto/realizado;
- valores decimais exatos.

---

# 14. Fase 8 — Relatórios e dashboard ERP

**Status:** PENDENTE  
**Commit esperado:** `feat: adiciona relatórios gerenciais do ERP`

## Objetivo

Transformar os dados consolidados em informação gerencial sem criar uma camada de BI excessiva.

## Relatórios mínimos

### Comercial

- vendas por período;
- vendas por cliente;
- vendas por produto;
- vendas por funcionário;
- cancelamentos;
- devoluções.

### Compras

- compras por período;
- compras por fornecedor;
- custos por produto;
- recebimentos pendentes.

### Estoque

- saldo atual;
- produtos abaixo do mínimo;
- movimentações;
- ajustes;
- inventários.

### Financeiro

- contas a pagar;
- contas a receber;
- vencidos;
- fluxo de caixa;
- realizado x previsto.

## Dashboard

Evoluir o dashboard de forma modular.

Não exibir métrica sem fonte de dados confiável.

Priorizar queries agregadas no backend.

Evitar carregar coleções inteiras para calcular KPI no browser.

## Exportação

Adicionar CSV/XLSX apenas se coerente com as dependências e padrões do projeto.

PDF deve ser limitado a documentos que realmente precisem de apresentação formal.

---

# 15. Fase 9 — Modularidade por cliente

**Status:** PENDENTE  
**Commit esperado:** `feat: adiciona configuração modular do ERP`

## Objetivo

Consolidar o ERP Geral como um produto-base único adaptável a clientes diferentes.

## 15.1 Módulos ativos

Criar configuração para ativação/visibilidade de módulos como:

- comercial;
- compras;
- estoque;
- financeiro;
- relatórios.

Regra:

**desabilitar módulo na interface não é autorização.**

Backend deve continuar protegendo operações.

## 15.2 Navegação

Menu deve refletir módulos ativos e permissões.

Evitar menu enorme.

## 15.3 Configurações por cliente

Centralizar, quando fizer sentido:

- branding;
- labels;
- campos personalizados;
- módulos;
- regras operacionais simples;
- formas de pagamento;
- categorias.

## 15.4 Extensões

Documentar regra:

- configuração quando possível;
- feature geral quando reutilizável;
- módulo quando domínio isolável;
- extensão específica somente para demanda realmente exclusiva.

Não criar branches permanentes por cliente como arquitetura de produto.

---

# 16. Segurança transversal

Além da Fase 1, todas as fases devem respeitar:

1. autorização backend-first;
2. validação de input;
3. ORM/queries parametrizadas;
4. proteção contra mass assignment;
5. transações para efeitos múltiplos;
6. idempotência quando um efeito puder repetir;
7. CORS restrito por configuração;
8. secrets fora do código;
9. uploads validados;
10. auditoria de operações críticas;
11. erros sem vazamento de informação sensível.

---

# 17. Estratégia de migrations

Para toda alteração de schema:

- criar nova migration Alembic;
- nunca editar migration histórica já aplicada;
- migrations devem preservar dados existentes;
- preencher novos campos de forma segura;
- `downgrade` deve ser implementado quando razoável e seguro;
- mudanças destrutivas exigem justificativa explícita;
- validar em banco descartável quando credenciais de teste estiverem disponíveis.

---

# 18. Estratégia de testes

Cada fase deve adicionar cobertura proporcional ao risco.

## Backend

Cobrir:

- regras de domínio;
- validações;
- autorização;
- transições;
- integrações entre documentos;
- idempotência;
- migrations quando possível.

## Frontend

Cobrir:

- fluxos críticos;
- loading;
- vazio;
- erro;
- permissões;
- interações principais;
- filtros/paginação.

## Regressão

Antes de encerrar cada fase:

- suíte existente deve permanecer verde;
- novas funcionalidades devem ter testes;
- não reduzir cobertura removendo testes válidos apenas para passar.

---

# 19. Validações obrigatórias por fase

Usar os comandos reais do repositório.

No mínimo, quando existentes:

## Frontend

```bash
npm test
npm run lint
npm run typecheck
npm run build
```

ou equivalentes definidos em `package.json`.

## Backend

```bash
pytest
ruff check .
```

ou equivalentes definidos pelo projeto.

## Geral

```bash
git diff --check
git status
```

### PostgreSQL

Se `TEST_DATABASE_URL` estiver configurada e for claramente um banco de teste:

- executar suíte PostgreSQL;
- validar migrations.

Se não estiver disponível:

- não apontar testes destrutivos para banco de desenvolvimento;
- registrar a limitação;
- executar o restante;
- não afirmar que testes PostgreSQL passaram.

---

# 20. Commits por fase

Cada fase deve terminar em um commit próprio e coerente.

Títulos previstos:

```text
Fase 0
refactor: prepara fundação transacional do ERP

Fase 1
feat: adiciona segurança e auditoria operacional

Fase 2
feat: expande catálogo operacional do ERP

Fase 3
feat: adiciona orçamentos e pedidos de venda

Fase 4
feat: adiciona controle de estoque por movimentações

Fase 5
feat: adiciona compras e recebimentos

Fase 6
feat: integra vendas compras e estoque

Fase 7
feat: adiciona gestão financeira do ERP

Fase 8
feat: adiciona relatórios gerenciais do ERP

Fase 9
feat: adiciona configuração modular do ERP
```

O executor pode ajustar a redação se a implementação real justificar, preservando conventional commits e PT-BR.

Não fazer um commit gigante contendo várias fases.

---

# 21. Documentação obrigatória

Ao final de cada fase:

- atualizar este plano marcando o status;
- atualizar `AI_CONTEXT.md` com estado realmente implementado;
- atualizar README somente quando comportamento público mudar;
- documentar novas variáveis de ambiente;
- documentar migrations;
- registrar decisões arquiteturais não óbvias.

Não reescrever documentos históricos para fingir que decisões novas sempre existiram.

---

# 22. Critério de conclusão do plano

O plano estará concluído quando:

- Fases 0–9 estiverem `CONCLUÍDA`;
- testes disponíveis estiverem verdes;
- frontend build estiver aprovado;
- migrations estiverem consistentes;
- `git diff --check` estiver limpo;
- `git status` estiver limpo após o último commit;
- `AI_CONTEXT.md` refletir o estado final;
- nenhuma fase depender de alteração não versionada.

---

# 23. Backlog posterior ao Plano 04

Itens candidatos a planos futuros:

- fiscal brasileiro;
- emissão de documentos fiscais;
- integrações bancárias;
- multiempresa;
- múltiplos depósitos avançados;
- lotes e validade;
- serialização;
- reservas avançadas;
- integrações externas;
- importadores;
- CRM Geral;
- integração ERP ↔ CRM;
- automações de negócio;
- APIs públicas;
- webhooks;
- cloud storage;
- BI avançado.

Nada disso deve expandir silenciosamente o escopo do Plano 04.
