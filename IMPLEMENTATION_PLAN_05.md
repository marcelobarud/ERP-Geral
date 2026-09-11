# IMPLEMENTATION_PLAN_05 — Estabilização e Integração Vertical do ERP Geral

**Projeto:** ERP Geral
**Repositório:** `marcelobarud/ERP-Geral`
**Plano:** 05
**Data-base:** 11/09/2026
**Objetivo:** estabilizar a fundação criada no Plano 04 e transformar os módulos já existentes no backend em funcionalidades completas de ponta a ponta, com frontend, integrações reais, testes PostgreSQL e documentação coerente.

---

## 1. Contexto

A auditoria funcional posterior ao Plano 04 mostrou que o ERP Geral avançou significativamente no backend e banco, mas ainda possui uma diferença importante entre:

- modelagem/API já existente;
- experiência real do usuário;
- integração entre módulos;
- validação PostgreSQL;
- documentação atual.

O projeto já possui base técnica para:

- orçamentos;
- pedidos de venda;
- compras;
- recebimentos;
- estoque;
- financeiro;
- relatórios;
- módulos ativos;
- autenticação;
- permissões;
- auditoria.

Entretanto, parte relevante dessa base ainda não está exposta na interface e algumas integrações ainda são incompletas.

Este plano NÃO deve continuar expandindo horizontalmente o backend sem fechar os fluxos existentes.

A estratégia oficial passa a ser:

> construir e validar fatias verticais completas.

---

## 2. Princípios do Plano 05

### 2.1 Integração vertical

Cada fase deve fechar o fluxo completo:

```text
Banco
↓
Model
↓
Service
↓
API
↓
Frontend
↓
Testes
↓
Documentação
```

Não considerar módulo concluído apenas porque possui tabela e endpoint.

### 2.2 Não criar novos domínios sem necessidade

Antes de adicionar novas entidades ou áreas, verificar se o backend atual já possui suporte suficiente.

### 2.3 PostgreSQL real é gate

A partir deste plano, módulos transacionais não devem ser considerados plenamente validados sem testes PostgreSQL.

### 2.4 Venda continua sendo transação final

Preservar:

```text
Orçamento
↓
Pedido
↓
Venda
```

### 2.5 Estoque continua sendo baseado em movimentações

Não substituir a arquitetura existente por saldo direto no produto.

### 2.6 Financeiro deve ser integrado

Evitar um financeiro isolado que exija duplicação manual de dados já existentes em vendas e compras.

### 2.7 UI deve refletir módulos existentes

O usuário deve conseguir operar o que o backend já suporta.

### 2.8 Documentação deve representar o estado real

README e AI_CONTEXT não podem continuar descrevendo como "futuro" algo já implementado.

---

## 3. Estado-base identificado

O projeto já possui:

### Cadastros
- clientes;
- fornecedores;
- funcionários;
- produtos;
- categorias;
- unidades;
- múltiplos fornecedores por produto;
- histórico de custo.

### Comercial
- orçamentos;
- itens de orçamento;
- pedidos de venda;
- itens de pedido;
- vendas;
- itens de venda;
- devoluções.

### Compras
- pedidos de compra;
- itens;
- recebimentos;
- itens de recebimento.

### Estoque
- depósitos;
- configuração;
- movimentações;
- inventários;
- itens de inventário.

### Financeiro
- categorias;
- contas;
- títulos;
- parcelas;
- liquidações.

### Segurança
- usuários;
- sessões;
- roles/permissões;
- auditoria.

### Configuração
- aparência;
- campos personalizados;
- módulos ERP.

### Relatórios
- backend já possui base para relatórios e dashboard ERP.

---

## 4. Problemas críticos atuais

### BLOQUEADOR — recebimento parcial

Existe provável erro na lógica de recebimento parcial de compras.

O cálculo identificado utiliza a quantidade total do item em vez da quantidade recebida no recebimento atual.

Esse problema deve ser corrigido antes de qualquer evolução adicional de compras.

### BLOQUEADOR OPERACIONAL — testes PostgreSQL

`TEST_DATABASE_URL` não está configurada.

Estado auditado:

```text
53 passed
65 skipped
```

Os testes ignorados incluem fluxos dependentes de PostgreSQL, constraints e migrations.

### IMPORTANTE — depósito hardcoded

Compras/vendas utilizam depósito `1` diretamente em parte das integrações.

Isso deve ser eliminado antes da exposição completa dos módulos.

### IMPORTANTE — frontend incompleto

Ainda não existem telas operacionais completas para:

