# ============================================================================
#  Build completo do RJE Avaliações (Windows)
#   1. Gera o executável (PyInstaller, modo onedir)       -> dist\RJE_Avaliacoes
#   2. Assina o executável (se houver certificado)         -> ver ASSINATURA_DIGITAL.md
#   3. Gera o ZIP para o atualizador automático            -> output\RJE_Avaliacoes_vX.Y.Z.zip
#   4. Gera (e assina) o instalador                        -> output\RJE_Avaliacoes_Setup.exe
#  Uso:  powershell -ExecutionPolicy Bypass -File .\build_release.ps1
#
#  Assinatura (opcional) — defina UMA das opções antes de rodar:
#    $env:RJE_SIGN_THUMBPRINT = "<impressão digital do certificado instalado/token USB>"
#    $env:RJE_SIGN_PFX = "C:\caminho\certificado.pfx"; $env:RJE_SIGN_PASSWORD = "<senha>"
# ============================================================================
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
. "$PSScriptRoot\sign_tools.ps1"

$version = (Select-String -Path "version.py" -Pattern '__version__ = "(.*)"').Matches.Groups[1].Value
Write-Host "== RJE Avaliações v$version ==" -ForegroundColor Green

# 1) Python / dependências
$py = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "Criando ambiente virtual (.venv)..." -ForegroundColor Yellow
    python -m venv .venv
    & $py -m pip install --upgrade pip
}
& $py -m pip install -r requirements.txt

# 2) Limpeza e PyInstaller
foreach ($p in @("build", "dist")) { if (Test-Path $p) { Remove-Item $p -Recurse -Force } }
& $py -m PyInstaller --noconfirm --clean rje_avaliacoes.spec
if ($LASTEXITCODE -ne 0) { throw "Falha no PyInstaller." }

# 3) Assinatura do executável (antes de empacotar)
$staging = "dist\RJE_Avaliacoes"
if (Test-RjeSigning) { Invoke-RjeSign "$staging\RJE_Avaliacoes.exe" }
else { Write-Warning "Sem certificado configurado: o executável NÃO será assinado (o Windows pode exibir o aviso do SmartScreen)." }

# 4) ZIP para o atualizador (sem .env / sem token: o atualizador usa releases públicas)
New-Item -ItemType Directory -Force -Path "output" | Out-Null
$zip = "output\RJE_Avaliacoes_v$version.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
if (Test-Path "$staging\.env") { Remove-Item "$staging\.env" -Force }
Compress-Archive -Path "$staging\*" -DestinationPath $zip -Force
Write-Host "ZIP de atualização: $zip" -ForegroundColor Cyan

# 5) Instalador
& "$PSScriptRoot\build_installer.ps1"
Write-Host "Build concluído!" -ForegroundColor Green
