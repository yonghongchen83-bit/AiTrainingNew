param(
    [int]$Seed = 42,
    [switch]$DryRun
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $repoRoot

$cmd = @("python", "training/scripts/start_training.py", "--stage", "stage2", "--seed", "$Seed")
if ($DryRun) {
    $cmd += "--dry-run"
}

Write-Host "[training] Starting stage2 (RLHF confidence)" -ForegroundColor Cyan
Write-Host ($cmd -join " ")
& $cmd[0] $cmd[1..($cmd.Length - 1)]
exit $LASTEXITCODE
