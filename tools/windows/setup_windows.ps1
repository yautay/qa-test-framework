$ErrorActionPreference = "Stop"

# ============================================================
# netQArner - Windows setup wizard (Python + venv + deps)
# + Git install (optional) + git config user.name/user.email
# ASCII-only output to avoid encoding/parser issues.
# ============================================================

# -------------------------
# Flavor / UX
# -------------------------

function Show-QAFlavor {
    $lines = @(
        "The dark guardian asks: how are the tests going...",
        "Rubber duck whispers: trust me.",
        "Night watcher: every log tells a story.",
        "Silent CI watches from the shadows.",
        "Duck says: read the stacktrace slowly.",
        "Guardian nods at passing assertions.",
        "Somewhere a flaky test wakes up.",
        "The pipeline breathes quietly in the dark.",
        "A timeout waits patiently at the edge of night.",
        "The duck stares silently at your breakpoint.",
        "Logs keep watch while developers sleep.",
        "A single red test echoes in the void.",
        "Guardian counts retries with calm patience.",
        "CI dreams in green and occasionally red.",
        "Stacktraces are just stories told backwards.",
        "The duck approves small, focused commits.",
        "Somewhere a selector changed without warning.",
        "The night build knows all secrets.",
        "Assertions glow like lanterns in the fog.",
        "Silent typing... someone debugs at 2 AM.",
        "Guardian watches over fragile fixtures.",
        "Duck says: simplify before you optimize.",
        "The build passes - for now.",
        "A hidden race condition stretches its legs.",
        "Logs whisper truths no one wanted to hear.",
        "The watcher smiles at stable tests.",
        "Flaky tests fear deterministic minds.",
        "Every retry carries a lesson.",
        "CI waits - calm, unforgiving.",
        "The duck listens longer than humans do."
    )
    $i = Get-Random -Minimum 0 -Maximum $lines.Count
    Write-Host "   > $($lines[$i])" -ForegroundColor DarkGray
}

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
    Show-QAFlavor
}

function Ask-YesNo {
    param(
        [string]$Question,
        [bool]$Default = $true
    )
    $suffix = if ($Default) { "[Y/n]" } else { "[y/N]" }
    $answer = Read-Host "$Question $suffix"
    if ([string]::IsNullOrWhiteSpace($answer)) { return $Default }
    $normalized = $answer.Trim().ToLowerInvariant()
    return $normalized -in @("y","yes")
}

function Confirm-Or-DefaultPath {
    param(
        [string]$Question,
        [string]$DefaultPath
    )
    $entered = Read-Host "$Question [$DefaultPath]"
    if ([string]::IsNullOrWhiteSpace($entered)) { return $DefaultPath }
    return $entered.Trim()
}

function Save-SetupState {
    param(
        [string]$StatePath,
        [string]$PythonExe,
        [string]$VenvDir,
        [string]$GitExe
    )

    @{
        python_dir = "per-user-default"
        python_exe = $PythonExe
        venv_dir   = $VenvDir
        git_exe    = $GitExe
    } | ConvertTo-Json | Set-Content -Path $StatePath -Encoding UTF8
}

# -------------------------
# Human typing (ASCII only)
# -------------------------

function Write-HumanTyping {
    param([string]$Text)

    $rand = New-Object System.Random
    foreach ($char in $Text.ToCharArray()) {

        # occasional human typo only for A-Z letters
        if ($rand.NextDouble() -lt 0.06 -and $char -match '[A-Za-z]') {
            $wrong = [char]($rand.Next(97,123))
            Write-Host -NoNewline $wrong
            Start-Sleep -Milliseconds ($rand.Next(60,160))
            # backspace + erase + backspace
            Write-Host -NoNewline "`b `b"
            Start-Sleep -Milliseconds ($rand.Next(40,120))
        }

        Write-Host -NoNewline $char

        $delay = $rand.Next(20,140)
        if ($char -match '[,.!?]') { $delay += $rand.Next(180,350) }
        elseif ($char -eq ' ') { $delay += $rand.Next(10,60) }
        if ($rand.NextDouble() -lt 0.08) { $delay += $rand.Next(120,400) }

        Start-Sleep -Milliseconds $delay
    }
    Write-Host ""
}

