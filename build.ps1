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
$runs=Join-Path $PSScriptRoot 'build/board/runs'
$latest=Join-Path $runs 'latest-route'
if($IsWindows -or $env:OS -eq 'Windows_NT'){
 $git=Join-Path $env:ProgramFiles 'Git'
 $gitBash=Join-Path $git 'bin/bash.exe'
 if(Test-Path -LiteralPath $gitBash){$makeArgs+="SHELL=$gitBash"}
 # Native Windows make runs simple recipe lines (true, mkdir, ln) directly,
 # not through SHELL, so Git's Unix tools must be on PATH for this process.
 $gitUsr=Join-Path $git 'usr/bin'
 if((Test-Path -LiteralPath $gitUsr) -and -not (($env:PATH -split ';') -contains $gitUsr)){$env:PATH="$gitUsr;$env:PATH"}
 # route points latest-route at the new run with `ln -sfn`. Without symlink
 # rights Git Bash copies the (empty) run folder instead, which breaks order,
 # render and review, and the next route's ln. Clear an old link or empty copy
 # first; after the route, point latest-route at the run with a junction,
 # which needs no special rights.
 if($Action -eq 'route' -and (Test-Path -LiteralPath $latest)){
  $item=Get-Item -LiteralPath $latest -Force
  if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){[IO.Directory]::Delete($latest,$false)}
  elseif(-not (Get-ChildItem -LiteralPath $latest -Force | Select-Object -First 1)){Remove-Item -LiteralPath $latest -Force}
  else{throw "$latest is a real folder with files in it, not a link to a run; move or delete it, then route again."}
 }
}
& $makeCommand.Source @makeArgs
$code=$LASTEXITCODE
if($Action -eq 'route' -and (Test-Path -LiteralPath $latest)){
 $item=Get-Item -LiteralPath $latest -Force
 if(-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){
  $run=Get-ChildItem -LiteralPath $runs -Directory | Where-Object Name -match '^\d{8}T\d{6}Z-route$' | Sort-Object Name | Select-Object -Last 1
  if($run -and -not (Get-ChildItem -LiteralPath $latest -Force | Select-Object -First 1)){
   Remove-Item -LiteralPath $latest -Force
   New-Item -ItemType Junction -Path $latest -Target $run.FullName | Out-Null
   Write-Host "latest-route -> $($run.Name) (junction)"
  }
 }
}
exit $code
