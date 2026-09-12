[CmdletBinding()]
param(
    [switch]$SkipMigrations,
    [switch]$SkipFrontendBuild
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $projectRoot

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Comando obrigatório não encontrado: $Name"
    }
}

Require-Command 'python'
Require-Command 'npm'

$envPath = Join-Path $projectRoot '.env'
if (-not (Test-Path -LiteralPath $envPath)) {
    Copy-Item -LiteralPath (Join-Path $projectRoot '.env.example') -Destination $envPath
    Write-Warning "Arquivo .env criado a partir do exemplo. Preencha os placeholders antes de continuar."
    throw "Instalação pausada: configure .env e execute o script novamente."
}

$backend = Join-Path $projectRoot 'backend'
$python = Join-Path $backend '.venv\Scripts\python.exe'
$alembic = Join-Path $backend '.venv\Scripts\alembic.exe'

if (-not (Test-Path -LiteralPath $python)) {
    & python -m venv (Join-Path $backend '.venv')
}

& $python -m pip install --upgrade pip
& $python -m pip install (Join-Path $backend '.')

if (-not $SkipMigrations) {
    Set-Location -LiteralPath $backend
    & $alembic upgrade head
    & $alembic current
}

if (-not $SkipFrontendBuild) {
    Set-Location -LiteralPath (Join-Path $projectRoot 'frontend')
    & npm ci
    & npm run build
}

Write-Host 'Instalação técnica concluída. Crie o administrador pelo bootstrap e siga docs/PRODUCTION.md.'
