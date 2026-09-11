# ERP Geral

ERP Geral é uma plataforma genérica e configurável de gestão administrativa e
operacional.

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

- Python 3.11 ou superior;
- Node.js e npm;
- PostgreSQL;
- um banco de desenvolvimento e, preferencialmente, um banco separado para testes.

## Configuração

Copie `.env.example` para um arquivo `.env` na raiz do projeto e ajuste as
URLs para as credenciais locais do PostgreSQL. Não versione o arquivo `.env`.

As variáveis principais são:

- `DATABASE_URL`: banco usado pelo backend e pelas migrations;
- `TEST_DATABASE_URL`: banco PostgreSQL dedicado aos testes.
- `ENVIRONMENT`: ambiente de execução; `production` ativa a autenticação
  obrigatória e valida os secrets.
- `AUTH_REQUIRED`: ativa autenticação fora de produção quando necessário.
- `AUTH_SECRET`: segredo usado para assinar sessões; mantenha fora do Git.
- `AUTH_TOKEN_EXPIRATION_MINUTES`: duração dos tokens de sessão.
- `AUTH_BOOTSTRAP_TOKEN`: token temporário para criar o primeiro administrador.

Ambas devem usar o formato `postgresql+psycopg://...`.

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
