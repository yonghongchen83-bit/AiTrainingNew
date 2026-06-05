param(
    [Parameter(Mandatory=$true)][string]$RunId,
    [Parameter(Mandatory=$true)][string]$Stage,
    [switch]$Approve,
    [string]$Reason = ""
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $repoRoot

$cmd = @("python", "training/scripts/promote_stage_model.py", "--run-id", $RunId, "--stage", $Stage)
if ($Approve) {
    $cmd += "--approve"
}
if ($Reason -ne "") {
    $cmd += @("--reason", $Reason)
}

Write-Host "[training] Recording promotion decision" -ForegroundColor Yellow
Write-Host ($cmd -join " ")
& $cmd[0] $cmd[1..($cmd.Length - 1)]
exit $LASTEXITCODE
