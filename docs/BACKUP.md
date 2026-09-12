# Backup, restore e rollback — ERP Geral

O backup de uma instalação precisa preservar o banco PostgreSQL e o diretório
de armazenamento do ERP. Atualmente esse armazenamento é
`backend/storage`, que contém a branding enviada pela interface. Não inclua
`.env` em arquivos compartilhados: ele contém credenciais e secrets.

## Backup

No Windows, com PostgreSQL Client instalado:

```powershell
.\scripts\backup.ps1
```

O script lê `DATABASE_URL` do `.env` sem exibi-la, cria uma pasta com timestamp
em `backups/`, salva `database.dump` em formato custom e inclui `storage.zip`
quando o diretório de storage existir. Para uma pasta externa:

```powershell
.\scripts\backup.ps1 -OutputDirectory 'E:\Backups\ERP Geral'
```

Para VPS, agende o equivalente com `pg_dump --format=custom` e arquive o
storage. Mantenha cópias fora do servidor e teste a restauração periodicamente.

## Restore

Restauração substitui objetos do banco e arquivos persistentes. Faça uma cópia
do estado atual, pare o backend e execute somente após conferir o diretório do
backup e o banco de destino:

```powershell
.\scripts\restore.ps1 `
  -BackupDirectory 'E:\Backups\ERP Geral\erp-geral-20260912-120000' `
  -DatabaseUrl 'postgresql+psycopg://usuario:SENHA@host:5432/erp_geral' `
  -ConfirmRestore
```

O parâmetro `-ConfirmRestore` é obrigatório. Nunca aponte o restore para o
banco de produção sem confirmar o destino; faça primeiro um ensaio em um banco
isolado com sufixo `_restore_test`.

Após restaurar, execute `alembic upgrade head`, reinicie o backend, confirme
`/api/health` e realize o smoke test de login, clientes, produtos e uma leitura
de relatório. O arquivo `.env` não é restaurado automaticamente.

## Atualização e rollback

O fluxo de atualização é:

```text
backup → parar aplicação → atualizar código → dependências
→ migrations → build frontend → iniciar → health → smoke
```

O script técnico executa o backup, migrations e build:

```powershell
.\scripts\update.ps1
```

O operador controla o stop/start do serviço para evitar que uma versão antiga
execute durante uma migration. Se a versão nova falhar, preserve os logs,
pare-a, restaure o backup em um banco isolado ou no destino autorizado e
republique o build anterior. Rollback de banco nunca deve ser feito apagando
migrations versionadas: restaure um backup compatível e confirme o health antes
de liberar o acesso.
