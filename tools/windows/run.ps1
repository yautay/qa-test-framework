$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

param(
    [Parameter(Position = 0)]
    [string]$Command = "doctor",

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$CommandArgs = @()
)

. (Join-Path $PSScriptRoot "common.ps1")

$repoRoot = Get-RepoRoot
Set-Location $repoRoot

function Ensure-BootstrapReady {
    if (-not (Test-Path (Get-VenvPythonPath))) {
        throw "Missing .venv. Run tools/windows/bootstrap.ps1 first."
    }
    [void](Ensure-Uv)
}

$normalized = $Command.Trim().ToLowerInvariant()

switch ($normalized) {
    "bootstrap" {
        & (Join-Path $PSScriptRoot "bootstrap.ps1") @CommandArgs
        break
    }
    "doctor" {
        & (Join-Path $PSScriptRoot "doctor.ps1") @CommandArgs
        break
    }
    "sync" {
        Ensure-RepoEnvironment
        break
    }
    "report" {
        Ensure-BootstrapReady
        $args = @("-m", "framework.reporting.report_server")
        $args += $CommandArgs
        Invoke-RepoPython -Arguments $args
        break
    }
    "verify" {
        Ensure-BootstrapReady
        Invoke-RepoPython -Arguments @("framework/pytest_discovery_guard.py")
        Invoke-RepoPython -Arguments @("tools/scenarios/verify_scenarios.py")
        break
    }
    "test" {
        Ensure-BootstrapReady
        Invoke-RepoPython -Arguments @("-m", "pytest", "-q")
        break
    }
    "aso" {
        Ensure-BootstrapReady
        Invoke-RepoPython -Arguments @("-m", "pytest", "-m", "aso", "-q")
        break
    }
    "api" {
        Ensure-BootstrapReady
        Invoke-RepoPython -Arguments @("-m", "pytest", "-m", "api", "-q")
        break
    }
    "e2e" {
        Ensure-BootstrapReady
        Invoke-RepoPython -Arguments @("-m", "pytest", "-m", "e2e", "-q")
        break
    }
    "visual" {
        Ensure-BootstrapReady
        Invoke-RepoPython -Arguments @("-m", "pytest", "-m", "visual", "-q")
        break
    }
    "smoke" {
        Ensure-BootstrapReady
        Invoke-RepoPython -Arguments @("-m", "pytest", "-m", "smoke", "-q")
        break
    }
    "lint" {
        Ensure-BootstrapReady
        Invoke-RepoPython -Arguments @("-m", "ruff", "check", "qa", "framework", "tools")
        break
    }
    "format-check" {
        Ensure-BootstrapReady
        Invoke-RepoPython -Arguments @("-m", "black", "--check", "qa", "framework", "tools")
        break
    }
    "typecheck" {
        Ensure-BootstrapReady
        Invoke-RepoPython -Arguments @("-m", "mypy", "qa", "framework", "tools")
        break
    }
    "security" {
        Ensure-BootstrapReady
        Invoke-RepoPython -Arguments @("-m", "bandit", "-r", "-x", "qa", "--skip", "B101,B105,B106,B110,B112,B404,B603,B607,B311", "framework", "tools")
        Invoke-RepoPython -Arguments @("-m", "pip_audit")
        break
    }
    default {
        throw "Unknown command '$Command'. Supported: bootstrap, doctor, sync, report, verify, test, aso, api, e2e, visual, smoke, lint, format-check, typecheck, security"
    }
}
