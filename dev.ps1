<#
.SYNOPSIS
    Backend(uvicorn) / Frontend(vite) / Nginx를 한 번에 기동·종료·상태체크·로그확인한다.

.USAGE
    .\dev.ps1 start            # 세 서버 모두 기동 (기본 dev 환경)
    .\dev.ps1 stop             # 세 서버 모두 종료
    .\dev.ps1 status           # 세 서버 상태 확인
    .\dev.ps1 restart          # stop 후 start
    .\dev.ps1 start -Env prod  # 운영 모드 (vite 대신 Frontend/dist를 nginx가 직접 서빙)

    .\dev.ps1 logs                                # 전체 로그 마지막 부분 출력
    .\dev.ps1 logs -Service backend               # 백엔드 로그만
    .\dev.ps1 logs -Service nginx-error -Follow   # nginx 에러 로그 실시간 tail (Ctrl+C로 종료)
#>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet("start", "stop", "status", "restart", "logs")]
    [string]$Action,

    [ValidateSet("dev", "prod")]
    [string]$Env = "dev",

    [ValidateSet("all", "backend", "frontend", "nginx", "nginx-access", "nginx-error")]
    [string]$Service = "all",

    [switch]$Follow,

    [int]$Tail = 40
)

$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$BackendDir = Join-Path $ProjectRoot "Backend"
$FrontendDir = Join-Path $ProjectRoot "Frontend"

$RunDir = Join-Path $ProjectRoot ".run"
if (-not (Test-Path $RunDir)) {
    New-Item -ItemType Directory -Path $RunDir | Out-Null
}
$BackendPidFile = Join-Path $RunDir "backend.pid"
$FrontendPidFile = Join-Path $RunDir "frontend.pid"
$BackendLog = Join-Path $RunDir "backend.log"
$FrontendLog = Join-Path $RunDir "frontend.log"
$NginxAccessLog = Join-Path $ProjectRoot "logs\access.log"
$NginxErrorLog = Join-Path $ProjectRoot "logs\error.log"

$NginxConf = Join-Path $ProjectRoot "nginx\$Env.conf"

# winget 설치 직후에는 PATH가 새 셸에 아직 반영되지 않았을 수 있어 fallback 경로를 둔다.
$NginxFallback = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\nginxinc.nginx_Microsoft.Winget.Source_8wekyb3d8bbwe\nginx-1.31.3\nginx.exe"

function Get-NginxExe {
    $cmd = Get-Command nginx -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    if (Test-Path $NginxFallback) { return $NginxFallback }
    throw "nginx.exe를 찾을 수 없습니다. PATH를 확인하거나 이 스크립트의 `$NginxFallback 값을 수정하세요."
}

function Get-PortState([int]$Port) {
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($conn) { return "LISTEN" } else { return "닫힘" }
}

function Wait-Port([int]$Port, [int]$TimeoutSec = 15) {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
            return $true
        }
        Start-Sleep -Milliseconds 300
    }
    return $false
}

function Get-AlivePidFromFile([string]$PidFile) {
    if (-not (Test-Path $PidFile)) { return $null }
    $procId = Get-Content $PidFile -ErrorAction SilentlyContinue
    if (-not $procId) { return $null }
    if (Get-Process -Id $procId -ErrorAction SilentlyContinue) { return $procId }
    return $null
}

function Start-Backend {
    $alive = Get-AlivePidFromFile $BackendPidFile
    if ($alive) {
        Write-Host "[backend]  이미 실행 중입니다 (PID $alive)"
        return
    }
    $proc = Start-Process -FilePath "uv" `
        -ArgumentList "run", "python", "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000" `
        -WorkingDirectory $BackendDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput $BackendLog `
        -RedirectStandardError "$BackendLog.err" `
        -PassThru
    $proc.Id | Out-File -FilePath $BackendPidFile -Encoding ascii
    if (Wait-Port 8000) {
        Write-Host "[backend]  기동됨 (PID $($proc.Id), :8000), 로그: $BackendLog"
    }
    else {
        Write-Host "[backend]  기동 시도했지만 :8000 응답이 없습니다. $BackendLog 를 확인하세요." -ForegroundColor Yellow
    }
}

function Start-Frontend {
    if ($Env -eq "prod") {
        Write-Host "[frontend] prod 모드에서는 vite를 띄우지 않습니다 (nginx가 Frontend/dist를 직접 서빙). 'npm run build'로 최신 빌드인지 확인하세요."
        return
    }
    $alive = Get-AlivePidFromFile $FrontendPidFile
    if ($alive) {
        Write-Host "[frontend] 이미 실행 중입니다 (PID $alive)"
        return
    }
    $proc = Start-Process -FilePath "npm.cmd" `
        -ArgumentList "run", "dev" `
        -WorkingDirectory $FrontendDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput $FrontendLog `
        -RedirectStandardError "$FrontendLog.err" `
        -PassThru
    $proc.Id | Out-File -FilePath $FrontendPidFile -Encoding ascii
    if (Wait-Port 5173) {
        Write-Host "[frontend] 기동됨 (PID $($proc.Id), :5173), 로그: $FrontendLog"
    }
    else {
        Write-Host "[frontend] 기동 시도했지만 :5173 응답이 없습니다. $FrontendLog 를 확인하세요." -ForegroundColor Yellow
    }
}

