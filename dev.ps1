param(
  [int]$BackendPort = 8000,
  [int]$FrontendPort = 5173,
  [switch]$SkipInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
if (-not $root) { $root = (Get-Location).Path }
$frontendDir = Join-Path $root 'frontend'
$BackendHost = if ($env:BACKEND_HOST) { $env:BACKEND_HOST } else { '0.0.0.0' }
$FrontendHost = if ($env:VITE_HOST) { $env:VITE_HOST } else { '0.0.0.0' }

function Get-NpmPath {
  $npmCmd = Get-Command 'npm.cmd' -ErrorAction SilentlyContinue
  if ($npmCmd) { return $npmCmd.Source }
  $npm = Get-Command 'npm' -ErrorAction SilentlyContinue
  if ($npm) { return $npm.Source }
  throw 'npm not found on PATH. Please install Node.js or add npm to PATH.'
}

function Install-BackendDeps {
  Write-Host 'Installing backend dependencies...'
  python -m pip install --upgrade pip | Write-Host
  python -m pip install -r (Join-Path $root 'backend/requirements.txt')
}

function Install-FrontendDeps {
  if (-not (Test-Path (Join-Path $frontendDir 'package.json'))) { return }
  if ($SkipInstall) { return }
  $nm = Join-Path $frontendDir 'node_modules'
  $needInstall = $true
  if (Test-Path $nm) {
    $markedDir = Join-Path $nm 'marked'
    $dompurifyDir = Join-Path $nm 'dompurify'
    if ((Test-Path $markedDir) -and (Test-Path $dompurifyDir)) {
      $needInstall = $false
    }
  }
  if (-not $needInstall) { return }
  Write-Host 'Installing/updating frontend dependencies (npm install)...'
  Push-Location $frontendDir
  try {
    npm install
  } finally {
    Pop-Location
  }
}

function Start-Frontend {
  if (-not (Test-Path (Join-Path $frontendDir 'package.json'))) {
    Write-Warning 'frontend/ not found; skipping frontend start.'
    return $null
  }
  Write-Host ("Starting frontend (Vite) on http://{0}:{1} ..." -f $FrontendHost, $FrontendPort)
  $npmExe = Get-NpmPath
  $npmArgs = @('run','dev','--','--port',"$FrontendPort",'--host',"$FrontendHost")
  $p = Start-Process -FilePath $npmExe -ArgumentList $npmArgs -WorkingDirectory $frontendDir -PassThru -NoNewWindow
  return $p
}

function Start-Backend {
  Write-Host ("Starting backend (Uvicorn) on http://{0}:{1} ..." -f $BackendHost, $BackendPort)
  $args = @('-m','uvicorn','backend.app.main:app','--reload','--host',"$BackendHost",'--port',"$BackendPort")
  $p = Start-Process -FilePath 'python' -ArgumentList $args -WorkingDirectory $root -PassThru -NoNewWindow
  return $p
}

# Main
if (-not $SkipInstall) { Install-BackendDeps }
Install-FrontendDeps

$frontendProc = Start-Frontend
$backendProc = Start-Backend

Write-Host '---'
Write-Host ("Frontend: http://{0}:{1}" -f $FrontendHost, $FrontendPort)
Write-Host ("Backend : http://{0}:{1}" -f $BackendHost, $BackendPort)
Write-Host 'Press Ctrl+C to stop both.'
Write-Host '---'

# Handle Ctrl+C to stop both processes
$handler = Register-EngineEvent -SourceIdentifier ConsoleCancelEvent -Action {
  try {
    if ($backendProc -and !$backendProc.HasExited) { Stop-Process -Id $backendProc.Id -Force }
    if ($frontendProc -and !$frontendProc.HasExited) { Stop-Process -Id $frontendProc.Id -Force }
  } catch {}
}

try {
  # Wait for either to exit, then stop the other
  Wait-Process -Id @($backendProc.Id, $frontendProc.Id) -ErrorAction SilentlyContinue
} finally {
  if ($backendProc -and !$backendProc.HasExited) { Stop-Process -Id $backendProc.Id -Force }
  if ($frontendProc -and !$frontendProc.HasExited) { Stop-Process -Id $frontendProc.Id -Force }
  if ($handler) { Unregister-Event -SourceIdentifier ConsoleCancelEvent -ErrorAction SilentlyContinue }
}
