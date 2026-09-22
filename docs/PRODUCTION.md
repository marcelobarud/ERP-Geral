# Operação de produção — ERP Geral

Este documento descreve a execução web do ERP Geral após o build. Em produção,
o frontend é servido como arquivos estáticos e o FastAPI roda sem `--reload` e
sem `npm run dev`.

## Componentes

```text
navegador → HTTPS/reverse proxy → frontend/dist (SPA)
                           └──→ /api e /uploads → FastAPI :8000 → PostgreSQL
```

O caminho recomendado é usar Nginx, IIS ou outro reverse proxy mantido pelo
operador. O proxy deve encaminhar `/api/`, `/uploads/` e `/docs` para o
backend, servir o `frontend/dist` e usar `index.html` como fallback para rotas
internas do React. Um exemplo de Nginx está em `deploy/nginx.conf.example`.

## Execução local sem servidor de desenvolvimento

Com o `.env` preenchido, as dependências instaladas e o build pronto:

```powershell
.\scripts\start-backend.ps1
.\scripts\serve-frontend.ps1
```

O backend fica em `http://127.0.0.1:8000` e o frontend em
`http://127.0.0.1:4173`. O script do frontend implementa fallback de SPA para
que um refresh em uma rota como `/customers` continue funcionando.

Para acessar pela rede local, informe explicitamente `-BindHost 0.0.0.0` nos dois
scripts e libere somente as portas necessárias no firewall. Em uma instalação
exposta, prefira o reverse proxy com HTTPS.

## Processo Linux

`deploy/erp-geral-backend.service` fornece um modelo de unidade systemd. Ajuste
o caminho `WorkingDirectory`, o usuário do serviço e o caminho do Python antes
de instalar a unidade. O processo executa Uvicorn sem reload e reinicia em caso
de falha.

O frontend deve ser copiado para um diretório de publicação servido pelo proxy:

```bash
cd frontend
npm ci
npm run build
```

Se o frontend e a API estiverem no mesmo domínio, não defina
`VITE_API_BASE_URL`: o cliente usará a mesma origem e o proxy encaminhará
`/api`. Para domínios separados, defina `VITE_API_BASE_URL` antes de executar
`npm run build` e configure CORS no backend.

## Reinício, logs e saúde

- systemd: `systemctl restart erp-geral-backend`;
- logs: `journalctl -u erp-geral-backend -f`;
- Windows: encerre o processo iniciado pelos scripts e execute-o novamente;
- saúde: `GET /api/health` deve retornar `status=ok`, `process=ok`,
  `database=ok` e `schema=ok`;
- documentação OpenAPI (`/docs`) deve ser protegida ou desativada conforme a
  configuração de segurança da instalação.

O processo não deve ser iniciado com `uvicorn --reload` em produção. O build do
frontend deve ser promovido como uma unidade e o backend deve apontar para a
mesma versão de migrations aplicada no banco.
