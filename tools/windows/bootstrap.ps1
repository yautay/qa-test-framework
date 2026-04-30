param(
    [switch]$SkipPlaywright,
    [switch]$Reinstall
)

$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

. (Join-Path $PSScriptRoot "common.ps1")

$repoRoot = Get-RepoRoot
Set-Location $repoRoot

if ($Reinstall -and (Test-Path (Get-RepoPath ".venv"))) {
    Remove-Item -Recurse -Force (Get-RepoPath ".venv")
}

Ensure-RepoEnvironment

if (-not $SkipPlaywright) {
    $pythonVersion = Get-RequiredPythonVersion
    Invoke-Uv -Arguments @(
        "run",
        "--frozen",
        "--managed-python",
        "--python",
        $pythonVersion,
        "--extra",
        "dev",
        "--",
        "python",
        "-m",
        "playwright",
        "install",
        "chromium"
    )
}

Write-Host "Bootstrap completed." -ForegroundColor Green
Write-Host "Repo root: $repoRoot"
Write-Host "Python: $(Get-RequiredPythonVersion)"
Write-Host "Venv: $(Get-RepoPath '.venv')"
Write-Host "Next: powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 doctor"
