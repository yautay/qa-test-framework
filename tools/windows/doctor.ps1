$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

. (Join-Path $PSScriptRoot "common.ps1")

$repoRoot = Get-RepoRoot
Set-Location $repoRoot

$failures = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]

function Write-Check {
    param(
        [string]$Label,
        [bool]$Ok,
        [string]$Details,
        [switch]$WarningOnly
    )

    if ($Ok) {
        Write-Host "[OK]   $Label - $Details" -ForegroundColor Green
        return
    }

    if ($WarningOnly) {
        $warnings.Add($Label) | Out-Null
        Write-Host "[WARN] $Label - $Details" -ForegroundColor Yellow
        return
    }

    $failures.Add($Label) | Out-Null
    Write-Host "[FAIL] $Label - $Details" -ForegroundColor Red
}

$uvExe = Resolve-UvExe
Write-Check -Label "uv" -Ok ([bool]$uvExe) -Details ($(if ($uvExe) { $uvExe } else { "not installed" }))

$lockFile = Get-RepoPath "uv.lock"
Write-Check -Label "uv.lock" -Ok (Test-Path $lockFile) -Details $lockFile

$venvPython = Get-VenvPythonPath
$hasVenv = Test-Path $venvPython
Write-Check -Label ".venv" -Ok $hasVenv -Details $venvPython

if ($hasVenv) {
    $pythonVersion = (& $venvPython --version).Trim()
    $expectedVersion = "Python $(Get-RequiredPythonVersion)"
    Write-Check -Label "python" -Ok ($pythonVersion -eq $expectedVersion) -Details $pythonVersion
}

$playwrightCachePaths = @(
    (Join-Path $env:LOCALAPPDATA "ms-playwright"),
    (Join-Path $env:USERPROFILE "AppData\Local\ms-playwright")
) | Select-Object -Unique

$playwrightInstalled = $false
foreach ($cachePath in $playwrightCachePaths) {
    if ($cachePath -and (Test-Path $cachePath)) {
        $chromiumDirs = Get-ChildItem -Path $cachePath -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like "chromium-*" }
        if ($chromiumDirs) {
            $playwrightInstalled = $true
            break
        }
    }
}
Write-Check -Label "playwright chromium" -Ok $playwrightInstalled -Details "Run bootstrap without -SkipPlaywright if missing." -WarningOnly

$uiDistIndex = Get-RepoPath "framework/visual/ui/dist/index.html"
Write-Check -Label "report ui dist" -Ok (Test-Path $uiDistIndex) -Details $uiDistIndex

$dockerExe = Get-Command docker -ErrorAction SilentlyContinue
Write-Check -Label "docker" -Ok ([bool]$dockerExe) -Details ($(if ($dockerExe) { $dockerExe.Source } else { "required only for MinIO/grid helpers" })) -WarningOnly

if ($warnings.Count -gt 0) {
    Write-Host "Warnings: $($warnings -join ', ')" -ForegroundColor Yellow
}

if ($failures.Count -gt 0) {
    throw "Doctor found blocking issues: $($failures -join ', ')"
}

Write-Host "Doctor finished without blocking issues." -ForegroundColor Green
