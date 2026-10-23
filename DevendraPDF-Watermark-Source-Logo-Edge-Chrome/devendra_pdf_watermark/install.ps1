param(
  [Parameter(Mandatory=$false)][string]$SourceExe = (Join-Path $PSScriptRoot 'DevendraPDF.exe'),
  [Parameter(Mandatory=$false)][string]$LogoPath = (Join-Path $PSScriptRoot 'Logo.png')
)
$ErrorActionPreference = 'Stop'
if (!(Test-Path $SourceExe)) { throw "DevendraPDF.exe not found at $SourceExe. Build it in GitHub Actions first." }
if (!(Test-Path $LogoPath)) { throw "Logo.png not found at $LogoPath. Copy the official company logo PNG next to the installer." }
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\DevendraPDF'
$dataDir = Join-Path $env:LOCALAPPDATA 'DevendraPDF'
New-Item -ItemType Directory -Force -Path $installDir, (Join-Path $dataDir 'Watermarked'), (Join-Path $dataDir 'Logs') | Out-Null
Copy-Item -Force $SourceExe (Join-Path $installDir 'DevendraPDF.exe')
Copy-Item -Force $LogoPath (Join-Path $installDir 'Logo.png')
$config = @{ viewer = 'auto'; logo_width_points = 64; margin_points = 18 } | ConvertTo-Json
$configPath = Join-Path $installDir 'config.json'
[System.IO.File]::WriteAllText($configPath, $config, (New-Object System.Text.UTF8Encoding($false)))

# Register the app for Open With. Windows still requires the user to select the default app in Settings.
$progId = 'DevendraPDF.PDF'
$exe = Join-Path $installDir 'DevendraPDF.exe'
New-Item -Path "HKCU:\Software\Classes\$progId\shell\open\command" -Force | Out-Null
Set-Item -Path "HKCU:\Software\Classes\$progId\shell\open\command" -Value ('"' + $exe + '" "%1"')
New-Item -Path "HKCU:\Software\Classes\Applications\DevendraPDF.exe\shell\open\command" -Force | Out-Null
Set-Item -Path "HKCU:\Software\Classes\Applications\DevendraPDF.exe\shell\open\command" -Value ('"' + $exe + '" "%1"')
New-Item -Path 'HKCU:\Software\Classes\Applications\DevendraPDF.exe\SupportedTypes' -Force | Out-Null
New-ItemProperty -Path 'HKCU:\Software\Classes\Applications\DevendraPDF.exe\SupportedTypes' -Name '.pdf' -Value '' -PropertyType String -Force | Out-Null
New-Item -Path 'HKCU:\Software\Classes\.pdf\OpenWithProgids' -Force | Out-Null
New-ItemProperty -Path 'HKCU:\Software\Classes\.pdf\OpenWithProgids' -Name $progId -Value '' -PropertyType String -Force | Out-Null
Write-Host "Installed to $installDir"
Write-Host 'Next: open Settings > Apps > Default apps, search .pdf, and choose DevendraPDF if listed.'
Start-Process 'ms-settings:defaultapps'
