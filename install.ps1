param(
    [switch]$NoProfile
)

$ErrorActionPreference = "Stop"

python -m pip install --user .

if (-not $NoProfile) {
    $profileDirectory = Split-Path -Parent $PROFILE
    if (-not (Test-Path -LiteralPath $profileDirectory)) {
        New-Item -ItemType Directory -Path $profileDirectory -Force | Out-Null
    }

    $marker = "# sem-image-archive"
    $profileText = if (Test-Path -LiteralPath $PROFILE) {
        Get-Content -LiteralPath $PROFILE -Raw
    } else {
        ""
    }

    if ($profileText -notlike "*$marker*") {
        Add-Content -LiteralPath $PROFILE -Value @"

$marker
function sem-archive {
    python -m sem_image_archive @args
}
"@
        Write-Host "Added sem-archive to $PROFILE"
    } else {
        Write-Host "sem-archive profile entry already exists"
    }
}

Write-Host "Installation complete. Open a new PowerShell session and run: sem-archive --help"
