[CmdletBinding()]
param(
    [string]$BindHost = '127.0.0.1',
    [int]$Port = 4173
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$frontend = Join-Path $projectRoot 'frontend'
$build = Join-Path $frontend 'dist'
$python = Get-Command python -ErrorAction SilentlyContinue

if (-not $python) { throw 'Python não encontrado no PATH.' }
if (-not (Test-Path -LiteralPath (Join-Path $build 'index.html'))) {
    throw "Build do frontend não encontrado em $build. Execute npm run build em frontend."
}

Set-Location -LiteralPath $projectRoot
& $python.Source scripts\static_server.py --directory $build --host $BindHost --port $Port
