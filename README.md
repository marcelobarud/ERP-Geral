# ERP Geral

ERP Geral é uma plataforma genérica e configurável de gestão administrativa e
operacional.

A raiz do repositório pode ser aberta como um vault do Obsidian; o índice
documental principal está em [docs/OBSIDIAN_PROJECT_INDEX.md](docs/OBSIDIAN_PROJECT_INDEX.md).

## Estado atual

A versão atual oferece:

- clientes;
- produtos;
- fornecedores;
- funcionários;
- registro de vendas;
- campos personalizados;
- filtros e busca operacional;
- paginação backend-driven nas listagens principais;
- detalhes relacionais;
- histórico operacional;
- cancelamento não destrutivo de vendas com status e observação;
- personalização visual e branding.
- orçamentos, pedidos de venda e conversões controladas;
- compras, recebimentos parciais/totais e histórico de custos;
- depósitos, movimentações, inventários e integração de vendas/devoluções com estoque;
- financeiro operacional, fluxo de caixa e relatórios agregados;
- autenticação, permissões, auditoria e configuração modular.

## Limites atuais e direção futura

O backend desses módulos já está implementado e validado. O Plano 05 fecha
gradualmente as fatias verticais que ainda faltam na interface, sem iniciar
novos domínios antes de integrar os existentes.

## Requisitos

- Git;
- Python 3.11 ou superior;
- Node.js 20.19 ou superior (22.12+ recomendado);
- npm;
- PostgreSQL;
- um banco de desenvolvimento e, preferencialmente, um banco separado para testes.

Para preparar uma instalação reproduzível, siga
[docs/INSTALLATION.md](docs/INSTALLATION.md). A execução de produção está em
[docs/PRODUCTION.md](docs/PRODUCTION.md).

## Configuração

Copie `.env.example` para um arquivo `.env` na raiz do projeto e ajuste as
URLs e secrets. O backend encontra esse arquivo pela raiz do monorepo, mesmo
quando o comando é executado dentro de `backend/`. Não versione o arquivo
`.env`.

As variáveis principais são:

- `DATABASE_URL`: banco usado pelo backend e pelas migrations;
- `TEST_DATABASE_URL`: banco PostgreSQL dedicado aos testes.
- `ENVIRONMENT`: ambiente de execução; `production` ativa a autenticação
  obrigatória e valida os secrets.
- `AUTH_REQUIRED`: ativa autenticação fora de produção quando necessário.
- `AUTH_SECRET`: segredo usado para assinar sessões; mantenha fora do Git.
- `AUTH_TOKEN_EXPIRATION_MINUTES`: duração dos tokens de sessão.
- `AUTH_BOOTSTRAP_TOKEN`: token temporário para criar o primeiro administrador.
- `CORS_ORIGINS`: origens permitidas separadas por vírgula; em produção, deixe
  vazio quando frontend e API usarem a mesma origem.
- `API_DOCS_ENABLED`: controla `/docs`, `/redoc` e `/openapi.json`; o padrão de
  produção é desativado.
- `STORAGE_DIR`: diretório persistente opcional para uploads e branding.

Ambas devem usar o formato `postgresql+psycopg://...`.

Em desenvolvimento local controlado, altere explicitamente
`ENVIRONMENT=development` e `AUTH_REQUIRED=false`. Nunca use essa configuração
em uma instalação exposta a usuários reais.

Para executar a suíte PostgreSQL, configure `TEST_DATABASE_URL` para um banco
separado com sufixo `_test`. A fixture valida o PostgreSQL real, mantém os
dados de referência das migrations e limpa somente o banco de testes.

Em desenvolvimento controlado, `AUTH_REQUIRED=false` mantém a experiência
local existente. Em produção, configure `AUTH_SECRET` e
`AUTH_BOOTSTRAP_TOKEN` com valores reais; o backend rejeita uma configuração
de produção sem esses secrets.

Quando a autenticação está ativa, crie o primeiro administrador com
`POST /api/auth/bootstrap` usando `nome`, `email`, `senha` e o token de
bootstrap. Depois utilize `POST /api/auth/login`; o frontend mantém a sessão
e oferece a opção de logout.

## Migrations

No diretório `backend/`, execute:

```powershell
python -m alembic upgrade head
```

Antes de iniciar o backend, confirme a revisão aplicada com:

```powershell
python -m alembic current
python -m alembic heads
```

O endpoint `GET /api/health` informa separadamente o estado do processo,
PostgreSQL e schema. O status `degraded` significa que o processo respondeu,
mas alguma dependência operacional — normalmente a revisão Alembic — ainda
não está pronta.

A migration `20260911_0002` prepara a fundação transacional do ERP: adiciona
timestamps operacionais, ciclo de vida e observação das vendas, paginação das
listagens e agregações do dashboard.

A migration `20260911_0003` adiciona autenticação por sessão revogável,
usuários, permissões e auditoria operacional. A migration `20260911_0004`
expande o catálogo com SKU, código de barras, unidades, categorias estruturadas,
produto ativo/inativo, estoque mínimo, múltiplos fornecedores e histórico de
custos.

