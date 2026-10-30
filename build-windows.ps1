# Compatibility entry point: use -Action/-Target/-Copper as documented in build.ps1.
& (Join-Path $PSScriptRoot 'build.ps1') @args
exit $LASTEXITCODE
