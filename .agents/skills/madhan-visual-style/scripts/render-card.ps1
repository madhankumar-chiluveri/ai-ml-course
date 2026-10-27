param(
    [Parameter(Mandatory = $true)]
    [string]$InputHtml,

    [Parameter(Mandatory = $true)]
    [string]$OutputPng,

    [int]$Width = 1080,
    [int]$Height = 1350,

    [ValidateRange(1, 4)]
    [int]$Scale = 2
)

$ErrorActionPreference = 'Stop'

$inputPath = (Resolve-Path -LiteralPath $InputHtml).Path
$outputParent = Split-Path -Parent $OutputPng
if (-not $outputParent) {
    $outputParent = (Get-Location).Path
}
if (-not (Test-Path -LiteralPath $outputParent)) {
    New-Item -ItemType Directory -Path $outputParent | Out-Null
}
$outputPath = [System.IO.Path]::GetFullPath((Join-Path $outputParent (Split-Path -Leaf $OutputPng)))

$edgeCandidates = @(
    'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    'C:\Program Files\Microsoft\Edge\Application\msedge.exe'
)
$edge = $edgeCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $edge) {
    throw 'Microsoft Edge was not found. Install Edge or render the HTML with another deterministic browser workflow.'
}

$renderTempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
$profilePath = Join-Path $renderTempRoot ("madvibe-card-render-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $profilePath | Out-Null

try {
    $uri = [System.Uri]::new($inputPath).AbsoluteUri
    $arguments = @(
        '--headless',
        '--disable-gpu',
        '--hide-scrollbars',
        '--no-first-run',
        "--force-device-scale-factor=$Scale",
        "--window-size=$Width,$Height",
        '--disable-background-mode',
        '--disable-background-networking',
        '--virtual-time-budget=1500',
        ('--user-data-dir="{0}"' -f $profilePath),
        ('--screenshot="{0}"' -f $outputPath),
        $uri
    )

    $process = Start-Process -FilePath $edge -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
    if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $outputPath)) {
        throw "Card render failed with Edge exit code $($process.ExitCode)."
    }

    Add-Type -AssemblyName System.Drawing
    $bitmap = [System.Drawing.Image]::FromFile($outputPath)
    try {
        $expectedWidth = $Width * $Scale
        $expectedHeight = $Height * $Scale
        if ($bitmap.Width -ne $expectedWidth -or $bitmap.Height -ne $expectedHeight) {
            throw "Rendered image is $($bitmap.Width)x$($bitmap.Height); expected ${expectedWidth}x${expectedHeight}."
        }
    }
    finally {
        $bitmap.Dispose()
    }

    Write-Output $outputPath
}
finally {
    if (Test-Path -LiteralPath $profilePath) {
        $resolvedProfile = (Resolve-Path -LiteralPath $profilePath).Path
        $tempPrefix = $renderTempRoot + [System.IO.Path]::DirectorySeparatorChar
        if (-not $resolvedProfile.StartsWith($tempPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
            (Split-Path -Leaf $resolvedProfile) -notmatch '^madvibe-card-render-[0-9a-f]{32}$') {
            throw 'Refusing to remove an unexpected browser profile path.'
        }
        Remove-Item -LiteralPath $resolvedProfile -Recurse -Force
    }
}
