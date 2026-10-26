param(
    [Parameter(Mandatory = $true)]
    [string]$InputHtml,

    [Parameter(Mandatory = $true)]
    [string]$OutputPng,

    [int]$Width = 1080,
    [int]$Height = 1350
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

$profilePath = Join-Path ([System.IO.Path]::GetTempPath()) ("madhan-card-render-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $profilePath | Out-Null

try {
    $uri = [System.Uri]::new($inputPath).AbsoluteUri
    $arguments = @(
        '--headless',
        '--disable-gpu',
        '--hide-scrollbars',
        '--no-first-run',
        '--force-device-scale-factor=1',
        "--window-size=$Width,$Height",
        "--user-data-dir=$profilePath",
        "--screenshot=$outputPath",
        $uri
    )

    $process = Start-Process -FilePath $edge -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
    if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $outputPath)) {
        throw "Card render failed with Edge exit code $($process.ExitCode)."
    }

    Add-Type -AssemblyName System.Drawing
    $bitmap = [System.Drawing.Image]::FromFile($outputPath)
    try {
        if ($bitmap.Width -ne $Width -or $bitmap.Height -ne $Height) {
            throw "Rendered image is $($bitmap.Width)x$($bitmap.Height); expected ${Width}x${Height}."
        }
    }
    finally {
        $bitmap.Dispose()
    }

    Write-Output $outputPath
}
finally {
    if (Test-Path -LiteralPath $profilePath) {
        Remove-Item -LiteralPath $profilePath -Recurse -Force
    }
}
