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
- detalhes relacionais;
- histórico operacional;
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

Ambas devem usar o formato `postgresql+psycopg://...`.

## Migrations

No diretório `backend/`, execute:

```powershell
python -m alembic upgrade head
```

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