function Show-TesterHaiku {
    Write-Host ""
    Write-Host "..." -ForegroundColor DarkGray
    Start-Sleep -Milliseconds 250

    Write-HumanTyping "Silent tests at night"
    Write-HumanTyping "Selenium is asleep now"
    Write-HumanTyping "Logs keep watch for bugs"

    Write-Host ""
    Show-QAFlavor
}

function Show-SuccessHaiku {
    Write-Host ""
    Write-Host "..." -ForegroundColor DarkGray
    Start-Sleep -Milliseconds 250

    # English haiku about best women testing team in Greater Poland (ASCII-only)
    Write-HumanTyping "Greater Poland nights"
    Write-HumanTyping "Best women testers stand as one"
    Write-HumanTyping "Bugs fall, courage stays"

    Write-Host ""
    Show-QAFlavor
}

# -------------------------
# Python 3.13 detection
# -------------------------

function Get-PythonFromRegistry {
    param([string]$HivePath)
    try {
        $p = Get-ItemProperty -Path $HivePath -ErrorAction SilentlyContinue
        if ($p -and $p.'(default)') { return $p.'(default)' }
        if ($p -and $p.InstallPath) { return $p.InstallPath }
    } catch {}
    return $null
}

function Resolve-Python313 {
    param([ref]$ProbedLocations)

    $probes = New-Object System.Collections.Generic.List[string]

    # 1) py launcher (best)
    try {
        $pyExe = & py -3.13 -c 'import sys; print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0 -and $pyExe) {
            $cand = $pyExe.Trim()
            $probes.Add("py -3.13 -> $cand")
            if (Test-Path $cand) {
                $ProbedLocations.Value = $probes
                return $cand
            }
        } else {
            $probes.Add("py -3.13 -> (not available)")
        }
    } catch {
        $probes.Add("py -3.13 -> (error)")
    }

    # 2) Registry HKCU/HKLM
    $regKeys = @(
        "HKCU:\Software\Python\PythonCore\3.13\InstallPath",
        "HKLM:\Software\Python\PythonCore\3.13\InstallPath",
        "HKLM:\Software\WOW6432Node\Python\PythonCore\3.13\InstallPath"
    )

    foreach ($k in $regKeys) {
        $ip = Get-PythonFromRegistry -HivePath $k
        if ($ip) {
            $ip2 = $ip.TrimEnd('\')
            $cand = Join-Path $ip2 "python.exe"
            $probes.Add("$k -> $cand")
            if (Test-Path $cand) {
                $ProbedLocations.Value = $probes
                return $cand
            }
        } else {
            $probes.Add("$k -> (missing)")
        }
    }

    # 3) Standard per-user install path
    $userDefault = Join-Path $env:LocalAppData "Programs\Python\Python313\python.exe"
    $probes.Add("LocalAppData default -> $userDefault")
    if (Test-Path $userDefault) {
        $ProbedLocations.Value = $probes
        return $userDefault
    }

    # 4) Common per-machine (if present)
    $machine = Join-Path $env:ProgramFiles "Python313\python.exe"
    $probes.Add("ProgramFiles -> $machine")
    if (Test-Path $machine) {
        $ProbedLocations.Value = $probes
        return $machine
    }

    $ProbedLocations.Value = $probes
    return $null
}

# -------------------------
# Git install + config
# -------------------------

function Resolve-GitExe {
    try {
        $cmd = Get-Command git -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Source -and (Test-Path $cmd.Source)) { return $cmd.Source }
    } catch {}
    return $null
}

