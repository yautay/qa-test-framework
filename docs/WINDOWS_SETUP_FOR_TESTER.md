# Windows Setup For Testers

This guide is for someone who wants to run tests and the local report app on Windows without needing deep technical knowledge of the framework.

## What You Need

1. A computer with Windows 10 or Windows 11.
2. Internet access.
3. A local copy of this repository on disk.
4. Git for Windows.
5. Docker Desktop, optionally.

Docker Desktop is only needed for extra services such as local MinIO or the remote grid.
It is not required for normal test execution or for opening the report app.

Node.js is not required for testers.

## Before You Start

1. Make sure you already have the project folder on your computer.
2. Make sure the project is not opened from a USB drive or a slow network share.
3. Close old terminal windows that were previously used for this project.

## First-Time Setup Step by Step

1. Open the project folder in Windows Explorer.
2. Go to `tools\windows`.
3. Double-click `Setup_Windows.cmd`.
4. Wait until the setup is finished.

During setup, the script will do the following for you:

1. check and install `uv`,
2. prepare Python `3.13.2`,
3. create the local `.venv` environment,
4. install all required Python packages,
5. install Chromium for Playwright,
6. install the local git hook.

The first run can take a few minutes.

## Check That Everything Works

After setup is complete:

1. Right-click inside the project folder.
2. Open PowerShell in that folder.
3. Paste and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 doctor
```

If everything is ready, you will see `OK` messages and a final message saying there are no blocking issues.

## Daily Work

Always work from the main repository folder.

The easiest way:

1. Open PowerShell in the project folder.
2. Paste one of the ready commands below.

### Run ASO Tests

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 aso
```

### Run API Tests

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 api
```

### Run E2E Tests

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 e2e
```

### Run Visual Tests

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 visual
```

### Verify Framework Configuration

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 verify
```

## How To Open The Report App

1. Open PowerShell in the project folder.
2. Paste and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 report
```

3. Wait until the server address appears in the terminal.
4. Open that address in your browser.

In most cases it will be:

```text
http://127.0.0.1:4173/
```

Important:

1. The report works without Node.js on the tester machine.
2. If the repository is up to date, nothing needs to be built locally.

## After Updating The Repository

If you run `git pull`, it is best to refresh the environment using one of the two methods below.

Quick method:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 sync
```

Full method if something behaves strangely:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\bootstrap.ps1
```

## When Docker Desktop Is Needed

Docker Desktop is optional.

You only need it if you want to use:

1. local MinIO for visual baselines,
2. local remote grid.

Examples:

```powershell
docker compose -f tools\minio\docker-compose.yml up -d
docker compose -f tools\minio\docker-compose.yml down

docker compose -f tools\remote\docker-compose.yml up -d
docker compose -f tools\remote\docker-compose.yml down
```

## Common Problems

### 1. The script does not start after double-clicking

Run it from PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\bootstrap.ps1
```

### 2. `doctor` shows an error for `.venv` or `python`

Run bootstrap again:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\bootstrap.ps1
```

### 3. `doctor` shows a warning for Docker

This does not block normal tester work.
You can ignore it if you are not using MinIO or the remote grid.

### 4. Chromium / Playwright does not work

Run bootstrap again. The script will check and install the missing parts again.

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\bootstrap.ps1
```

### 5. The report does not open in the browser

1. Check whether the `report` command is still running in the terminal.
2. Check whether you are opening the exact address shown in the terminal.
3. If it still does not work, run `git pull`, then `sync`, and then start the report again.

### 6. Will `Setup_Windows.cmd` ask for administrator rights?

Usually no.

This setup is designed to install everything locally for the current user.
This mainly applies to:

1. `uv`
2. Python `3.13.2`
3. `.venv`
4. Python packages
5. Playwright Chromium

Possible exceptions:

1. your company Windows policy blocks `winget` or downloaded scripts,
2. Git for Windows is not installed yet and your organization requires admin rights for that installation,
3. the machine has additional security restrictions managed by IT.

Short answer:

1. `Setup_Windows.cmd` itself usually does not require admin rights,
2. but company policies may change that.

## Short Version For Testers

First time:

1. `tools\windows\Setup_Windows.cmd`
2. `powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 doctor`

Daily work:

1. `powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 aso`
2. `powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 e2e`
3. `powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 visual`
4. `powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 report`

After `git pull`:

1. `powershell -ExecutionPolicy Bypass -File .\tools\windows\run.ps1 sync`

## What Must Be Installed In Windows Before You Start

Below is the practical checklist for a tester.

### Required

1. Git for Windows
2. Internet access
3. The repository copied to disk or cloned locally

### Installed Automatically By Bootstrap

1. `uv`
2. Python `3.13.2`
3. local `.venv`
4. Python packages from `uv.lock`
5. Playwright Chromium
6. local git hook

### Optional

1. Docker Desktop, only if you want to use MinIO or the remote grid
2. Node.js `22`, only for someone maintaining the report UI

## Software List And Whether It Usually Needs Admin Rights

| Item | Needed by tester | Installed by | Usually needs admin rights | Notes |
| --- | --- | --- | --- | --- |
| Git for Windows | Yes | tester or IT | Usually no for per-user install; sometimes yes in corporate environments | Needed for repository work and git hooks |
| `uv` | Yes | bootstrap | Usually no | Bootstrap tries to install it automatically |
| Python `3.13.2` | Yes | bootstrap through `uv` | No | Installed locally for the current user |
| Python packages from `uv.lock` | Yes | bootstrap | No | Installed into local `.venv` |
| Playwright Chromium | Yes | bootstrap | No | Installed in the user profile |
| Report UI `dist` | Yes | already in repo | No | Testers do not build it locally |
| Docker Desktop | Optional | tester or IT | Yes, usually yes | Needed only for MinIO / remote grid |
| Node.js `22` | Not for testers | UI maintainer or IT | Usually no | Needed only for changes in `framework/visual/ui` |

## Short Answer: What Do I Need Before Starting?

For a regular tester, in most cases this is enough:

1. Windows
2. Git for Windows
3. the repository folder
4. internet access

`Setup_Windows.cmd` prepares the rest.

If you need Docker Desktop, its installation usually requires administrator rights.
