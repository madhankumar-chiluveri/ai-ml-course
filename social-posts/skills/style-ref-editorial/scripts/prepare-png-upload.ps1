param(
    [Parameter(Mandatory = $true)][string]$InputPng,
    [Parameter(Mandatory = $true)][string]$OutputPng
)

# Container metadata export only. Preserve the original and every non-caBX byte.
$ErrorActionPreference = 'Stop'
$workspaceRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../../..')).Path
$workspacePrefix = $workspaceRoot.TrimEnd('\') + '\'
$inputPath = (Resolve-Path -LiteralPath $InputPng).Path
$outputPath = if ([IO.Path]::IsPathRooted($OutputPng)) {
    [IO.Path]::GetFullPath($OutputPng)
} else {
    [IO.Path]::GetFullPath((Join-Path (Get-Location).Path $OutputPng))
}
foreach ($target in @($inputPath, $outputPath)) {
    if (-not $target.StartsWith($workspacePrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Target is outside the workspace: $target"
    }
}
if ($inputPath.Equals($outputPath, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Choose a separate output file. The source must remain intact.'
}
if (Test-Path -LiteralPath $outputPath) {
    throw 'The output already exists. Choose a new versioned output path.'
}
if ([IO.Path]::GetExtension($outputPath) -ne '.png') {
    throw 'The output must be a PNG file.'
}

$bytes = [IO.File]::ReadAllBytes($inputPath)
$signature = [byte[]]@(137, 80, 78, 71, 13, 10, 26, 10)
if ($bytes.Length -lt 20) { throw 'Truncated PNG.' }
for ($index = 0; $index -lt 8; $index++) {
    if ($bytes[$index] -ne $signature[$index]) { throw 'Invalid PNG signature.' }
}

$stream = New-Object IO.MemoryStream
$removedChunks = @()
$offset = 8
$ended = $false
try {
    $stream.Write($bytes, 0, 8)
    while ($offset -lt $bytes.Length) {
        if ($bytes.Length - $offset -lt 12) { throw 'Truncated PNG chunk header.' }
        $length = [Net.IPAddress]::NetworkToHostOrder([BitConverter]::ToInt32($bytes, $offset))
        if ($length -lt 0 -or [long]$offset + $length + 12 -gt $bytes.Length) {
            throw 'Invalid PNG chunk length.'
        }
        $type = [Text.Encoding]::ASCII.GetString($bytes, $offset + 4, 4)
        $total = $length + 12
        if ($type -eq 'caBX') {
            $removedChunks += [PSCustomObject]@{ Type = $type; Bytes = $total }
        } else {
            $stream.Write($bytes, $offset, $total)
        }
        $offset += $total
        if ($type -eq 'IEND') {
            $ended = $true
            if ($offset -ne $bytes.Length) { throw 'Unexpected data after PNG end.' }
            break
        }
    }
    if (-not $ended) { throw 'PNG has no end chunk.' }
    $outputBytes = $stream.ToArray()
    [IO.File]::WriteAllBytes($outputPath, $outputBytes)
} finally {
    $stream.Dispose()
}

[PSCustomObject]@{
    Input = $inputPath
    Output = $outputPath
    RemovedChunks = $removedChunks
    BytesSaved = $bytes.Length - $outputBytes.Length
    SourcePreserved = $true
    InputSha256 = (Get-FileHash -LiteralPath $inputPath -Algorithm SHA256).Hash
    OutputSha256 = (Get-FileHash -LiteralPath $outputPath -Algorithm SHA256).Hash
} | ConvertTo-Json -Depth 4
