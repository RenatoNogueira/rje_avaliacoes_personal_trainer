# Script de Instalação Nativo - RJE Avaliações

$ErrorActionPreference = "Stop"

function Show-Welcome {
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "   Bem-vindo ao instalador RJE Avaliações" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Ask-Agreement {
    $license = Get-Content "LICENSE.txt" -Raw
    Write-Host "Leia os termos abaixo:" -ForegroundColor Yellow
    Write-Host "------------------------------------------"
    Write-Host $license
    Write-Host "------------------------------------------"
    
    $choice = Read-Host "Você aceita os termos e deseja prosseguir com a instalação? (S/N)"
    if ($choice -ne "S" -and $choice -ne "s") {
        Write-Host "Instalação cancelada pelo usuário." -ForegroundColor Red
        exit
    }
}

function Install-Files {
    $installPath = "C:\RJE_Avaliacoes"
    $sourcePath = "dist\RJE_Avaliacoes"

    if (-not (Test-Path $sourcePath)) {
        Write-Error "Pasta de origem não encontrada em $sourcePath. Certifique-se de que o build foi realizado."
        exit 1
    }

    Write-Host "Preparando para instalar em: $installPath" -ForegroundColor Cyan
    
    if (Test-Path $installPath) {
        $confirm = Read-Host "A pasta $installPath já existe. Deseja substituir os arquivos? (S/N)"
        if ($confirm -ne "S" -and $confirm -ne "s") {
            Write-Host "Instalação abortada." -ForegroundColor Yellow
            exit
        }
        Remove-Item $installPath -Recurse -Force
    }

    New-Item -ItemType Directory -Path $installPath -Force | Out-Null
    
    Write-Host "Copiando arquivos... Isso pode levar alguns segundos." -ForegroundColor Yellow
    Copy-Item "$sourcePath\*" -Destination $installPath -Recurse -Force
    
    Write-Host "Arquivos copiados com sucesso." -ForegroundColor Green
    return $installPath
}

function Create-Shortcut {
    param($TargetPath)

    $WshShell = New-Object -ComObject WScript.Shell
    $ShortcutPath = [System.IO.Path]::Combine([Environment]::GetFolderPath("Desktop"), "RJE Avaliações.lnk")
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = Join-Path $TargetPath "RJE_Avaliacoes.exe"
    $Shortcut.WorkingDirectory = $TargetPath
    $Shortcut.IconLocation = Join-Path $TargetPath "icon.ico"
    $Shortcut.Save()

    Write-Host "Atalho criado na Área de Trabalho." -ForegroundColor Green
}

# Execução do Instalador
try {
    Show-Welcome
    Ask-Agreement
    $installedPath = Install-Files
    Create-Shortcut -TargetPath $installedPath

    Write-Host ""
    Write-Host "Instalação concluída com sucesso!" -ForegroundColor Green
    Write-Host "Você pode abrir o programa através do atalho na Área de Trabalho." -ForegroundColor Cyan
}
catch {
    Write-Host "Ocorreu um erro durante a instalação: $($_.Exception.Message)" -ForegroundColor Red
}
