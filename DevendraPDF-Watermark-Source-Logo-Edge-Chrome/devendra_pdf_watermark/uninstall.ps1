$ErrorActionPreference = 'Continue'
$progId = 'DevendraPDF.PDF'
Remove-Item -Recurse -Force "HKCU:\Software\Classes\$progId" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force 'HKCU:\Software\Classes\Applications\DevendraPDF.exe' -ErrorAction SilentlyContinue
Remove-ItemProperty -Path 'HKCU:\Software\Classes\.pdf\OpenWithProgids' -Name $progId -ErrorAction SilentlyContinue
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\DevendraPDF'
Remove-Item -Recurse -Force $installDir -ErrorAction SilentlyContinue
Write-Host 'Launcher removed. Watermarked copies and logs were retained.'
Write-Host 'If the launcher was the default PDF app, use Settings > Apps > Default apps > .pdf to select Edge or Adobe Reader.'
