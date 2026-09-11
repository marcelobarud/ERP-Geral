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

## Direção futura

O projeto deverá evoluir gradualmente para um ERP de uso geral, com módulos
como pedidos, compras, estoque, movimentações, inventário, contas a pagar,
contas a receber e fluxo de caixa. Esses módulos ainda não fazem parte da
versão atual.

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

A migration `20260911_0007` adiciona pedidos de compra, recebimentos parciais
ou totais, entradas idempotentes no estoque e atualização do histórico de
custos após a confirmação do recebimento.

A migration `20260911_0008` integra vendas e devoluções ao estoque: vendas
podem ser postadas uma única vez, cancelamentos geram reversões compensatórias
e devoluções aprovadas geram entradas idempotentes.

A migration `20260911_0009` adiciona categorias financeiras, contas/caixas,
títulos a receber e pagar, parcelamento, liquidações reversíveis e fluxo de
caixa previsto versus realizado.

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

Frontend:

```powershell
cd frontend
npm test
npm run lint
npm run typecheck
npm run build
```
