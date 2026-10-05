param(
    [string]$Neo4jHome = "D:\bishe\tools\neo4j-community-2026.04.0"
)

$ErrorActionPreference = "Stop"

function Start-NamedService {
    param(
        [string]$Name,
        [string]$DisplayName
    )

    $service = Get-Service -Name $Name -ErrorAction SilentlyContinue
    if (-not $service) {
        Write-Host "$DisplayName service is not installed."
        return $false
    }

    if ($service.Status -ne "Running") {
        Start-Service -Name $Name
        $service.WaitForStatus("Running", "00:00:30")
    }

    Write-Host "$DisplayName is running."
    return $true
}

$redisStarted = Start-NamedService -Name "Redis" -DisplayName "Redis"

if ($redisStarted) {
    $redisCli = "C:\Program Files\Redis\redis-cli.exe"
    if (Test-Path $redisCli) {
        & $redisCli ping
    }
}

$neo4jStarted = Start-NamedService -Name "neo4j" -DisplayName "Neo4j"

if (-not $neo4jStarted) {
    $neo4jBat = Join-Path $Neo4jHome "bin\neo4j.bat"
    if (-not (Test-Path $neo4jBat)) {
        throw "Neo4j executable not found: $neo4jBat"
    }

    & $neo4jBat start
}

$neo4jStatus = Join-Path $Neo4jHome "bin\neo4j.bat"
if (Test-Path $neo4jStatus) {
    & $neo4jStatus status
}
