# Script para gerar release completa do RJE Avaliações
# 1. Gera executável
# 2. Copia .env e outros arquivos necessários
# 3. Compacta para ZIP

$ErrorActionPreference = "Stop"

Write-Host "Iniciando build do RJE Avaliações..." -ForegroundColor Green

# 1. Limpar pastas de build antigas
$oldPaths = @("dist", "dist_fix", "dist_fix_v2", "dist_final", "build")
foreach ($path in $oldPaths) {
    if (Test-Path $path) {
        Write-Host "Limpando $path..." -ForegroundColor Gray
        Remove-Item $path -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# 2. Executar PyInstaller
Write-Host "Executando PyInstaller..." -ForegroundColor Yellow
$pypython = ".\.venv\Scripts\python.exe"
if (Test-Path $pypython) {
    & $pypython -m PyInstaller --noconfirm --clean --distpath dist_final rje_avaliacoes.spec
}
else {
    pyinstaller --noconfirm --clean --distpath dist_final rje_avaliacoes.spec
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Falha no PyInstaller."
    exit 1
}

# 3. Preparar pasta de distribuição
$distPath = "dist_final\Release"
if (Test-Path $distPath) { Remove-Item $distPath -Recurse -Force }
New-Item -ItemType Directory -Path $distPath | Out-Null

Write-Host "Copiando arquivos da distribuição (onedir)..." -ForegroundColor Yellow
# Copia todo o conteúdo gerado pelo PyInstaller (exe, dlls, _internal)
Copy-Item "dist_final\RJE_Avaliacoes\*" -Destination $distPath -Recurse -Force

Write-Host "Copiando arquivos de configuração (.env)..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Copy-Item ".env" -Destination $distPath
}
else {
    Write-Warning "Arquivo .env não encontrado! O token de atualização não será incluído."
}

# 4. Compactar para ZIP
$versionContent = Get-Content "version.py" | Select-String '__version__ = "(.*)"'
$version = $versionContent.Matches.Groups[1].Value
$zipName = "RJE_Avaliacoes_v$version.zip"
$zipPath = "dist_final\$zipName"

Write-Host "Compactando para $zipName..." -ForegroundColor Yellow
Compress-Archive -Path "$distPath\*" -DestinationPath $zipPath -Force

Write-Host "Build concluído com sucesso!" -ForegroundColor Green
Write-Host "Arquivo pronto para upload: $zipPath" -ForegroundColor Cyan
