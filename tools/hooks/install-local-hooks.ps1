$ErrorActionPreference = "Stop"

$repoRoot = (& git rev-parse --show-toplevel).Trim()
if ([string]::IsNullOrWhiteSpace($repoRoot)) {
    throw "Cannot resolve repository root from git."
}

$hooksDir = Join-Path $repoRoot ".git\hooks"
$sourceHook = Join-Path $repoRoot "tools\hooks\pre-commit-aso.sh"
$targetHook = Join-Path $hooksDir "pre-commit"

New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null
Copy-Item -Path $sourceHook -Destination $targetHook -Force

Write-Host "Installed local pre-commit hook: $targetHook"
Write-Host "It runs: python -m pytest -m aso -q"