function Ensure-Git {
    param(
        [string]$RepoRoot
    )

    $gitExe = Resolve-GitExe
    if ($gitExe) { return $gitExe }

    if (-not (Ask-YesNo -Question "Git not found. Install Git now?" -Default $true)) {
        return $null
    }

    # Prefer winget (no hardcoded URLs).
    $winget = $null
    try { $winget = Get-Command winget -ErrorAction SilentlyContinue } catch {}

    if ($winget) {
        Write-Step "Installing Git (winget)"
        $args = @(
            "install",
            "--id", "Git.Git",
            "-e",
            "--source", "winget",
            "--accept-package-agreements",
            "--accept-source-agreements"
        )
        $p = Start-Process -FilePath $winget.Source -ArgumentList $args -Wait -PassThru -NoNewWindow
        if ($p.ExitCode -ne 0) {
            throw "Git install via winget failed (exit code $($p.ExitCode))."
        }

        $gitExe = Resolve-GitExe
        if ($gitExe) { return $gitExe }

        throw "Git install finished, but git.exe is still not found on PATH. Restart terminal and rerun, or add Git to PATH."
    }

    # Fallback: prompt user for installer URL (no guessing).
    Write-Step "Installing Git (manual URL required)"
    $installerUrl = Read-Host "Enter Git for Windows installer URL (EXE). Leave empty to abort"
    if ([string]::IsNullOrWhiteSpace($installerUrl)) {
        throw "Git installer URL not provided and winget is unavailable. Aborting."
    }

    $tempDir = Join-Path $RepoRoot ".tmp"
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

    $installerPath = Join-Path $tempDir "git-installer.exe"
    Write-Host "Downloading Git installer..." -ForegroundColor DarkGray
    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath

    # Silent install flags differ by Git installer versions.
    # We try the common Inno Setup /VERYSILENT first.
    Write-Host "Running Git installer (silent)..." -ForegroundColor DarkGray
    $p2 = Start-Process -FilePath $installerPath -ArgumentList @("/VERYSILENT","/NORESTART") -Wait -PassThru -NoNewWindow

    if ($p2.ExitCode -ne 0) {
        throw "Git installer failed (exit code $($p2.ExitCode)). You may need to run the installer interactively."
    }

    $gitExe = Resolve-GitExe
    if ($gitExe) { return $gitExe }

    throw "Git install finished, but git.exe is still not found on PATH. Restart terminal and rerun."
}

function Configure-GitIdentity {
    param(
        [string]$GitExe
    )

    if (-not $GitExe) { return }

    if (-not (Ask-YesNo -Question "Configure git user.name and user.email now?" -Default $true)) {
        return
    }

    $name = Read-Host "git user.name"
    $email = Read-Host "git user.email"

    if ([string]::IsNullOrWhiteSpace($name) -or [string]::IsNullOrWhiteSpace($email)) {
        throw "git user.name and user.email cannot be empty."
    }

    Write-Step "Configuring git identity"
    & $GitExe config --global user.name "$name"
    & $GitExe config --global user.email "$email"

    Write-Host "git user.name  = $(& $GitExe config --global user.name)" -ForegroundColor Green
    Write-Host "git user.email = $(& $GitExe config --global user.email)" -ForegroundColor Green
}

function Install-LocalPreCommitHook {
    param(
        [string]$RepoRoot
    )

    if (-not (Ask-YesNo -Question "Install local pre-commit hook (ASO tests before commit)?" -Default $true)) {
        return
    }

    $sourceHook = Join-Path $RepoRoot "tools\hooks\pre-commit-aso.sh"
    $gitDir = Join-Path $RepoRoot ".git"
    $hooksDir = Join-Path $gitDir "hooks"
    $targetHook = Join-Path $hooksDir "pre-commit"

    if (-not (Test-Path $sourceHook)) {
        Write-Host "Hook source not found: $sourceHook" -ForegroundColor DarkYellow
        return
    }
    if (-not (Test-Path $gitDir)) {
        Write-Host "Git metadata not found (.git). Skip hook install." -ForegroundColor DarkYellow
        return
    }

    New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null
    Copy-Item -Path $sourceHook -Destination $targetHook -Force
    Write-Host "Installed local hook: $targetHook" -ForegroundColor Green
}

# -------------------------
# Diagnostics (friendly)
# -------------------------

function Write-Diagnostics {
    param(
        [string]$PythonExe,
        [string]$VenvPython,
        [string]$RepoRoot,
        [string]$GitExe
    )

    Write-Step "Diagnostics"

    Write-Host "`nBase Python:" -ForegroundColor DarkCyan
    Write-Host "  exe: $PythonExe"
    & $PythonExe --version

    Write-Host "`nVenv Python:" -ForegroundColor DarkCyan
    Write-Host "  exe: $VenvPython"
    & $VenvPython --version

    Write-Host "`nGit:" -ForegroundColor DarkCyan
    if ($GitExe) {
        Write-Host "  exe: $GitExe"
        & $GitExe --version
    } else {
        Write-Host "  not installed / not on PATH"
    }

    Write-Host "`nRepo root: $RepoRoot" -ForegroundColor DarkCyan
}

