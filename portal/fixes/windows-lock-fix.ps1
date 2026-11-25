# Repairs the two omitted Windows dependencies in v0.1.1.
# Run at the folder containing nawa.py. Preserves data/configuration and hashes.
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath '.\nawa.py')) {
    throw 'Open PowerShell in the nawa-workspace folder containing nawa.py first.'
}
$tzdata = 'tzdata==2026.6 ; sys_platform == "win32" --hash=sha256:0a10eec6e13ef16b627fabed9a5f2ba61a62b1c67f327305f4e7e412a70b4aec --hash=sha256:85d2cd9c09f81f0bb29db27759fc83af4f1e620efb814f8c5bf8b4cc4feece6d'
$colorama = 'colorama==0.4.6 ; sys_platform == "win32" --hash=sha256:08695f5cb7ed6e0531a20572697297273c47b8cae5a63ffc6d6ed5c201be6e44 --hash=sha256:4f1d9991f5acc0ca119f9d443620b77f9d6b33703e51011c16baf57afb285fc6'
foreach ($file in @('requirements.lock', 'requirements-dev.lock')) {
    if (-not (Test-Path -LiteralPath $file)) { throw "Missing required lockfile: $file" }
    if (-not (Select-String -LiteralPath $file -Pattern '^tzdata==' -Quiet)) {
        Add-Content -LiteralPath $file -Value "`n$tzdata" -Encoding UTF8
    }
}
if (-not (Select-String -LiteralPath 'requirements-dev.lock' -Pattern '^colorama==' -Quiet)) {
    Add-Content -LiteralPath 'requirements-dev.lock' -Value "`n$colorama" -Encoding UTF8
}
Write-Output 'Windows pins and trusted hashes are present. Rerun: py -3.12 nawa.py setup'

