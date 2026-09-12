# Último gate operacional do ERP Geral

Data: 2026-09-12
Workspace: `D:\Codex\ERP Geral`
Branch: `main`
Remote: `https://github.com/marcelobarud/ERP-Geral.git`
Classificação: **SIM**

## Conclusão

O ERP Geral foi certificado em um ciclo completo com dados artificiais:

```text
backup → restore → health → login → dados → storage
```

Conclusão operacional: **ERP Geral pronto para primeira implantação
controlada.** Isso não representa alta disponibilidade, operação em larga
escala, certificação fiscal ou SaaS.

## Ferramentas PostgreSQL

| Ferramenta | Versão | Resultado |
|---|---:|---|
| PostgreSQL Server | 18.6 | ativo em `D:\PostGre` |
| `psql` | 18.6 | disponível em `D:\PostGre\bin` |
| `pg_dump` | 18.6 | backup real aprovado |
| `pg_restore` | 18.6 | validação e restore real aprovados |

As ferramentas estavam instaladas, mas fora do `PATH`; foram usadas por
caminho absoluto/`PATH` temporário de sessão. O PATH global não foi alterado.

## Ambiente de teste

- origem: `erp_geral_backup_test`;
- restore: `erp_geral_restore_test`;
- ambos isolados e recriados exclusivamente para este gate;
- migration em ambos: `20260911_0012 (head)`;
- banco principal `erp_geral`: não recebeu restore, DROP, limpeza ou operação
  destrutiva.

## Dados de prova

Foram criados somente dados artificiais:

- `Cliente Backup Gate Final`;
- `Fornecedor Backup Gate Final`;
- `Produto Backup Gate Final`, vinculado ao fornecedor;
- arquivo artificial `gate-final-proof.txt` no storage.

Os bancos, o arquivo e o backup temporário foram removidos após a validação.

## Backup

| Verificação | Resultado |
|---|---|
| Script oficial `scripts/backup.ps1` | aprovado |
| `database.dump` | criado, 181.494 bytes |
| `storage.zip` | criado, 336 bytes |
| `pg_restore --list` | dump válido, 486 entradas |
| `.env` e secrets no artefato | não encontrados |
| storage arquivado | `storage/gate-final-proof.txt` presente |

## Restore

| Verificação | Resultado |
|---|---|
| Script oficial `scripts/restore.ps1 -ConfirmRestore` | aprovado |
| destino | `erp_geral_restore_test` |
| `pg_restore` | restore real aprovado |
| migration pós-restore | `20260911_0012 (head)` |
| health | `status`, `process`, `database` e `schema` em `ok` |
| login | usuário restaurado autenticou com sucesso; papel `ADMIN` |
| dados | cliente, fornecedor e produto encontrados; vínculo produto-fornecedor preservado |
| storage | arquivo restaurado e servido por `/uploads` com HTTP 200 |

## Smoke pós-restore

Foram validados com a instalação restaurada:

- login e sessão autenticada;
- clientes;
- fornecedores;
- produtos;
- dashboard/relatório HTTP 200;
- `/api/health`;
- `/api/system-info`;
- arquivo persistente do storage.

## Proteções do restore

O restore sem `-ConfirmRestore` foi recusado com mensagem explícita de
operação destrutiva. O destino foi informado explicitamente e permaneceu
isolado durante todo o ensaio.

## Testes de regressão anteriores preservados

- backend: **123 passed, 0 skipped**;
- frontend: **79 passed**;
- typecheck e build frontend: aprovados;
- Ruff completo: aprovado;
- Git: limpo após o gate.

## Git

Nenhum push, tag ou deploy foi realizado. A atualização desta auditoria e do
contexto do projeto deve ser registrada em um único commit local do gate.

Nenhuma credencial temporária foi persistida.