A migration `20260911_0005` adiciona condições de pagamento, orçamentos e
pedidos de venda, com snapshots comerciais, transições de status, conversões
idempotentes para pedido/venda e saída HTML simples para impressão.

A migration `20260911_0006` adiciona o depósito padrão, movimentações de
estoque, proteção contra saldo negativo, reversões idempotentes, inventário e
consulta de saldo comparada ao estoque mínimo.

O depósito padrão é identificado explicitamente pela flag `padrao`; as
operações de compras, vendas, devoluções e relatórios resolvem esse depósito
por serviço e não dependem do ID `1`. A migration cria o depósito inicial com
timestamps válidos no PostgreSQL.

A migration `20260911_0007` adiciona pedidos de compra, recebimentos parciais
ou totais, entradas idempotentes no estoque e atualização do histórico de
custos após a confirmação do recebimento.

A migration `20260911_0008` integra vendas e devoluções ao estoque: vendas
podem ser postadas uma única vez, cancelamentos geram reversões compensatórias
e devoluções aprovadas geram entradas idempotentes.

A migration `20260911_0009` adiciona categorias financeiras, contas/caixas,
títulos a receber e pagar, parcelamento, liquidações reversíveis e fluxo de
caixa previsto versus realizado.

Também estão disponíveis relatórios agregados de comercial, compras, estoque
e financeiro, além do dashboard ERP, sempre calculados no backend.

A migration `20260911_0010` adiciona a configuração central dos módulos
Comercial, Compras, Estoque, Financeiro e Relatórios.

A migration `20260911_0011` preserva na venda a origem do pedido comercial e a
condição de pagamento utilizada. A interface comercial agora oferece
orçamentos, pedidos, devoluções e condições de pagamento, com conversões
controladas e impressão HTML dos documentos.

A migration `20260911_0012` separa os identificadores de aparência do
dashboard e dos relatórios Comercial, Compras, Estoque e Financeiro, evitando
que personalizações visuais de uma tela sejam reutilizadas indevidamente em
outra.

A interface de compras agora oferece pedidos de compra e recebimentos,
incluindo recebimentos parciais, custo efetivo, confirmação idempotente,
entrada no estoque e histórico de custos.

O contas a pagar de um recebimento de compra nasce somente na confirmação
efetiva do recebimento; criar um recebimento em rascunho não gera obrigação
financeira.

## Marco funcional V1

O ERP Geral foi classificado como **SIM, COM AJUSTES** no Plano 06. Os fluxos
de venda, compra, estoque, financeiro, devolução, inventário, permissões,
módulos e relatórios foram validados no ambiente local. Fiscal, NF-e, SPED,
contabilidade, folha, CRM, BI avançado e integrações bancárias automáticas
seguem como evoluções futuras.

A interface de estoque agora oferece saldos, movimentações, ajustes,
inventários e depósitos, mantendo o saldo derivado das movimentações e o
depósito padrão resolvido explicitamente.

A interface financeira agora oferece contas a receber, contas a pagar,
liquidações, reversões e fluxo de caixa previsto versus realizado. Vendas e
recebimentos confirmados integram automaticamente seus títulos financeiros,
com vínculo de origem idempotente.

A área de Relatórios oferece Dashboard ERP e visões agregadas de Comercial,
Compras, Estoque e Financeiro, com filtro comercial por período e exportação
CSV dos dados carregados.

Em Configurações → Módulos, as áreas Comercial, Compras, Estoque, Financeiro
e Relatórios podem ser ativadas ou desativadas. A navegação acompanha essa
configuração e rotas diretas de módulos desativados exibem estado bloqueado,
mantendo autenticação e permissões na API.

O backend aplica headers de segurança, limites de tentativa por IP para login,
bootstrap e upload de logo, expiração/revogação de sessões e auditoria das
operações críticas de autenticação, usuários, configuração, compras,
recebimentos, estoque, vendas e financeiro. O rate limiting local deve ser
complementado por um proxy compartilhado quando houver múltiplas instâncias.

Com a autenticação ativa, a área Configurações → Usuários fica disponível para
administradores e permite administrar papéis, vínculos com funcionários e
status de acesso. A interface trata separadamente indisponibilidade, sessão
expirada, falta de permissão, validação, conflito e falhas do servidor sem
expor detalhes técnicos.

## Execução local

Backend, em um terminal:

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend, em outro terminal:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

A aplicação fica disponível em `http://127.0.0.1:5173` e a documentação da
API em `http://127.0.0.1:8000/docs`.

## Testes e qualidade

Backend:

```powershell
cd backend
python -m pytest
python -m ruff check app tests
```

Com PostgreSQL de testes configurado na sessão atual:

```powershell
$env:DATABASE_URL="postgresql+psycopg://usuario@localhost:5432/erp_geral_test"
$env:TEST_DATABASE_URL="postgresql+psycopg://usuario@localhost:5432/erp_geral_test"
python -m alembic upgrade head
python -m pytest
```

As credenciais devem ser fornecidas pelo ambiente local e não devem ser
gravadas neste repositório.

Frontend:

```powershell
cd frontend
npm test
npm run lint
npm run typecheck
npm run build
```
