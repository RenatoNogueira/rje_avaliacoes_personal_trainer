# Script para compilar o Instalador EXE (Requer Inno Setup)

$iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if (-not (Test-Path $iscc)) {
    Write-Warning "Inno Setup Compiler (ISCC.exe) não encontrado em $iscc."
    Write-Host "Por favor, instale o Inno Setup ou ajuste o caminho no script." -ForegroundColor Yellow
    exit 1
}

Write-Host "Compilando o instalador..." -ForegroundColor Cyan
& $iscc installer.iss

if ($LASTEXITCODE -eq 0) {
    Write-Host "Instalador gerado com sucesso na pasta 'Output'!" -ForegroundColor Green
} else {
    Write-Error "Falha ao compilar o instalador."
}