function Start-Nginx {
    $exe = Get-NginxExe
    # nginx는 실행되면 자체적으로 마스터/워커 프로세스를 데몬화한다. `&`로 직접
    # 호출하면 환경에 따라 제어권 반환이 지연될 수 있어 Start-Process로 fire-and-forget한다.
    Start-Process -FilePath $exe `
        -ArgumentList "-p", "`"$ProjectRoot`"", "-c", "`"$NginxConf`"" `
        -WindowStyle Hidden | Out-Null
    if (Wait-Port 8080 -TimeoutSec 10) {
        Write-Host "[nginx]    기동됨 (:8080, $Env 설정)"
    }
    else {
        Write-Host "[nginx]    기동 실패. logs\error.log 를 확인하세요." -ForegroundColor Red
    }
}

function Stop-ByPidFile([string]$PidFile, [string]$Label) {
    if (-not (Test-Path $PidFile)) {
        Write-Host "[$Label]  실행 중이 아닙니다"
        return
    }
    $procId = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($procId -and (Get-Process -Id $procId -ErrorAction SilentlyContinue)) {
        # npm/uv는 실제 서버(node/python)를 자식 프로세스로 띄우므로 트리 전체를 종료한다.
        taskkill /PID $procId /T /F | Out-Null
        Write-Host "[$Label]  종료됨 (PID $procId)"
    }
    else {
        Write-Host "[$Label]  이미 종료된 상태입니다"
    }
    Remove-Item $PidFile -ErrorAction SilentlyContinue
}

function Stop-Nginx {
    $running = Get-Process nginx -ErrorAction SilentlyContinue
    if (-not $running) {
        Write-Host "[nginx]    실행 중이 아닙니다"
        return
    }
    try {
        $exe = Get-NginxExe
        Start-Process -FilePath $exe `
            -ArgumentList "-p", "`"$ProjectRoot`"", "-c", "`"$NginxConf`"", "-s", "stop" `
            -WindowStyle Hidden | Out-Null
        Start-Sleep -Milliseconds 800
    }
    catch {}
    $remaining = Get-Process nginx -ErrorAction SilentlyContinue
    if ($remaining) {
        $remaining | Stop-Process -Force
    }
    Write-Host "[nginx]    종료됨"
}

function Show-Status {
    Write-Host "=== 서버 상태 ($Env) ==="

    $backendPid = Get-AlivePidFromFile $BackendPidFile
    Write-Host ("[backend]  프로세스: {0,-10} 포트 8000: {1}" -f `
        $(if ($backendPid) { "실행 중(PID $backendPid)" } else { "중지" }), (Get-PortState 8000))

    if ($Env -eq "prod") {
        Write-Host "[frontend] prod 모드 (vite 미사용, Frontend/dist 직접 서빙)"
    }
    else {
        $frontendPid = Get-AlivePidFromFile $FrontendPidFile
        Write-Host ("[frontend] 프로세스: {0,-10} 포트 5173: {1}" -f `
            $(if ($frontendPid) { "실행 중(PID $frontendPid)" } else { "중지" }), (Get-PortState 5173))
    }

    $nginxProcs = Get-Process nginx -ErrorAction SilentlyContinue
    $nginxCount = if ($nginxProcs) { @($nginxProcs).Count } else { 0 }
    Write-Host ("[nginx]    프로세스: {0,-10} 포트 8080: {1}" -f "$nginxCount 개", (Get-PortState 8080))
}

function Get-LogTargets([string]$Filter) {
    $all = @(
        [pscustomobject]@{ Label = "backend"; Path = $BackendLog }
        [pscustomobject]@{ Label = "frontend"; Path = $FrontendLog }
        [pscustomobject]@{ Label = "nginx-access"; Path = $NginxAccessLog }
        [pscustomobject]@{ Label = "nginx-error"; Path = $NginxErrorLog }
    )
    switch ($Filter) {
        "all" { return $all }
        "nginx" { return $all | Where-Object { $_.Label -like "nginx-*" } }
        default { return $all | Where-Object { $_.Label -eq $Filter } }
    }
}

function Show-Logs {
    $targets = @(Get-LogTargets $Service)
    if ($targets.Count -eq 0) {
        Write-Host "알 수 없는 서비스입니다: $Service"
        return
    }

    if ($Follow) {
        if ($targets.Count -gt 1) {
            Write-Host "-Follow는 로그 하나만 대상으로 할 수 있습니다. -Service backend|frontend|nginx-access|nginx-error 중 하나를 지정하세요." -ForegroundColor Yellow
            return
        }
        $t = $targets[0]
        if (-not (Test-Path $t.Path)) {
            Write-Host "[$($t.Label)] 로그 파일이 아직 없습니다: $($t.Path)"
            return
        }
        Write-Host "===== $($t.Label) 실시간 출력 ($($t.Path), Ctrl+C로 종료) ====="
        Get-Content -Path $t.Path -Wait -Tail $Tail
        return
    }

    foreach ($t in $targets) {
        Write-Host ""
        Write-Host "===== $($t.Label) ($($t.Path)) =====" -ForegroundColor Cyan
        if (Test-Path $t.Path) {
            Get-Content -Path $t.Path -Tail $Tail
        }
        else {
            Write-Host "(로그 파일 없음 — 서버가 dev.ps1로 기동된 적이 없을 수 있습니다)"
        }
    }
}

switch ($Action) {
    "start" {
        Start-Backend
        Start-Frontend
        Start-Nginx
    }
    "stop" {
        Stop-Nginx
        Stop-ByPidFile $FrontendPidFile "frontend"
        Stop-ByPidFile $BackendPidFile "backend"
    }
    "restart" {
        Stop-Nginx
        Stop-ByPidFile $FrontendPidFile "frontend"
        Stop-ByPidFile $BackendPidFile "backend"
        Start-Sleep -Seconds 1
        Start-Backend
        Start-Frontend
        Start-Nginx
    }
    "status" {
        Show-Status
    }
    "logs" {
        Show-Logs
    }
}
