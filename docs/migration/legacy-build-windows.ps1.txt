param(
    [ValidateSet('all','fetch','check','test','compile','pcb','edit','route','render','verify','power-probes','assembly','manufacturing','order')]
    [string]$Target = 'all',
    [string]$Uv = 'uv',
    [string]$KiCadCli = "$env:ProgramW6432/KiCad/10.0/bin/kicad-cli.exe"
)
$ErrorActionPreference = 'Stop'
$trackerMake = Get-Command make -ErrorAction Stop
if (-not (Get-Command $Uv -ErrorAction SilentlyContinue) -and -not (Test-Path -LiteralPath $Uv)) {
    throw 'Install uv or pass -Uv with its absolute executable path.'
}
Push-Location $PSScriptRoot
try {
    & $trackerMake.Source $Target "UV=$Uv" "KICAD_CLI=$KiCadCli"
    if ($LASTEXITCODE -ne 0) { throw "Build target '$Target' failed ($LASTEXITCODE)." }
} finally { Pop-Location }
