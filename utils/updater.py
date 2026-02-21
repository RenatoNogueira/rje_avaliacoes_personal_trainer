import json
import urllib.request
import zipfile
import os
import sys
import shutil
import threading
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk

from version import __version__, GITHUB_REPO

class Updater:
    def __init__(self, master_window):
        self.master = master_window
        self.current_version = __version__
        self.repo = GITHUB_REPO
        self.latest_version = None
        self.download_url = None
        self.release_notes = ""

    def check_for_updates_async(self, callback=None):
        """Inicia a verificação em uma thread separada para não travar a UI."""
        thread = threading.Thread(target=self._check_worker, args=(callback,))
        thread.daemon = True
        thread.start()

    def _check_worker(self, callback):
        try:
            # 1. Obter releases do GitHub
            api_url = f"https://api.github.com/repos/{self.repo}/releases/latest"
            req = urllib.request.Request(api_url)
            req.add_header("User-Agent", "RJE-Avaliacoes-Updater")
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
            tag_name = data.get("tag_name", "").lstrip("v")
            self.latest_version = tag_name
            self.release_notes = data.get("body", "")
            
            # 2. Comparar versões (semântica simples)
            if self._is_newer(tag_name, self.current_version):
                # Pegar URL do zipball ou asset específico
                self.download_url = data.get("zipball_url") # ou assets[0].browser_download_url
                if callback:
                    callback(True) # Atualização disponível
            else:
                if callback:
                    callback(False) # Sem atualização
                    
        except Exception as e:
            print(f"Erro ao verificar atualizações: {e}")
            if callback:
                callback(False)

    def _is_newer(self, remote_ver, local_ver):
        # Comparação básica de strings ou tuplas
        try:
            r_parts = [int(x) for x in remote_ver.split(".")]
            l_parts = [int(x) for x in local_ver.split(".")]
            return r_parts > l_parts
        except Exception:
            return remote_ver != local_ver

    def perform_update(self):
        """Baixa e aplica a atualização."""
        if not self.download_url:
            return
            
        try:
            # 1. Download
            temp_zip = Path("update.zip")
            urllib.request.urlretrieve(self.download_url, temp_zip)
            
            # 2. Extrair
            extract_dir = Path("update_temp")
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir()
            
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
                
            # O zip do GitHub geralmente cria uma pasta raiz (user-repo-hash). 
            # Precisamos mover o conteúdo dela para a raiz do app.
            content_dir = next(extract_dir.iterdir())
            if not content_dir.is_dir():
                # Fallback se não tiver subpasta
                content_dir = extract_dir

            # 3. Substituir arquivos (exceto configs e DB)
            app_dir = Path.cwd()
            ignored_files = {"database.db", ".env", "settings.json", "custom_settings.json", ".venv", "__pycache__", ".git"}
            
            for item in content_dir.iterdir():
                if item.name in ignored_files:
                    continue
                    
                dest = app_dir / item.name
                
                # Se for diretório, mesclar/substituir
                if item.is_dir():
                    if dest.exists():
                        # shutil.copytree(item, dest, dirs_exist_ok=True) # Python 3.8+
                        self._copy_tree_recursive(item, dest)
                    else:
                        shutil.copytree(item, dest)
                else:
                    # Arquivo
                    try:
                        shutil.copy2(item, dest)
                    except PermissionError:
                        # Arquivo em uso (ex: main.py ou dlls). 
                        # No Windows, não dá pra substituir o executável em uso facilmente.
                        # Para scripts Python puros, às vezes funciona se não for o arquivo principal bloqueado.
                        print(f"Não foi possível substituir {item.name}. Arquivo em uso.")
                        pass

            # 4. Limpeza
            temp_zip.unlink()
            shutil.rmtree(extract_dir)
            
            messagebox.showinfo("Sucesso", "Atualização aplicada! O sistema será reiniciado.")
            self._restart_app()

        except Exception as e:
            messagebox.showerror("Erro", f"Falha na atualização: {e}")

    def _copy_tree_recursive(self, src, dst):
        if not dst.exists():
            dst.mkdir(parents=True)
        for item in src.iterdir():
            d = dst / item.name
            if item.is_dir():
                self._copy_tree_recursive(item, d)
            else:
                shutil.copy2(item, d)

    def _restart_app(self):
        python = sys.executable
        os.execl(python, python, *sys.argv)
