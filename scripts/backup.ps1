[CmdletBinding()]
param(
    [string]$OutputDirectory = '',
    [string]$DatabaseUrl = ''
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$storage = Join-Path $projectRoot 'backend\storage'

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Comando obrigatório não encontrado: $Name"
    }
}

function Read-EnvValue([string]$Name) {
    $envFile = Join-Path $projectRoot '.env'
    if (-not (Test-Path -LiteralPath $envFile)) { return '' }
    $line = Get-Content -LiteralPath $envFile | Where-Object {
        $_ -match "^\s*$Name\s*="
    } | Select-Object -First 1
    if (-not $line) { return '' }
    return ($line -replace "^\s*$Name\s*=\s*", '').Trim().Trim('"').Trim("'")
}

function Get-PostgresConnection([string]$Value) {
    if (-not $Value) { throw 'Informe -DatabaseUrl ou configure DATABASE_URL no .env.' }
    $normalized = $Value -replace '^postgresql\+psycopg://', 'postgresql://'
    $uri = [Uri]$normalized
    $userInfo = $uri.UserInfo.Split(':', 2)
    if ($userInfo.Count -lt 2) { throw 'DATABASE_URL precisa conter usuário e senha.' }
    $safeDsn = "postgresql://$([Uri]::EscapeDataString($userInfo[0]))@$($uri.Host)"
    if ($uri.Port -gt 0) { $safeDsn += ":$($uri.Port)" }
    $safeDsn += $uri.AbsolutePath
    if ($uri.Query) { $safeDsn += $uri.Query }
    return [pscustomobject]@{
        Dsn = $safeDsn
        Password = [Uri]::UnescapeDataString($userInfo[1])
    }
}

Require-Command 'pg_dump'
Require-Command 'Compress-Archive'
$database = Get-PostgresConnection ($DatabaseUrl.Trim() | ForEach-Object { if ($_ ) { $_ } else { Read-EnvValue 'DATABASE_URL' } })
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$targetRoot = if ($OutputDirectory) { [IO.Path]::GetFullPath($OutputDirectory) } else { Join-Path $projectRoot 'backups' }
New-Item -ItemType Directory -Force -Path $targetRoot | Out-Null
$target = Join-Path $targetRoot "erp-geral-$timestamp"
New-Item -ItemType Directory -Force -Path $target | Out-Null

$env:PGPASSWORD = $database.Password
try {
    & pg_dump --format=custom --no-owner --no-acl --file (Join-Path $target 'database.dump') --dbname $database.Dsn
} finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}

if (Test-Path -LiteralPath $storage) {
    Compress-Archive -Path $storage -DestinationPath (Join-Path $target 'storage.zip') -CompressionLevel Optimal
}
Write-Host "Backup criado em $target"