- orçamento;
- pedidos;
- compras;
- recebimentos;
- estoque;
- financeiro;
- relatórios.

### IMPORTANTE — financeiro não integrado

Vendas não geram automaticamente contas a receber.

Compras/recebimentos não geram automaticamente contas a pagar.

### IMPORTANTE — documentação defasada

README e AI_CONTEXT não representam corretamente o backend atual.

---

## 5. Fases do Plano 05

| Fase | Nome | Prioridade |
|---|---|---:|
| 0 | Estabilização do Plano 04 | P0 |
| 1 | Comercial completo | P0 |
| 2 | Compras e recebimentos completos | P1 |
| 3 | Estoque completo | P1 |
| 4 | Financeiro integrado | P1 |
| 5 | Relatórios e Dashboard ERP | P1 |
| 6 | Navegação modular e configurações | P2 |
| 7 | Hardening operacional | P2 |

---

## 6. Fase 0 — Estabilização do Plano 04

**Status:** CONCLUÍDA em 11/09/2026
**Commit esperado:** `fix: estabiliza fundação criada no plano 04`

### Objetivo

Corrigir problemas conhecidos, validar PostgreSQL e alinhar documentação antes de continuar.

### 6.1 Corrigir recebimento parcial

Inspecionar `backend/app/services/purchases.py`.

Corrigir a regra para que:

```text
quantidade_recebida_acumulada
=
quantidade_recebida_anterior
+
quantidade_real_do_recebimento_atual
```

Não somar a quantidade total pedida incorretamente.

Cobrir:

- recebimento parcial;
- múltiplos recebimentos;
- recebimento final;
- tentativa acima do saldo pendente;
- idempotência.

### 6.2 Configurar ambiente PostgreSQL de testes

Preparar `TEST_DATABASE_URL`.

Requisitos:

- banco exclusivo de testes;
- nunca apontar para banco de desenvolvimento;
- documentação clara;
- limpeza controlada apenas no banco de teste.

Se necessário, criar instruções/scripts auxiliares mínimos.

### 6.3 Validar migrations

Executar:

- upgrade do zero;
- upgrade até head;
- migrations sequenciais;
- downgrade quando seguro;
- re-upgrade.

Validar cadeia até a migration atual.

### 6.4 Executar suíte PostgreSQL completa

Meta:

```text
0 skipped por ausência de TEST_DATABASE_URL
```

Se alguns skips forem intencionais por outro motivo, documentar.

### 6.5 Depósito padrão

Remover dependência direta de ID fixo `1`.

Criar mecanismo explícito de depósito padrão.

Pode ser:

- configuração;
- flag no depósito;
- resolução via service.

Não espalhar ID fixo.

### 6.6 Documentação

Atualizar:

- README;
- AI_CONTEXT;
- Plano 04, se necessário apenas como estado histórico;
- variáveis de ambiente.

### 6.7 Revisar commits locais

Verificar os commits locais pendentes.

Não reescrever histórico sem necessidade.

Após validação completa, publicar conforme fluxo autorizado.

### Critérios de aceite

- bug corrigido;
- testes PostgreSQL executáveis;
- migrations validadas;
- nenhum depósito hardcoded crítico;
- documentação coerente;
- suíte verde;
- git limpo.

### Resultado da execução

Os critérios da Fase 0 foram atendidos. A causa raiz da falha da migration
`20260911_0006` era a inserção do depósito sem `created_at` e `updated_at`;
durante a validação PostgreSQL também foi identificado que expressões
`CURRENT_TIMESTAMP` não podem ser passadas como parâmetros de `bulk_insert`.
O seed foi convertido para `INSERT` SQL explícito, mantendo a migration
reversível e preservando suas revisões.

Também foram corrigidos o acumulado de recebimentos parciais, a resolução
explícita do depósito padrão e o isolamento da fixture PostgreSQL. A suíte
completa passou com `118 passed` no PostgreSQL de testes. A validação de
frontend passou com `75 passed`, lint, typecheck e build; Ruff e
`git diff --check` também passaram.

O upgrade foi validado desde banco vazio e desde revisão anterior. Em banco
descartável, o downgrade até `base` e o re-upgrade até `20260911_0010` também
foram aprovados. A Fase 1 foi executada na sequência e está registrada abaixo.

---

## 7. Fase 1 — Comercial completo

**Status:** CONCLUÍDA em 11/09/2026
**Commit:** `feat: conclui fluxo comercial do ERP`

### Objetivo

Transformar o backend comercial já existente em fluxo funcional completo.

### 7.1 Navegação

Criar grupo:

