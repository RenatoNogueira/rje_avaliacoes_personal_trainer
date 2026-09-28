# Funções de assinatura digital (Authenticode) usadas pelos scripts de build.
$RjeTimestampUrl = "http://timestamp.digicert.com"

function Find-SignTool {
    $cmd = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $kits = Get-ChildItem "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1
    if ($kits) { return $kits.FullName }
    return $null
}

function Test-RjeSigning {
    return [bool]($env:RJE_SIGN_THUMBPRINT -or $env:RJE_SIGN_PFX)
}

function Get-RjeSignArgs {
    if ($env:RJE_SIGN_THUMBPRINT) {
        return "/sha1 $($env:RJE_SIGN_THUMBPRINT)"
    }
    $a = "/f `"$($env:RJE_SIGN_PFX)`""
    if ($env:RJE_SIGN_PASSWORD) { $a += " /p `"$($env:RJE_SIGN_PASSWORD)`"" }
    return $a
}

function Get-RjeSignCommand {
    $st = Find-SignTool
    if (-not $st) { throw "signtool.exe não encontrado. Instale o Windows SDK (componente 'Signing Tools')." }
    # Formato do Inno Setup: $q = aspas, $f = arquivo a assinar (evita problemas de aspas do PowerShell)
    $argsInno = (Get-RjeSignArgs).Replace('"', '$q')
    return "`$q$st`$q sign $argsInno /fd sha256 /tr $RjeTimestampUrl /td sha256 /d `$qRJE Avaliacoes`$q `$f"
}

function Invoke-RjeSign([string]$file) {
    $st = Find-SignTool
    if (-not $st) { throw "signtool.exe não encontrado. Instale o Windows SDK (componente 'Signing Tools')." }
    $cmd = "`"$st`" sign $(Get-RjeSignArgs) /fd sha256 /tr $RjeTimestampUrl /td sha256 /d `"RJE Avaliações`" `"$file`""
    cmd /c $cmd
    if ($LASTEXITCODE -ne 0) { throw "Falha ao assinar $file" }
    Write-Host "Assinado: $file" -ForegroundColor Green
}
