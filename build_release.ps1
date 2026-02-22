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
$pyinstaller = ".\.venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $pyinstaller)) {
    $pyinstaller = "pyinstaller" # Fallback para o global
}
& $pyinstaller --noconfirm --clean rje_avaliacoes.spec

if ($LASTEXITCODE -ne 0) {
    Write-Error "Falha no PyInstaller."
    exit 1
}

# 3. Copiar arquivos extras para a pasta dist/RJE_Avaliacoes
$distPath = "dist\RJE_Avaliacoes"

Write-Host "Copiando arquivos de configuração (.env)..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Copy-Item ".env" -Destination $distPath
} else {
    Write-Warning "Arquivo .env não encontrado na raiz! A atualização automática pode falhar sem ele."
}

# Opcional: Copiar icone se existir
if (Test-Path "icon.ico") {
    Copy-Item "icon.ico" -Destination $distPath
}

# 4. Compactar para ZIP
# Pega a versão do arquivo version.py
$versionContent = Get-Content "version.py" | Select-String '__version__ = "(.*)"'
$version = $versionContent.Matches.Groups[1].Value
$zipName = "RJE_Avaliacoes_v$version.zip"
$zipPath = "dist\$zipName"

Write-Host "Compactando para $zipName..." -ForegroundColor Yellow

# Compacta o CONTEÚDO da pasta RJE_Avaliacoes para que ao extrair fique na raiz ou crie pasta
# O ideal para o updater é que o zip contenha a pasta ou os arquivos. 
# Vamos zipar a PASTA RJE_Avaliacoes inteira para manter a estrutura.
Compress-Archive -Path "$distPath" -DestinationPath $zipPath -Force

Write-Host "Build concluído com sucesso!" -ForegroundColor Green
Write-Host "Arquivo pronto para upload: $zipPath" -ForegroundColor Cyan