```text
Comercial
├── Orçamentos
├── Pedidos
├── Vendas
└── Devoluções
```

### 7.2 Condições de pagamento

Criar interface administrativa simples.

Permitir:

- listar;
- criar;
- editar;
- ativar/inativar.

### 7.3 Orçamentos

Frontend deve permitir:

- listar;
- buscar;
- filtrar;
- criar;
- editar enquanto permitido;
- visualizar detalhes;
- alterar status;
- converter em pedido;
- imprimir/exportar apresentação simples.

### 7.4 Pedidos de venda

Frontend deve permitir:

- listar;
- buscar;
- filtrar;
- criar;
- editar em estados permitidos;
- confirmar;
- cancelar;
- visualizar;
- converter em venda.

### 7.5 Conversões

Validar:

```text
Orçamento → Pedido
Pedido → Venda
```

Regras:

- sem duplicação;
- com vínculo de origem;
- snapshots preservados;
- transições inválidas bloqueadas;
- autorização backend.

### 7.6 Devoluções

Criar interface para:

- devolução total;
- devolução parcial;
- motivo;
- visualização do efeito.

Nesta fase, integrar apenas efeitos já suportados com segurança.

### 7.7 Vendas

Atualizar telas atuais para refletir:

- status;
- cancelamento;
- origem do pedido;
- observações;
- condição de pagamento quando aplicável.

### Testes

Cobrir frontend e backend de ponta a ponta.

### Critério de aceite

Usuário consegue realizar:

```text
Orçamento
→ Pedido
→ Venda
→ Devolução
```

sem usar API manualmente.

### Resultado da execução

A Fase 1 foi concluída com navegação comercial para Orçamentos, Pedidos,
Vendas e Devoluções, além da administração de condições de pagamento. Foram
adicionadas telas para criar, editar enquanto permitido, pesquisar, filtrar,
visualizar, alterar status, converter e imprimir orçamentos e pedidos. A tela
de devoluções permite registrar devoluções totais ou parciais, informar o
motivo e aprovar o efeito de entrada no estoque.

O vínculo pedido→venda e a condição de pagamento passaram a ser persistidos
na venda pela migration `20260911_0011`. As conversões continuam idempotentes,
preservam snapshots e bloqueiam transições inválidas no backend.

Validações da fase: backend PostgreSQL `118 passed`, frontend `77 passed`,
lint, typecheck, build, Ruff e `git diff --check` aprovados.

---

## 8. Fase 2 — Compras e recebimentos completos

**Status:** CONCLUÍDA em 11/09/2026
**Commit:** `feat: conclui fluxo de compras e recebimentos`

### Objetivo

Expor e validar o processo completo de compras.

### 8.1 Navegação

```text
Compras
├── Pedidos
└── Recebimentos
```

### 8.2 Pedido de compra

Frontend:

- listar;
- buscar;
- filtrar;
- criar;
- editar;
- emitir;
- cancelar;
- visualizar status;
- visualizar itens recebidos/pendentes.

### 8.3 Recebimento

Permitir:

- selecionar pedido;
- receber total;
- receber parcialmente;
- registrar quantidade real;
- registrar custo real;
- confirmar recebimento;
- visualizar histórico.

### 8.4 Estoque

Confirmação de recebimento deve gerar entrada única.

### 8.5 Histórico de custo

Expor ou validar o histórico gerado.

### 8.6 Depósito

Usuário deve selecionar ou utilizar depósito padrão explicitamente resolvido.

Nenhum ID fixo.

### Testes

- parcial;
- múltiplos recebimentos;
- finalização;
- excesso;
- idempotência;
- estoque;
- custo;
- cancelamento.

---

## 9. Fase 3 — Estoque completo

**Status:** PENDENTE
**Commit esperado:** `feat: conclui gestão operacional de estoque`

### Objetivo

Transformar o motor de estoque existente em módulo operável.

### Navegação

```text
Estoque
├── Saldos
├── Movimentações
├── Ajustes
├── Inventários
└── Depósitos
```

### 9.1 Depósitos

Frontend:

- listar;
- criar;
- editar;
- ativar/inativar;
- definir padrão.

### 9.2 Saldo

Mostrar:

- produto;
- SKU;
- depósito;
- saldo;
- estoque mínimo;
- status de baixo estoque.

Filtros:

- produto;
- categoria;
- depósito;
- baixo estoque.

### 9.3 Movimentações

Timeline/tabela contendo:

- data;
- produto;
- depósito;
- tipo;
- quantidade;
- origem;
- documento;
- usuário.

### 9.4 Ajustes

