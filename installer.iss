; ============================================================================
;  Instalador do RJE Avaliações (Inno Setup 6)
;  Gerar:  ISCC.exe installer.iss      (ou execute build_installer.ps1)
; ============================================================================

#define AppName      "RJE Avaliações"
#define AppVersion   "1.1.0"
#define AppPublisher "RJE Tecnologia"
#define AppExeName   "RJE_Avaliacoes.exe"
#define SourceDir    "dist\RJE_Avaliacoes"

[Setup]
; AppId igual ao nome usado nas versões anteriores -> atualiza a instalação existente
AppId={#AppName}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
VersionInfoVersion={#AppVersion}.0
VersionInfoCompany={#AppPublisher}
VersionInfoDescription=Instalador do {#AppName}
; Pasta mantida para compatibilidade com o atualizador automático (que grava na pasta do app)
DefaultDirName=C:\RJE_Avaliacoes
DisableProgramGroupPage=yes
DefaultGroupName={#AppName}
UsePreviousAppDir=yes
PrivilegesRequired=admin
#if Ver >= 0x06030000
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
#else
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
#endif
MinVersion=10.0
LicenseFile=LICENSE.txt
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
OutputDir=output
OutputBaseFilename=RJE_Avaliacoes_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; Fecha o sistema automaticamente se estiver aberto durante a atualização
AppMutex=RJE_Avaliacoes_SingleInstance,Global\RJE_Avaliacoes_SingleInstance
CloseApplications=yes
RestartApplications=no
; Assinatura digital opcional (ativada pelo build_release.ps1 quando há certificado)
#ifdef SIGN
SignTool=rjesign
SignedUninstaller=yes
#endif

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Dirs]
; Permite que o atualizador automático substitua arquivos sem pedir administrador
Name: "{app}"; Permissions: users-modify
; Dados do usuário (banco, fotos, backups): compartilhados e preservados em atualizações
Name: "{commonappdata}\RJE Avaliacoes"; Permissions: users-modify; Flags: uninsneveruninstall

[InstallDelete]
; Remove bibliotecas e cópias de código de versões antigas que não são mais usadas
; (os DADOS antigos em _internal\data e _internal\media NÃO são removidos: são migrados na 1ª execução)
Type: filesandordirs; Name: "{app}\_internal\matplotlib"
Type: filesandordirs; Name: "{app}\_internal\numpy"
Type: filesandordirs; Name: "{app}\_internal\numpy.libs"
Type: filesandordirs; Name: "{app}\_internal\numpy-*.dist-info"
Type: filesandordirs; Name: "{app}\_internal\contourpy"
Type: filesandordirs; Name: "{app}\_internal\kiwisolver"
Type: filesandordirs; Name: "{app}\_internal\gui"
Type: filesandordirs; Name: "{app}\_internal\reports"
Type: filesandordirs; Name: "{app}\_internal\utils"
Type: files; Name: "{app}\_internal\version.py"
; Remove o .env com token do GitHub distribuído pelas versões antigas (não é mais usado)
Type: files; Name: "{app}\.env"

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent

[Messages]
brazilianportuguese.FinishedLabel=O {#AppName} foi instalado.%n%nSeus dados ficam em %nC:\ProgramData\RJE Avaliacoes%ne são preservados em atualizações.
