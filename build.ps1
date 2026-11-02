# Thin Windows entry point; all settings and commands live in the Makefile.
[CmdletBinding()]
param(
 [ValidateSet('all','check','compile','si-check','plan','layout','edit','route','render','review','bom','order','test','copper')]
 [string]$Action='all',
 [string]$Copper,
 [string]$KiCadCli
)
$ErrorActionPreference='Stop'
$makeCommand=Get-Command make,mingw32-make -ErrorAction SilentlyContinue | Select-Object -First 1
if(-not $makeCommand){throw 'GNU Make is required for this shortcut; use the public copper CLI directly or install GNU Make.'}
$makeArgs=@('-C',$PSScriptRoot,$Action)
if($Copper){$makeArgs+="COPPER=$Copper"}
if($KiCadCli){$makeArgs+="KICAD_CLI=$KiCadCli"}
if($IsWindows -or $env:OS -eq 'Windows_NT'){
 $gitBash=Join-Path $env:ProgramFiles 'Git/bin/bash.exe'
 if(Test-Path -LiteralPath $gitBash){$makeArgs+="SHELL=$gitBash"}
}
& $makeCommand.Source @makeArgs
exit $LASTEXITCODE
