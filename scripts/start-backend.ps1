[CmdletBinding()]
param(
    [string]$Host = '127.0.0.1',
    [int]$Port = 8000,
    [switch]$AccessLog
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backend = Join-Path $projectRoot 'backend'
$python = Join-Path $backend '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) {
    throw "Ambiente Python não encontrado em $python. Execute scripts/install.ps1."
}
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot '.env'))) {
    throw 'Arquivo .env não encontrado na raiz do ERP Geral.'
}

Set-Location -LiteralPath $backend
$arguments = @('-m', 'uvicorn', 'app.main:app', '--host', $Host, '--port', $Port)
if ($AccessLog) { $arguments += '--access-log' } else { $arguments += '--no-access-log' }
& $python @arguments
