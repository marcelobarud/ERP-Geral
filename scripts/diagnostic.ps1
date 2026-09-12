[CmdletBinding()]
param(
    [string]$BackendUrl = 'http://127.0.0.1:8000'
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$backend = Join-Path $projectRoot 'backend'
$alembic = Join-Path $backend '.venv\Scripts\alembic.exe'

Write-Host 'ERP Geral — diagnóstico seguro'
Write-Host "Data: $(Get-Date -Format o)"
Write-Host "Git: $(git -C $projectRoot rev-parse --short HEAD 2>$null)"
Write-Host "Python: $(& python --version 2>&1)"
Write-Host "Node: $(& node --version 2>&1)"
if (Test-Path -LiteralPath $alembic) {
    Set-Location -LiteralPath $backend
    Write-Host "Alembic: $(& $alembic current 2>&1)"
}

$health = Invoke-RestMethod -Uri "$($BackendUrl.TrimEnd('/'))/api/health" -Method Get
Write-Host "Health: status=$($health.status); process=$($health.process); database=$($health.database); schema=$($health.schema); migration=$($health.current_migration); expected=$($health.expected_migration); version=$($health.version)"
Write-Host 'Nenhum valor do .env foi lido ou exibido.'
