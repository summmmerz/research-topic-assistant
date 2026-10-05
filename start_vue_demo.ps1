param(
    [switch]$NoBrowser,
    [switch]$Install
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $ProjectRoot "frontend"
$BackendEntry = Join-Path $ProjectRoot "web_app\run.py"
$DemoUrl = "http://127.0.0.1:5173/vue/"

function Require-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$InstallHint
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name was not found. $InstallHint"
    }
}

if (-not (Test-Path -LiteralPath $FrontendDir)) {
    throw "Frontend directory not found: $FrontendDir"
}

if (-not (Test-Path -LiteralPath $BackendEntry)) {
    throw "Backend entry not found: $BackendEntry"
}

Require-Command -Name "python" -InstallHint "Install Python and add it to PATH."
Require-Command -Name "npm" -InstallHint "Install Node.js and add npm to PATH."

$NodeModules = Join-Path $FrontendDir "node_modules"
if ($Install -or -not (Test-Path -LiteralPath $NodeModules)) {
    Write-Host "Installing frontend dependencies..."
    Push-Location $FrontendDir
    try {
        npm install
    }
    finally {
        Pop-Location
    }
}

Write-Host "Starting Flask backend on http://127.0.0.1:5000 ..."
Start-Process `
    -FilePath "powershell.exe" `
    -WorkingDirectory $ProjectRoot `
    -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command", "python web_app\run.py --host 127.0.0.1 -p 5000 --no-check"
    )

Write-Host "Starting Vue demo on $DemoUrl ..."
Start-Process `
    -FilePath "powershell.exe" `
    -WorkingDirectory $FrontendDir `
    -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-Command", "npm run dev"
    )

if (-not $NoBrowser) {
    Start-Sleep -Seconds 3
    Start-Process $DemoUrl
}

Write-Host ""
Write-Host "Vue demo: $DemoUrl"
Write-Host "Backend API: http://127.0.0.1:5000/api/health"
Write-Host "Close the two service windows to stop the demo."
