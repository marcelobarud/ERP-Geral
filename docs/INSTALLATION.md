# Instalação do ERP Geral

Este é o procedimento oficial para uma instalação nativa do ERP Geral em uma
máquina Windows ou Linux. O modelo desta versão é uma instalação por cliente:
um frontend, um backend e um banco PostgreSQL.

## Pré-requisitos

- Git;
- Python 3.11 ou superior;
- Node.js 20.19 ou superior; Node.js 22.12+ é recomendado;
- npm;
- PostgreSQL 15 ou superior;
- acesso administrativo para criar um usuário e um banco no PostgreSQL.

Confira as versões:

```powershell
git --version
python --version
node --version
npm --version
psql --version
```

## 1. Obter o código

```powershell
git clone https://github.com/marcelobarud/ERP-Geral.git
Set-Location -LiteralPath .\ERP-Geral
```

## 2. Criar o banco

Crie um usuário dedicado e um banco vazio. Não use o superusuário do
PostgreSQL para a aplicação.

Exemplo executado em uma sessão administrativa do PostgreSQL:

```sql
CREATE USER erp_user WITH PASSWORD 'defina-uma-senha-fora-do-repositorio';
CREATE DATABASE erp_geral OWNER erp_user;
```

Para a suíte de testes, crie um banco separado com sufixo `_test`:

```sql
CREATE DATABASE erp_geral_test OWNER erp_user;
```

## 3. Configurar o ambiente

```powershell
Copy-Item .env.example .env
```

Edite `.env` e substitua todos os placeholders. Para uma instalação real,
mantenha:

```text
ENVIRONMENT=production
AUTH_REQUIRED=true
```

Gere secrets aleatórios e mantenha o arquivo fora do Git. O backend carrega o
`.env` da raiz do repositório, portanto o comando funciona mesmo iniciado em
`backend/`.

## 4. Instalar o backend

```powershell
Set-Location -LiteralPath .\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install .
```

Em uma máquina de desenvolvimento, use `.[dev]` para instalar pytest e Ruff:

```powershell
.\.venv\Scripts\python.exe -m pip install ".[dev]"
```

## 5. Aplicar migrations

Ainda dentro de `backend/`:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\alembic.exe heads
```

O `current` deve coincidir com o único `head` exibido.

## 6. Criar o primeiro administrador

Com o backend em execução e a autenticação ativa, faça uma única chamada ao
endpoint de bootstrap, usando o token configurado em `AUTH_BOOTSTRAP_TOKEN`:

```text
POST /api/auth/bootstrap
```

Payload:

```json
{
  "nome": "Administrador",
  "email": "admin@cliente.example",
  "senha": "defina-uma-senha-forte",
  "token": "token-configurado-no-ambiente"
}
```

O endpoint só aceita o primeiro usuário. Depois do bootstrap, use o login do
frontend e remova o token de bootstrap dos registros temporários de operação.

## 7. Instalar e compilar o frontend

```powershell
Set-Location -LiteralPath ..\frontend
npm ci
```

Crie `frontend/.env.local` somente se a API não estiver no endereço padrão:

```text
VITE_API_BASE_URL=https://erp.cliente.example
```

Gere o build:

```powershell
npm run build
```

O diretório `frontend/dist` é o artefato estático que deve ser servido por um
servidor web. Consulte [PRODUCTION.md](PRODUCTION.md) para a execução sem
servidores de desenvolvimento.

## 8. Validação inicial

Confirme:

```text
[ ] frontend abre no endereço publicado
[ ] backend responde GET /api/health
[ ] status, banco e schema estão ok
[ ] login do administrador funciona
[ ] cliente pode ser criado
[ ] produto pode ser criado
[ ] venda de teste pode ser registrada
```

Não use `npm run dev` ou `uvicorn --reload` como execução de cliente.

## Script assistido

Em Windows, após criar o banco e preencher o `.env`, o script abaixo automatiza
a criação da virtualenv, instalação das dependências, migrations e build:

```powershell
.\scripts\install.ps1
```

O script não cria usuários do PostgreSQL e não grava secrets automaticamente.