Permitir ajuste:

- entrada;
- saída;
- motivo obrigatório;
- depósito;
- usuário.

### 9.5 Inventário

Fluxo:

```text
Criar inventário
↓
Registrar contagem
↓
Calcular diferença
↓
Confirmar
↓
Gerar ajuste
```

### 9.6 Performance

Avaliar estratégia de saldo.

Se cálculo repetido por movimentações ficar caro, implementar cache/materialização sem mudar fonte de verdade.

Não otimizar prematuramente sem medição.

### 9.7 Transferência

Se infraestrutura atual permitir com baixo risco, incluir transferência simples entre depósitos.

Caso contrário, registrar para plano posterior.

### Resultado da execução

A Fase 2 foi concluída com navegação para Pedidos de compra e Recebimentos.
Pedidos permitem listar, pesquisar, filtrar, criar, editar em rascunho, emitir,
cancelar e visualizar quantidades solicitadas, recebidas e pendentes.
Recebimentos permitem selecionar o pedido, informar quantidade real parcial ou
total, registrar custo efetivo, criar rascunho, confirmar e consultar o
histórico. A confirmação continua usando o depósito padrão explicitamente
resolvido pelo backend, gera uma única entrada de estoque e atualiza o
histórico de custos.

O backend recebeu edição segura de pedidos em rascunho e busca por número ou
fornecedor. Não foi necessária migration nova nesta fase.

Validações da fase: teste PostgreSQL de compras `1 passed`, backend completo
`118 passed`, frontend `77 passed`, lint, typecheck, build, Ruff e
`git diff --check` aprovados.

---

## 10. Fase 4 — Financeiro integrado

**Status:** PENDENTE
**Commit esperado:** `feat: integra financeiro às operações do ERP`

### Objetivo

Fechar o ciclo financeiro operacional.

### Navegação

```text
Financeiro
├── Contas a receber
├── Contas a pagar
├── Caixa
└── Fluxo de caixa
```

### 10.1 Métodos/formas de pagamento

Adicionar ou consolidar estrutura necessária.

Distinguir:

- condição de pagamento;
- forma/método efetivamente utilizado.

### 10.2 Venda → contas a receber

Definir regra automática.

Ao concluir venda:

- gerar título;
- gerar parcelas;
- preservar vínculo de origem.

Evitar duplicação.

### 10.3 Compra/recebimento → contas a pagar

Gerar obrigação a pagar conforme regra definida.

Definir se geração ocorre:

- no pedido emitido;
- no recebimento;
- ou por configuração.

Preferência inicial: evento operacional mais seguro e coerente com o domínio real.

### 10.4 Liquidações

Frontend:

- registrar recebimento;
- registrar pagamento;
- parcial;
- total;
- reversão.

### 10.5 Títulos

Filtros:

- aberto;
- parcial;
- pago;
- vencido;
- cancelado;
- cliente/fornecedor;
- período.

### 10.6 Caixa

Mostrar movimentos realizados.

### 10.7 Fluxo de caixa

Separar:

- previsto;
- realizado.

### 10.8 Polimorfismo de origem

Revisar `origem_tipo` / `origem_id`.

Se a ausência de FK estiver causando risco real, propor solução segura.

Não fazer refatoração grande apenas por estética.

---

## 11. Fase 5 — Relatórios e Dashboard ERP

**Status:** PENDENTE
**Commit esperado:** `feat: conclui relatórios e dashboard do ERP`

### Objetivo

Expor no frontend as agregações já existentes e consolidar a visão gerencial.

### 11.1 Dashboard

Atualizar para indicadores ERP.

#### Comercial
- vendas do período;
- pedidos;
- cancelamentos;
- devoluções.

#### Compras
- pedidos pendentes;
- recebimentos pendentes.

#### Estoque
- produtos abaixo do mínimo;
- valor de estoque se cálculo confiável existir.

#### Financeiro
- contas a receber;
- contas a pagar;
- vencidos;
- fluxo previsto/realizado.

### 11.2 Relatórios

Criar telas para:

#### Comercial
- por período;
- cliente;
- produto;
- funcionário.

#### Compras
- fornecedor;
- produto;
- período.

#### Estoque
- saldo;
- movimentação;
- ajustes;
- inventários.

#### Financeiro
- a pagar;
- a receber;
- fluxo de caixa;
- vencimentos.

### 11.3 Filtros

Filtros backend-driven.

Não carregar todas as linhas no browser.

### 11.4 Exportação

Priorizar:

- CSV;
- XLSX.

PDF apenas onde agregar valor real.

---

