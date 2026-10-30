# Thin Windows entry point; all settings and commands live in the Make adapter.
[CmdletBinding()]
param(
 [ValidateSet('fetch','check','compile','power-check','layout','edit','test-smoke','test','route','route-draft','assembly','package','manufacturing','order','install-compiler')]
 [string]$Action='check',
 [string]$Target='main',
 [string]$Copper='copper',
 [string]$RunDirectory,
 [string]$KiCadCli='kicad-cli'
)
$ErrorActionPreference='Stop'
$makeCommand=Get-Command make,mingw32-make -ErrorAction SilentlyContinue | Select-Object -First 1
if(-not $makeCommand){throw 'GNU Make is required for this shortcut; use the public copper CLI directly or install GNU Make.'}
$makeArgs=@('-C',$PSScriptRoot,$Action,"TARGET=$Target","COPPER=$Copper","KICAD_CLI=$KiCadCli")
if($RunDirectory){$makeArgs+="RUN_DIR=$RunDirectory"}
if($IsWindows -or $env:OS -eq 'Windows_NT'){
 $gitBash=Join-Path $env:ProgramFiles 'Git/bin/bash.exe'
 if(Test-Path -LiteralPath $gitBash){$makeArgs+="SHELL=$gitBash"}
}
& $makeCommand.Source @makeArgs
exit $LASTEXITCODE
