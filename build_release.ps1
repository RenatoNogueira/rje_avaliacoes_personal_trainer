# Script para gerar release completa do RJE Avaliações
# 1. Gera executável
# 2. Copia .env e outros arquivos necessários
# 3. Compacta para ZIP

$ErrorActionPreference = "Stop"

Write-Host "Iniciando build do RJE Avaliações..." -ForegroundColor Green

# 1. Limpar pasta dist antiga
if (Test-Path "dist") {
    Remove-Item "dist" -Recurse -Force
}

# 2. Executar PyInstaller
Write-Host "Executando PyInstaller..." -ForegroundColor Yellow
$pypython = ".\.venv\Scripts\python.exe"
if (Test-Path $pypython) {
    & $pypython -m PyInstaller --noconfirm --clean rje_avaliacoes.spec
}
else {
    pyinstaller --noconfirm --clean rje_avaliacoes.spec
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Falha no PyInstaller."
    exit 1
}

# 3. Preparar pasta de distribuição
$distPath = "dist\Release"
if (Test-Path $distPath) { Remove-Item $distPath -Recurse -Force }
New-Item -ItemType Directory -Path $distPath | Out-Null

Write-Host "Copiando executável final..." -ForegroundColor Yellow
Copy-Item "dist\RJE_Avaliacoes.exe" -Destination $distPath

Write-Host "Copiando arquivos de configuração (.env)..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Copy-Item ".env" -Destination $distPath
}

# 4. Compactar para ZIP
$versionContent = Get-Content "version.py" | Select-String '__version__ = "(.*)"'
$version = $versionContent.Matches.Groups[1].Value
$zipName = "RJE_Avaliacoes_v$version.zip"
$zipPath = "dist\$zipName"

Write-Host "Compactando para $zipName..." -ForegroundColor Yellow
Compress-Archive -Path "$distPath\*" -DestinationPath $zipPath -Force

Write-Host "Build concluído com sucesso!" -ForegroundColor Green
Write-Host "Arquivo pronto para upload: $zipPath" -ForegroundColor Cyan