## 12. Fase 6 — Navegação modular e configurações

**Status:** PENDENTE
**Commit esperado:** `feat: integra módulos ativos à navegação do ERP`

### Objetivo

Usar de fato a infraestrutura de módulos ativos.

### 12.1 Configuração de módulos

Tela:

```text
Módulos
[✓] Comercial
[✓] Compras
[✓] Estoque
[ ] Financeiro
[✓] Relatórios
```

### 12.2 Navegação

Menu deve refletir:

- módulo ativo;
- permissão do usuário.

### 12.3 Segurança

Ocultar menu NÃO é segurança.

API continua protegida.

### 12.4 Rotas diretas

Acesso direto a módulo desativado deve:

- bloquear operação;
- apresentar estado apropriado;
- não depender apenas do menu.

### 12.5 Configurações

Organizar:

```text
Configurações
├── Aparência
├── Campos personalizados
├── Módulos
├── Usuários
├── Permissões
├── Depósitos
├── Condições de pagamento
└── demais configurações gerais
```

Evitar menu lateral excessivo.

---

## 13. Fase 7 — Hardening operacional

**Status:** PENDENTE
**Commit esperado:** `chore: reforça segurança e operação do ERP`

### Objetivo

Preparar o produto para uso mais realista.

### 13.1 Rate limiting

Adicionar onde apropriado:

- login;
- endpoints sensíveis;
- uploads.

### 13.2 Security headers

Revisar:

- CSP quando compatível;
- X-Content-Type-Options;
- frame policy;
- referrer policy;
- demais headers relevantes.

### 13.3 Auditoria

Revisar cobertura de:

- vendas;
- compras;
- estoque;
- financeiro;
- usuários;
- configurações.

### 13.4 Uploads

Revisar logo/storage atual.

Não migrar obrigatoriamente para cloud storage.

Apenas documentar limites operacionais de múltiplas instâncias.

### 13.5 Sessões

Revisar:

- expiração;
- revogação;
- logout;
- usuário inativo;
- secrets.

### 13.6 Banco

Revisar índices após crescimento dos novos módulos.

Não criar índice sem query real que justifique.

---

## 14. Validações obrigatórias por fase

### Frontend

Usar comandos reais do projeto.

Esperado:

```bash
npm test
npm run lint
npm run typecheck
npm run build
```

### Backend

Esperado:

```bash
pytest
ruff check .
```

### PostgreSQL

Com `TEST_DATABASE_URL` válida:

- testes PostgreSQL;
- migrations;
- constraints;
- integrações.

A partir da conclusão da Fase 0:

> ausência de execução PostgreSQL deve ser considerada bloqueio para concluir fases transacionais críticas, salvo justificativa explícita.

### Geral

```bash
git diff --check
git status
```

---

## 15. Estratégia de commits

Cada fase = um commit principal.

Mensagens previstas:

```text
Fase 0
fix: estabiliza fundação criada no plano 04

Fase 1
feat: conclui fluxo comercial do ERP

Fase 2
feat: conclui fluxo de compras e recebimentos

Fase 3
feat: conclui gestão operacional de estoque

Fase 4
feat: integra financeiro às operações do ERP

Fase 5
feat: conclui relatórios e dashboard do ERP

Fase 6
feat: integra módulos ativos à navegação do ERP

Fase 7
chore: reforça segurança e operação do ERP
```

---

## 16. Documentação obrigatória

Ao final de cada fase:

- atualizar `AI_CONTEXT.md`;
- atualizar este plano;
- atualizar README quando comportamento público mudar;
- documentar env vars;
- documentar migrations;
- registrar limitações ainda existentes.

---

## 17. Definition of Done do Plano 05

O Plano 05 estará concluído quando:

- Fases 0–7 estiverem concluídas;
- frontend possuir interfaces dos módulos principais;
- PostgreSQL estiver validado;
- compras e vendas integrarem estoque;
- vendas e compras integrarem financeiro;
- dashboard ERP estiver ativo;
- navegação respeitar módulos e permissões;
- auditoria cobrir operações críticas;
- testes disponíveis estiverem verdes;
- documentação refletir o estado real;
- Git estiver limpo.

---

## 18. Fora de escopo

Continuam fora:

- fiscal brasileiro;
- NF-e;
- SPED;
- folha;
- contabilidade formal;
- CRM;
- multiempresa completo;
- multi-tenant SaaS;
- lotes/validade obrigatórios;
- WMS;
- integrações bancárias automáticas;
- BI avançado;
- APIs públicas;
- webhooks generalizados.

Esses temas exigem planos próprios.
