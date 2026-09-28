# Compila o instalador (requer Inno Setup 6: https://jrsoftware.org/isdl.php)
# Se houver certificado configurado (ver ASSINATURA_DIGITAL.md), o instalador
# e o desinstalador são assinados automaticamente.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
. "$PSScriptRoot\sign_tools.ps1"

$candidatos = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$iscc = $candidatos | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
    $cmd = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($cmd) { $iscc = $cmd.Source }
}
if (-not $iscc) {
    Write-Warning "Inno Setup (ISCC.exe) não encontrado. Instale o Inno Setup 6 e execute novamente."
    exit 1
}
if (-not (Test-Path "dist\RJE_Avaliacoes\RJE_Avaliacoes.exe")) {
    Write-Warning "Executável não encontrado em dist\RJE_Avaliacoes. Rode build_release.ps1 primeiro."
    exit 1
}

$args = @("installer.iss")
if (Test-RjeSigning) {
    $cmdSign = Get-RjeSignCommand   # contém $f, substituído pelo Inno pelo arquivo a assinar
    $args = @("/DSIGN", "/Srjesign=$cmdSign") + $args
    Write-Host "Instalador será assinado digitalmente." -ForegroundColor Cyan
}

Write-Host "Compilando o instalador com $iscc ..." -ForegroundColor Cyan
& $iscc @args
if ($LASTEXITCODE -eq 0) {
    Write-Host "Instalador gerado em output\RJE_Avaliacoes_Setup.exe" -ForegroundColor Green
} else {
    throw "Falha ao compilar o instalador."
}
