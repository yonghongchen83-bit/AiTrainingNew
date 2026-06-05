param(
    [int]$Seed = 43,
    [switch]$DryRun
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $repoRoot

$cmd = @("python", "training/scripts/start_training.py", "--stage", "stage3", "--seed", "$Seed")
if ($DryRun) {
    $cmd += "--dry-run"
}

Write-Host "[training] Starting stage3 (SFT framework patterns)" -ForegroundColor Cyan
Write-Host ($cmd -join " ")
& $cmd[0] $cmd[1..($cmd.Length - 1)]
exit $LASTEXITCODE
