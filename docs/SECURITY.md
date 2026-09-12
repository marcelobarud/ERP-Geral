# Checklist de segurança de distribuição — ERP Geral

Antes de liberar uma instalação:

- use `ENVIRONMENT=production`;
- mantenha `AUTH_REQUIRED=true` e secrets aleatórios fora do Git;
- troque o `AUTH_BOOTSTRAP_TOKEN` depois do primeiro administrador, removendo o
  token do ambiente de operação quando o procedimento da instalação permitir;
- deixe `CORS_ORIGINS` vazio quando frontend e API estiverem na mesma origem;
  quando separados, liste somente origens HTTPS conhecidas;
- mantenha `API_DOCS_ENABLED=false` em produção ou publique `/docs` somente
  atrás de autenticação do reverse proxy;
- não exponha PostgreSQL diretamente à internet; permita acesso apenas do
  backend e do operador de backup;
- restrinja permissões do `.env`, do diretório `backend/storage` e dos backups;
- armazene backups fora do diretório publicado pelo frontend;
- mantenha HTTPS no reverse proxy e encaminhe os headers `X-Forwarded-*`;
- preserve o limite de tamanho, tipo e pixels de uploads de branding;
- mantenha o rate limit de login, bootstrap e upload ativo;
- não registre senha, token, URL com senha, CPF, telefone ou e-mail em logs;
- revise usuários ativos e papéis periodicamente.

## Secrets e configuração

`Settings` valida secrets mínimos quando `ENVIRONMENT=production` e rejeita
marcadores de exemplo. O `.env.example` não é uma credencial válida. O
operador deve gerar valores aleatórios e distribuir o `.env` por canal seguro.

## CORS e documentação

CORS não é um mecanismo de autenticação. Ele apenas restringe chamadas de
navegadores; mantenha autenticação e autorização no backend. O mesmo vale para
ocultar Swagger: a proteção real continua sendo o controle de acesso das
rotas.
