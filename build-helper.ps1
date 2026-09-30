$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$res = Join-Path $root 'Skins\X3 Superstrike\@Resources'
py -m pip install --upgrade hidapi pyinstaller
py -m PyInstaller --onefile --clean --noconfirm --name X3Helper --distpath "$root\dist" --workpath "$root\build" --specpath "$root" "$res\X3Helper.py"
Copy-Item "$root\dist\X3Helper.exe" "$res\X3Helper.exe" -Force
Write-Host "Built: $res\X3Helper.exe"
