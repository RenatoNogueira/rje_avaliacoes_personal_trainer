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

    def _get_base_path(self):
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        else:
            return Path(__file__).resolve().parent.parent

    def _check_worker(self, callback):
        try:
            # 1. Obter releases do GitHub
            api_url = f"https://api.github.com/repos/{self.repo}/releases/latest"
            
            req = urllib.request.Request(api_url)
            req.add_header("User-Agent", "RJE-Avaliacoes-Updater")
            
            # Autenticação para repositórios privados
            # Tenta ler do arquivo .env ou variável de ambiente
            github_token = os.environ.get("GITHUB_TOKEN")
            if not github_token:
                try:
                    base_path = self._get_base_path()
                    env_path = base_path / ".env"
                    if env_path.exists():
                        with env_path.open("r") as f:
                            for line in f:
                                if line.startswith("GITHUB_TOKEN="):
                                    github_token = line.strip().split("=", 1)[1].strip()
                                    break
                except Exception as e:
                    print(f"Erro ao ler .env: {e}")
            
            if github_token:
                req.add_header("Authorization", f"token {github_token}")
            else:
                print("Aviso: Token do GitHub não encontrado. Atualizações de repositório privado podem falhar.")
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
            tag_name = data.get("tag_name", "").lstrip("v")
            self.latest_version = tag_name
            self.release_notes = data.get("body", "")
            
            print(f"Versão Local: {self.current_version} | Versão Remota: {tag_name}")
            
            # 2. Comparar versões (semântica simples)
            if self._is_newer(tag_name, self.current_version):
                # Prioriza asset zip (binário) se estiver no modo frozen
                download_url = None
                
                # Se estamos rodando como EXE, procura um asset .zip na lista de assets
                if getattr(sys, 'frozen', False):
                    assets = data.get("assets", [])
                    for asset in assets:
                        if asset.get("name", "").lower().endswith(".zip"):
                            download_url = asset.get("url") # URL da API para download autenticado
                            break
                
                # Se não achou (ou não é exe), usa o zipball do código fonte
                if not download_url:
                    download_url = data.get("zipball_url")
                
                self.download_url = download_url
                
                if callback:
                    callback(True) # Atualização disponível
            else:
                if callback:
                    callback(False) # Sem atualização
                    
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"Nenhuma release encontrada no repositório {self.repo}.")
            else:
                print(f"Erro HTTP ao verificar atualizações: {e}")
            if callback:
                callback(False)
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
            
            # Adicionar headers para download também, se for asset privado
            req = urllib.request.Request(self.download_url)
            req.add_header("User-Agent", "RJE-Avaliacoes-Updater")
            req.add_header("Accept", "application/octet-stream") 
            
            github_token = os.environ.get("GITHUB_TOKEN")
            if not github_token:
                 try:
                     base_path = self._get_base_path()
                     env_path = base_path / ".env"
                     if env_path.exists():
                         with env_path.open("r") as f:
                             for line in f:
                                 if line.startswith("GITHUB_TOKEN="):
                                     github_token = line.strip().split("=", 1)[1].strip()
                                     break
                 except Exception:
                     pass
            
            if github_token:
                req.add_header("Authorization", f"token {github_token}")

            with urllib.request.urlopen(req, timeout=30) as response, open(temp_zip, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
            
            # 2. Lógica para EXE ou Código Fonte
            if getattr(sys, 'frozen', False):
                # Se for executável, precisa usar script externo para substituir
                self._update_frozen(temp_zip)
            else:
                # Se for script Python, atualiza normalmente
                self._update_source(temp_zip)

        except Exception as e:
            messagebox.showerror("Erro", f"Falha na atualização: {e}")

    def _update_source(self, temp_zip):
        # ... lógica original de extração e substituição ...
        extract_dir = Path("update_temp")
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir()
        
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        content_dir = next(extract_dir.iterdir())
        if not content_dir.is_dir():
            content_dir = extract_dir

        app_dir = Path.cwd()
        ignored_files = {"database.db", ".env", "settings.json", "custom_settings.json", ".venv", "__pycache__", ".git", "update.zip"}
        
        for item in content_dir.iterdir():
            if item.name in ignored_files:
                continue
            dest = app_dir / item.name
            if item.is_dir():
                if dest.exists():
                    self._copy_tree_recursive(item, dest)
                else:
                    shutil.copytree(item, dest)
            else:
                try:
                    shutil.copy2(item, dest)
                except PermissionError:
                    pass

        temp_zip.unlink()
        shutil.rmtree(extract_dir)
        messagebox.showinfo("Sucesso", "Atualização aplicada! O sistema será reiniciado.")
        self._restart_app()

    def _update_frozen(self, temp_zip):
        # Extrai para pasta temporária
        extract_dir = Path("update_temp_exe")
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir()
        
        try:
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except zipfile.BadZipFile:
            messagebox.showerror("Erro", "Arquivo de atualização corrompido.")
            return

        # Lógica robusta para encontrar a pasta raiz do conteúdo
        # Muitas vezes o zip tem uma pasta raiz (ex: RJE_Avaliacoes_v1.0.2) e dentro dela estão os arquivos
        content_dir = extract_dir
        items = list(extract_dir.iterdir())
        
        # Se tiver apenas uma pasta, entra nela (comportamento padrão de zips)
        if len(items) == 1 and items[0].is_dir():
            content_dir = items[0]
            
            # Verifica se essa pasta contém o executável ou a pasta _internal
            # Se não, pode ser que o zip tenha estrutura diferente.
            # Mas vamos assumir que o usuário zipou a pasta 'RJE_Avaliacoes' da dist.
            pass

        app_exe = sys.executable
        app_dir = Path.cwd() # Onde o executável atual está rodando
        
        # Script BAT melhorado
        # - Usa caminhos absolutos
        # - Espera PID (opcional, mas timeout resolve)
        # - xcopy com flags para sobrescrever tudo
        
        bat_script = f"""
@echo off
echo Aguardando fechamento do aplicativo...
timeout /t 4 /nobreak >nul

echo Atualizando arquivos...
xcopy "{content_dir.absolute()}\\*" "{app_dir.absolute()}" /E /H /Y /C /Q

echo Limpando arquivos temporarios...
rd /s /q "{extract_dir.absolute()}"
del "{temp_zip.absolute()}"

echo Reiniciando aplicativo...
start "" "{app_exe}"
del "%~f0"
"""
        bat_path = app_dir / "update_script.bat"
        with open(bat_path, "w") as f:
            f.write(bat_script)
            
        messagebox.showinfo("Atualização", "O sistema será fechado para aplicar a atualização.\nAguarde alguns instantes e ele reabrirá automaticamente.")
        
        # Executa o bat e fecha o app
        try:
            os.startfile(bat_path)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar script de atualização: {e}")
            return
            
        sys.exit(0)


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
