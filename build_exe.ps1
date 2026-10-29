$ErrorActionPreference = "Stop"

python -m pip install -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw "Could not install build requirements." }

python -m PyInstaller --noconfirm --clean --onefile --console `
    --name Starfall `
    --add-data "data;data" `
    game.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

Write-Host "Executable created at dist\Starfall.exe"
