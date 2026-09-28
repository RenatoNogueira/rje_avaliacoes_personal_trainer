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

from version import __version__, GITHUB_REPO, UPDATE_REPOS
import app_paths
import tempfile

class Updater:
    def __init__(self, master_window):
        self.master = master_window
        self.current_version = __version__
        self.repo = GITHUB_REPO
        self.latest_version = None
        self.download_url = None
        self.release_notes = ""
        self.log_file = app_paths.LOG_DIR / "updater.log"
        self._log(f"--- Iniciando Updater {self.current_version} ---")
        self._log(f"Base Path: {self._get_base_path()}")
        self._log(f"Log File: {self.log_file}")

    def _log(self, message):
        """Grava logs para diagnóstico."""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            # Garante que a pasta data exista
            log_dir = self.log_file.parent
            if not log_dir.exists():
                log_dir.mkdir(parents=True)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass

    def check_for_updates_async(self, callback=None):
        """Inicia a verificação em uma thread separada para não travar a UI."""
        thread = threading.Thread(target=self._check_worker, args=(callback,))
        thread.daemon = True
        thread.start()

    def _get_base_path(self):
        return app_paths.APP_DIR

    def _fetch_latest(self, repo):
        """Consulta a última release de um repositório público (sem token)."""
        api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        req = urllib.request.Request(api_url)
        req.add_header("User-Agent", "RJE-Avaliacoes-Desktop-App")
        req.add_header("Accept", "application/vnd.github+json")
        self._log(f"Chamando API: {api_url}")
        with urllib.request.urlopen(req, timeout=12) as response:
            return json.loads(response.read().decode())

    def _check_worker(self, callback):
        def _notify(has_update, err=None):
            if callback:
                try:
                    callback(has_update, err)
                except TypeError:
                    callback(bool(has_update))

        data = None
        last_error = None
        for repo in UPDATE_REPOS:
            try:
                data = self._fetch_latest(repo)
                self.repo = repo
                break
            except urllib.error.HTTPError as e:
                last_error = e
                self._log(f"{repo}: HTTP {e.code} ({e.reason})")
            except Exception as e:
                last_error = e
                self._log(f"{repo}: {e}")

        if data is None:
            if isinstance(last_error, urllib.error.HTTPError) and last_error.code in (401, 403, 404):
                err_msg = ("Nenhuma release pública encontrada. Publique a versão em um "
                           "repositório público do GitHub (veja DEPLOY_GUIDE.md).")
                if last_error.code == 403:
                    err_msg = "Limite de consultas do GitHub atingido. Tente novamente mais tarde."
            else:
                err_msg = f"Sem conexão com o GitHub ({last_error})."
            self._log(err_msg)
            _notify(None, err_msg)
            return

        tag_name = data.get("tag_name", "").lstrip("v")
        self.latest_version = tag_name
        self.release_notes = data.get("body", "")
        self._log(f"Versão remota {tag_name} encontrada em {self.repo}")

        if not self._is_newer(tag_name, self.current_version):
            _notify(False)
            return

        download_url = None
        if getattr(sys, "frozen", False):
            # URL pública de download direto (não exige autenticação)
            for asset in data.get("assets", []):
                if asset.get("name", "").lower().endswith(".zip"):
                    download_url = asset.get("browser_download_url")
                    self._log(f"Pacote encontrado: {asset.get('name')}")
                    break
            if not download_url:
                self._log("Release sem arquivo .zip anexado.")
        else:
            download_url = data.get("zipball_url")
        self.download_url = download_url
        _notify(True)

    def _is_newer(self, remote_ver, local_ver):
        """Compara versões numericamente (ex: 1.0.24 > 1.0.23)."""
        try:
            def to_tuple(v):
                # Extrai apenas números e converte para tupla de ints
                import re
                parts = re.findall(r'\d+', v)
                return tuple(int(p) for p in parts)
            
            r_val = to_tuple(remote_ver)
            l_val = to_tuple(local_ver)
            return r_val > l_val
        except Exception:
            return str(remote_ver) != str(local_ver)

    def perform_update(self):
        """Baixa a atualização em segundo plano (com progresso) e depois aplica."""
        if not self.download_url:
            messagebox.showwarning("Atualização", "Nenhum pacote de atualização disponível para esta versão.")
            return

        temp_zip = Path(tempfile.gettempdir()) / "rje_avaliacoes_update.zip"
        progress = _ProgressWindow(self.master, "Baixando atualização...")
        state = {"done": 0, "total": 0, "error": None, "finished": False}

        def worker():
            try:
                req = urllib.request.Request(self.download_url)
                req.add_header("User-Agent", "RJE-Avaliacoes-Updater")
                req.add_header("Accept", "application/octet-stream")
                with urllib.request.urlopen(req, timeout=60) as response, open(temp_zip, "wb") as out_file:
                    state["total"] = int(response.headers.get("Content-Length") or 0)
                    while True:
                        chunk = response.read(256 * 1024)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        state["done"] += len(chunk)
            except Exception as e:
                state["error"] = e
                self._log(f"Falha no download: {e}")
            finally:
                state["finished"] = True

        def poll():
            if not state["finished"]:
                progress.set(state["done"], state["total"])
                self.master.after(200, poll)
                return
            progress.close()
            if state["error"] is not None:
                messagebox.showerror("Erro", f"Falha ao baixar a atualização:\n{state['error']}")
                return
            try:
                if getattr(sys, "frozen", False):
                    self._update_frozen(temp_zip)
                else:
                    self._update_source(temp_zip)
            except SystemExit:
                raise
            except Exception as e:
                messagebox.showerror("Erro", f"Falha na atualização: {e}")

        threading.Thread(target=worker, daemon=True).start()
        self.master.after(200, poll)

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
        extract_dir = Path(tempfile.gettempdir()) / "rje_update_temp_exe"
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
        app_dir = app_paths.APP_DIR  # Onde o executável atual está instalado
        
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
        bat_path = Path(tempfile.gettempdir()) / "rje_update_script.bat"
        with open(bat_path, "w", encoding="mbcs" if os.name == "nt" else "utf-8") as f:
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


class _ProgressWindow:
    """Janela simples de progresso para o download da atualização."""

    def __init__(self, master, title: str):
        self.win = ctk.CTkToplevel(master)
        self.win.title("Atualização")
        self.win.geometry("380x130")
        self.win.resizable(False, False)
        try:
            self.win.transient(master)
            self.win.grab_set()
        except Exception:
            pass
        self.win.protocol("WM_DELETE_WINDOW", lambda: None)
        ctk.CTkLabel(self.win, text=title, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(18, 8))
        self.bar = ctk.CTkProgressBar(self.win, width=320)
        self.bar.pack(pady=4)
        self.bar.set(0)
        self.lbl = ctk.CTkLabel(self.win, text="Conectando...")
        self.lbl.pack(pady=(4, 10))

    def set(self, done: int, total: int) -> None:
        try:
            if total > 0:
                self.bar.set(min(1.0, done / total))
                self.lbl.configure(text=f"{done / 1_048_576:.1f} de {total / 1_048_576:.1f} MB")
            else:
                self.lbl.configure(text=f"{done / 1_048_576:.1f} MB recebidos")
        except Exception:
            pass

    def close(self) -> None:
        try:
            self.win.grab_release()
            self.win.destroy()
        except Exception:
            pass