# -------------------------
# MAIN
# -------------------------

try {
    Show-TesterHaiku

    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $repoRoot  = Split-Path -Parent (Split-Path -Parent $scriptDir)
    Set-Location $repoRoot

    Write-Host "netQArner - Windows setup wizard" -ForegroundColor Green
    Write-Host "Repository: $repoRoot"

    $defaultVenvDir      = Join-Path $repoRoot ".venv"
    $defaultInstallerUrl = "https://www.python.org/ftp/python/3.13.2/python-3.13.2-amd64.exe"
    $statePath           = Join-Path $repoRoot ".windows_setup_state.json"

    $venvDir = Confirm-Or-DefaultPath -Question "Virtual environment directory" -DefaultPath $defaultVenvDir
    $installerUrl = $defaultInstallerUrl

    # Git (optional) + config
    $gitExe = Ensure-Git -RepoRoot $repoRoot
    Configure-GitIdentity -GitExe $gitExe

    # Python 3.13
    $probed = $null
    $pythonExe = Resolve-Python313 -ProbedLocations ([ref]$probed)

    if (-not $pythonExe) {
        Write-Step "Installing/Updating Python 3.13 (per-user default)"

        $tempDir = Join-Path $repoRoot ".tmp"
        New-Item -ItemType Directory -Force -Path $tempDir | Out-Null

        $installerPath = Join-Path $tempDir "python-installer.exe"
        $logPath       = Join-Path $tempDir "python-install.log"

        Write-Host "Downloading Python installer..." -ForegroundColor DarkGray
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath

        # No TargetDir -> per-user default location.
        # Include_launcher=0 avoids launcher conflict noise.
        $args = @(
            "/quiet",
            "/log `"$logPath`"",
            "InstallAllUsers=0",
            "Include_launcher=0",
            "Include_pip=1",
            "Include_test=0",
            "Include_doc=0",
            "Include_tcltk=0",
            "Shortcuts=0",
            "PrependPath=0",
            "AppendPath=0"
        )

        $p = Start-Process -FilePath $installerPath -ArgumentList $args -Wait -PassThru
        if ($p.ExitCode -ne 0) {
            throw "Python installer failed (exit code $($p.ExitCode)). Log: $logPath"
        }

        $probed = $null
        $pythonExe = Resolve-Python313 -ProbedLocations ([ref]$probed)

        if (-not $pythonExe) {
            Write-Host "`nPython 3.13 still not found." -ForegroundColor Red
            Write-Host "Probes:" -ForegroundColor DarkGray
            foreach ($x in $probed) { Write-Host "  - $x" -ForegroundColor DarkGray }
            throw "Python 3.13 not found after installation. Log: $logPath"
        }
    } else {
        Write-Step "Using existing Python 3.13"
        Write-Host "Python: $pythonExe" -ForegroundColor Green
    }

    Write-Step "Creating virtual environment"
    & $pythonExe -m venv $venvDir

    $venvPython = Join-Path $venvDir "Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        throw "Virtual environment is invalid. Missing: $venvPython"
    }

    Write-Step "Upgrading pip"
    & $venvPython -m pip install --upgrade pip

    Write-Step "Installing dependencies"
    & $venvPython -m pip install -e ".[dev]"

    if (Ask-YesNo -Question "Install Playwright Chromium?" -Default $true) {
        Write-Step "Installing Playwright browser"
        & $venvPython -m playwright install chromium
    }

    Write-Step "Installing local git hooks"
    Install-LocalPreCommitHook -RepoRoot $repoRoot

    Write-Diagnostics -PythonExe $pythonExe -VenvPython $venvPython -RepoRoot $repoRoot -GitExe $gitExe
    Save-SetupState -StatePath $statePath -PythonExe $pythonExe -VenvDir $venvDir -GitExe $gitExe

    Write-Step "Setup completed"
    Write-Host "Activate:" -ForegroundColor Green
    Write-Host "  $venvDir\Scripts\Activate.ps1" -ForegroundColor Green

    # Extra live-typed haiku ONLY on success
    Show-SuccessHaiku
}
catch {
    Write-Host ""
    Write-Host "Setup failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
