$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

function Get-RepoRoot {
    return [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
}

function Get-RepoPath {
    param([string]$RelativePath)

    return [System.IO.Path]::GetFullPath((Join-Path (Get-RepoRoot) $RelativePath))
}

function Get-RequiredPythonVersion {
    $versionFile = Get-RepoPath ".python-version"
    if (-not (Test-Path $versionFile)) {
        throw "Missing .python-version in repository root."
    }

    $version = (Get-Content -Path $versionFile -TotalCount 1).Trim()
    if ([string]::IsNullOrWhiteSpace($version)) {
        throw ".python-version is empty."
    }

    return $version
}

function Get-VenvPythonPath {
    return Get-RepoPath ".venv\Scripts\python.exe"
}

function Refresh-SessionPath {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $parts = @($machinePath, $userPath) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    if ($parts.Count -gt 0) {
        $env:Path = ($parts -join ";")
    }
}

function Test-UvExe {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path $Path)) {
        return $false
    }

    try {
        & $Path --version *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Resolve-UvExe {
    $candidatePatterns = @(
        (Join-Path $env:USERPROFILE ".local\bin\uv.exe"),
        (Join-Path $env:USERPROFILE ".cargo\bin\uv.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\uv\uv.exe"),
        (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\uv.exe"),
        (Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\uv.exe"),
        (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages\astral-sh.uv_Microsoft.Winget.Source_*\uv.exe")
    )

    $candidates = @()
    foreach ($pattern in $candidatePatterns) {
        if (-not [string]::IsNullOrWhiteSpace($pattern)) {
            $candidates += @(Get-Item -Path $pattern -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
        }
    }

    $commands = @(Get-Command uv -All -ErrorAction SilentlyContinue)
    foreach ($cmd in $commands) {
        if ($cmd -and $cmd.Source) {
            $candidates += $cmd.Source
        }
    }

    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if (Test-UvExe $candidate) {
            return $candidate
        }
    }

    return $null
}

function Install-Uv {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        & $winget.Source install --id astral-sh.uv -e --accept-package-agreements --accept-source-agreements
        Refresh-SessionPath
        $uvExe = Resolve-UvExe
        if ($uvExe) {
            return $uvExe
        }
    }

    $response = Invoke-WebRequest -UseBasicParsing -Uri "https://astral.sh/uv/install.ps1"
    Invoke-Expression $response.Content
    Refresh-SessionPath
    $uvExe = Resolve-UvExe
    if ($uvExe) {
        return $uvExe
    }

    throw "uv installation failed. Install astral-sh/uv and rerun bootstrap."
}

function Ensure-Uv {
    $uvExe = Resolve-UvExe
    if ($uvExe) {
        return $uvExe
    }

    Write-Host "uv not found. Installing..." -ForegroundColor Cyan
    return Install-Uv
}

function Invoke-Uv {
    param([string[]]$Arguments)

    $uvExe = Ensure-Uv
    & $uvExe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "uv command failed with exit code $LASTEXITCODE"
    }
}

function Invoke-RepoPython {
    param([string[]]$Arguments)

    $pythonVersion = Get-RequiredPythonVersion
    $uvArgs = @(
        "run",
        "--frozen",
        "--managed-python",
        "--python",
        $pythonVersion,
        "--extra",
        "dev",
        "--",
        "python"
    )
    $uvArgs += $Arguments
    Invoke-Uv -Arguments $uvArgs
}

function Ensure-RepoEnvironment {
    $pythonVersion = Get-RequiredPythonVersion
    Invoke-Uv -Arguments @("python", "install", $pythonVersion)
    Invoke-Uv -Arguments @("sync", "--frozen", "--managed-python", "--python", $pythonVersion, "--extra", "dev")
}
