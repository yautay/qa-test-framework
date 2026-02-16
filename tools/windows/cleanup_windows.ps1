param()

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Yellow
}

function Ask-YesNo {
    param(
        [string]$Question,
        [bool]$Default = $false
    )

    $suffix = if ($Default) { "[Y/n]" } else { "[y/N]" }
    $answer = Read-Host "$Question $suffix"
    if ([string]::IsNullOrWhiteSpace($answer)) {
        return $Default
    }
    return $answer.Trim().ToLowerInvariant() -in @("y", "yes")
}

function Remove-IfExists {
    param([string]$PathToRemove)
    if (Test-Path $PathToRemove) {
        Remove-Item -Recurse -Force $PathToRemove
        Write-Host "Removed: $PathToRemove"
    } else {
        Write-Host "Not found (skip): $PathToRemove"
    }
}

function Is-UnderRepo {
    param(
        [string]$RepoRoot,
        [string]$CandidatePath
    )

    if ([string]::IsNullOrWhiteSpace($CandidatePath)) {
        return $false
    }

    $repo = [System.IO.Path]::GetFullPath($RepoRoot)
    $candidate = [System.IO.Path]::GetFullPath($CandidatePath)
    return $candidate.StartsWith($repo, [System.StringComparison]::OrdinalIgnoreCase)
}

try {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $repoRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
    Set-Location $repoRoot

    Write-Host "netQArner - Windows cleanup wizard" -ForegroundColor Green
    Write-Host "Repository: $repoRoot"

    $statePath = Join-Path $repoRoot ".windows_setup_state.json"
    $pythonDir = Join-Path $repoRoot ".python313"
    $venvDir = Join-Path $repoRoot ".venv"

    if (Test-Path $statePath) {
        try {
            $state = Get-Content $statePath -Raw | ConvertFrom-Json
            if ($state.python_dir) { $pythonDir = [string]$state.python_dir }
            if ($state.venv_dir) { $venvDir = [string]$state.venv_dir }
        } catch {
            Write-Host "Warning: could not parse $statePath, using defaults." -ForegroundColor DarkYellow
        }
    }

    Write-Host "Python directory to remove: $pythonDir"
    Write-Host "Venv directory to remove:   $venvDir"

    if (-not (Ask-YesNo -Question "Proceed with cleanup of Python + virtual environment?" -Default $false)) {
        Write-Host "Cleanup cancelled."
        exit 0
    }

    Write-Step "Removing virtual environment"
    if (Is-UnderRepo -RepoRoot $repoRoot -CandidatePath $venvDir) {
        Remove-IfExists -PathToRemove $venvDir
    } else {
        Write-Host "Skip venv removal (outside repo): $venvDir" -ForegroundColor DarkYellow
    }

    Write-Step "Removing local Python installation"
    if (Is-UnderRepo -RepoRoot $repoRoot -CandidatePath $pythonDir) {
        Remove-IfExists -PathToRemove $pythonDir
    } else {
        Write-Host "Skip Python removal (outside repo): $pythonDir" -ForegroundColor DarkYellow
    }

    if (Ask-YesNo -Question "Remove temporary installer directory (.tmp)?" -Default $true) {
        Remove-IfExists -PathToRemove (Join-Path $repoRoot ".tmp")
    }

    Remove-IfExists -PathToRemove $statePath

    Write-Step "Cleanup completed"
}
catch {
    Write-Host "`nCleanup failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
