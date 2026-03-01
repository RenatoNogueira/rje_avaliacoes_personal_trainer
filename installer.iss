; Script de instalação para RJE Avaliações
; Criado para Inno Setup

[Setup]
; Informações básicas do aplicativo
AppName=RJE Avaliações
AppVersion=1.0.32
AppPublisher=Renato Nogueira
DefaultDirName=C:\RJE_Avaliacoes
DefaultGroupName=RJE Avaliações
AllowNoIcons=yes
; Local do arquivo de licença (ajuste se necessário)
LicenseFile=LICENSE.txt
; Nome do instalador final
OutputBaseFilename=RJE_Avaliacoes_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; Ícone do instalador
SetupIconFile=icon.ico

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Inclui todos os arquivos da pasta dist/Release (agora em modo 'onedir')
Source: "dist\Release\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTA: Adicione outros arquivos necessários aqui se não estiverem no dist

[Icons]
Name: "{group}\RJE Avaliações"; Filename: "{app}\RJE_Avaliacoes.exe"
Name: "{commondesktop}\RJE Avaliações"; Filename: "{app}\RJE_Avaliacoes.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\RJE_Avaliacoes.exe"; Description: "{cm:LaunchProgram,RJE Avaliações}"; Flags: nowait postinstall skipifsilent
