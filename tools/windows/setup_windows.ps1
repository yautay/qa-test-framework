$ErrorActionPreference = "Stop"
$PSNativeCommandUseErrorActionPreference = $true

& (Join-Path $PSScriptRoot "bootstrap.ps1") @args
