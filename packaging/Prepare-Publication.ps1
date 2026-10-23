# Apply the prepared folder only after the current game session is finished.
# This script does not start the game or upload/publish anything.
$ErrorActionPreference = 'Stop'
$stage = $PSScriptRoot
$source = Join-Path $stage 'Roadster'
$root = Join-Path $env:USERPROFILE 'AppData\LocalLow\Hovgaard Games\Big Ambitions'
$target = Join-Path $root 'ModsLocal\Roadster'
$lock = Join-Path $env:USERPROFILE 'game-lock.txt'
if (Test-Path $lock) { throw "Another session holds game-lock.txt. Wait for its owner to release it; do not delete it." }
if (Get-Process 'Big Ambitions' -ErrorAction SilentlyContinue) { throw 'Close Big Ambitions before applying publication files.' }

function Get-PackageHashes([string]$folder) {
    $result = @{}
    Get-ChildItem $folder -Recurse -File | ForEach-Object {
        $relative = $_.FullName.Substring($folder.Length + 1).Replace('\', '/')
        $result[$relative] = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
    }
    return $result
}
function Confirm-Package([string]$folder, $expected) {
    $actual = Get-PackageHashes $folder
    if ($actual.Count -ne @($expected.PSObject.Properties).Count) { throw "Unexpected file set in $folder" }
    foreach ($entry in $expected.PSObject.Properties) {
        if ($actual[$entry.Name] -ne $entry.Value) { throw "Changed or missing file: $($entry.Name) in $folder" }
    }
}
$receipt = Get-Content (Join-Path $stage 'verification.json') -Raw -Encoding UTF8 | ConvertFrom-Json
Confirm-Package $source $receipt.publicationFiles
if (!(Test-Path $target)) { throw 'The original Roadster installation is missing. Recheck the setup before proceeding.' }
Confirm-Package $target $receipt.originalInstalledFiles

# Atomically claim the shared lock, then recheck before touching the installation.
$claim = [System.IO.File]::Open($lock, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
$writer = New-Object System.IO.StreamWriter($claim)
$writer.WriteLine('owner: Roadster publication preparation')
$writer.WriteLine('since: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm'))
$writer.WriteLine('game: applying verified publication package; no game launch')
$writer.Flush()
$incoming = Join-Path $root ('Roadster-publication-incoming-' + [guid]::NewGuid().ToString('N'))
$backup = Join-Path $root ('RoadsterPackageBackups\Roadster-before-publication-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
try {
    if (Get-Process 'Big Ambitions' -ErrorAction SilentlyContinue) { throw 'The game started. No install performed.' }
    Confirm-Package $target $receipt.originalInstalledFiles
    Copy-Item $source $incoming -Recurse
    Confirm-Package $incoming $receipt.publicationFiles
    New-Item (Split-Path $backup -Parent) -ItemType Directory -Force | Out-Null
    Move-Item $target $backup
    try {
        Move-Item $incoming $target
        Confirm-Package $target $receipt.publicationFiles
    } catch {
        if (Test-Path $target) { Remove-Item $target -Recurse -Force }
        Move-Item $backup $target
        throw
    }
    Write-Host "Publication files verified in $target"
    Write-Host "Previous installation backed up to $backup"
    Write-Host 'Open Big Ambitions > Mods > Mod Creator. Use the fields in Workshop.'
    Write-Host 'Nothing has been uploaded or published.'
} finally {
    if (Test-Path $incoming) { Remove-Item $incoming -Recurse -Force }
    $writer.Dispose()
    Remove-Item $lock -Force
}
