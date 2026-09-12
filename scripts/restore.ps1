[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)]
    [string]$BackupDirectory,
    [Parameter(Mandatory)]
    [string]$DatabaseUrl,
    [switch]$ConfirmRestore
)

$ErrorActionPreference = 'Stop'
if (-not $ConfirmRestore) {
    throw 'Restauração é destrutiva. Revise o backup e execute novamente com -ConfirmRestore.'
}

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Comando obrigatório não encontrado: $Name"
    }
}

function Get-PostgresConnection([string]$Value) {
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

$backup = [IO.Path]::GetFullPath($BackupDirectory)
$dump = Join-Path $backup 'database.dump'
if (-not (Test-Path -LiteralPath $dump)) { throw "database.dump não encontrado em $backup" }
$database = Get-PostgresConnection $DatabaseUrl
Require-Command 'pg_restore'

if ($PSCmdlet.ShouldProcess($database.Dsn, 'restaurar o banco do backup')) {
    $env:PGPASSWORD = $database.Password
    try {
        & pg_restore --clean --if-exists --exit-on-error --no-owner --no-acl --dbname $database.Dsn $dump
    } finally {
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    }
}

$storageZip = Join-Path $backup 'storage.zip'
if (Test-Path -LiteralPath $storageZip) {
    $projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
    $storage = Join-Path $projectRoot 'backend\storage'
    if ($PSCmdlet.ShouldProcess($storage, 'substituir o armazenamento persistente')) {
        Expand-Archive -LiteralPath $storageZip -DestinationPath (Split-Path $storage) -Force
    }
}
Write-Host 'Restauração concluída. Execute migrations pendentes e o smoke test antes de liberar o sistema.'
