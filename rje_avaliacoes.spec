# -*- mode: python ; coding: utf-8 -*-
# Spec versionado do RJE Avaliações (onedir, sem console).
# Gerar:  pyinstaller --noconfirm --clean rje_avaliacoes.spec
from PyInstaller.utils.hooks import collect_data_files

datas = [
    ("exercises-ptbr-full-translation.json", "."),
    ("assets/logo_rje.png", "assets"),
    ("icon.ico", "."),
    ("LICENSE.txt", "."),
]
datas += collect_data_files("customtkinter")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=["PIL._tkinter_finder"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Bibliotecas não utilizadas pelo sistema: reduzem o tamanho e alertas de antivírus
    excludes=["matplotlib", "numpy", "pandas", "scipy", "IPython", "pytest", "CTkMessagebox"],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RJE_Avaliacoes",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX aumenta falsos positivos de antivírus
    console=False,
    disable_windowed_traceback=False,
    icon="icon.ico",
    version="file_version_info.txt",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="RJE_Avaliacoes",
)
