[CmdletBinding()]
param(
    [string]$DatabaseUrl = '',
    [string]$BackupDirectory = ''
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backend = Join-Path $projectRoot 'backend'
$python = Join-Path $backend '.venv\Scripts\python.exe'
$alembic = Join-Path $backend '.venv\Scripts\alembic.exe'

if (-not (Test-Path -LiteralPath $python)) { throw 'Ambiente Python não encontrado. Execute scripts/install.ps1.' }
if (-not (Test-Path -LiteralPath $alembic)) { throw 'Alembic não encontrado no ambiente virtual.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot '.env'))) { throw '.env não encontrado na raiz do projeto.' }

$backupArgs = @('-OutputDirectory', $(if ($BackupDirectory) { $BackupDirectory } else { Join-Path $projectRoot 'backups' }))
if ($DatabaseUrl) { $backupArgs += @('-DatabaseUrl', $DatabaseUrl) }
& (Join-Path $PSScriptRoot 'backup.ps1') @backupArgs

Set-Location -LiteralPath $backend
& $alembic upgrade head
& $alembic current

Set-Location -LiteralPath (Join-Path $projectRoot 'frontend')
& npm ci
& npm run build

Write-Host 'Atualização técnica concluída. Reinicie o backend, verifique /api/health e execute o smoke test antes de liberar o acesso.'
