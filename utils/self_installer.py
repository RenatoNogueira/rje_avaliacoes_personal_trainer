import os
import sys
import shutil
import ctypes
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk

class SelfInstaller:
    TARGET_DIR = Path("C:/RJE_Avaliacoes")
    
    @classmethod
    def is_installed(cls):
        """Verifica se o app está rodando da pasta de destino."""
        if not getattr(sys, 'frozen', False):
            return True # No modo de desenvolvimento, ignora
            
        current_exe = Path(sys.executable).parent
        return current_exe.absolute() == cls.TARGET_DIR.absolute()

    @classmethod
    def run(cls):
        """Executa a lógica de instalação se necessário."""
        if cls.is_installed():
            return
            
        # Pergunta se o usuário deseja instalar
        root = ctk.CTk()
        root.withdraw()
        
        msg = ("O RJE Avaliações não está instalado no sistema.\n\n"
               "Deseja instalá-lo em C:\\RJE_Avaliacoes e criar um atalho no Desktop?\n\n"
               "(Você também pode clicar em 'Não' para executá-lo como portátil)")
               
        if messagebox.askyesno("Instalação", msg):
            cls.show_installer_gui()
            sys.exit(0) # Sai para que o usuário abra o atalho ou o app instalado
        else:
            root.destroy()

    @classmethod
    def show_installer_gui(cls):
        """Mostra a interface de instalação."""
        gui = InstallerGUI()
        gui.mainloop()

class InstallerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Instalador RJE Avaliações")
        self.geometry("500x400")
        self.resizable(False, False)
        
        # Centralizar
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self.header = ctk.CTkLabel(self, text="Termos de Uso", font=ctk.CTkFont(size=20, weight="bold"))
        self.header.grid(row=0, column=0, pady=20)
        
        # License Area
        self.textbox = ctk.CTkTextbox(self, width=450, height=200)
        self.textbox.grid(row=1, column=0, padx=25, pady=10, sticky="nsew")
        
        license_path = Path(sys._MEIPASS) / "LICENSE.txt" if hasattr(sys, '_MEIPASS') else Path("LICENSE.txt")
        if license_path.exists():
            self.textbox.insert("0.0", license_path.read_text(encoding="utf-8"))
        else:
            self.textbox.insert("0.0", "Arquivo de licença não encontrado.")
        self.textbox.configure(state="disabled")
        
        # Checkbox
        self.accept_var = ctk.BooleanVar(value=False)
        self.checkbox = ctk.CTkCheckBox(self, text="Eu aceito os termos e condições", variable=self.accept_var, command=self.toggle_button)
        self.checkbox.grid(row=2, column=0, pady=10)
        
        # Button
        self.btn_install = ctk.CTkButton(self, text="Instalar Agora", state="disabled", command=self.start_install)
        self.btn_install.grid(row=3, column=0, pady=20)

    def toggle_button(self):
        if self.accept_var.get():
            self.btn_install.configure(state="normal")
        else:
            self.btn_install.configure(state="disabled")

    def start_install(self):
        self.btn_install.configure(state="disabled", text="Instalando...")
        self.checkbox.configure(state="disabled")
        self.update()
        
        try:
            target = SelfInstaller.TARGET_DIR
            # No OneFile, os arquivos internos estão em _MEIPASS
            source_internal = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(".")
            current_exe = Path(sys.executable)
            
            if target.exists():
                # Tenta remover, mas ignora erros de arquivos em uso
                shutil.rmtree(target, ignore_errors=True)
            
            os.makedirs(target, exist_ok=True)
            
            # Copiar arquivos de dados/configuração internos
            # Queremos manter a estrutura de pastas originais (gui, reports, etc.) na pasta de destino para que o app funcione
            # No entanto, se o app for OneFile, ele continuará procurando em _MEIPASS a menos que mudemos a lógica.
            # Mas o usuário quer que ele descompacte o sistema.
            
            # Vamos copiar o EXE para o destino
            shutil.copy2(current_exe, target / "RJE_Avaliacoes.exe")
            
            # Copiar pastas e arquivos que o sistema precisa ter "fora" do exe (como data/ e LICENSE)
            for folder in ["data", "gui", "reports", "utils", "assets"]:
                src_folder = source_internal / folder
                if src_folder.exists():
                    shutil.copytree(src_folder, target / folder, dirs_exist_ok=True)
            
            for file in ["LICENSE.txt", "icon.ico", "version.py", "exercises-ptbr-full-translation.json"]:
                src_file = source_internal / file
                if src_file.exists():
                    shutil.copy2(src_file, target / file)

            self._create_shortcut(target)
            
            messagebox.showinfo("Sucesso", "RJE Avaliações instalado com sucesso!\n\nUm atalho foi criado na sua área de trabalho.")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Erro na Instalação", f"Não foi possível completar a instalação: {e}")
            self.btn_install.configure(state="normal", text="Instalar Agora")

    def _create_shortcut(self, target_path):
        try:
            import subprocess
            
            exe_path = str(target_path / "RJE_Avaliacoes.exe")
            icon_path = str(target_path / "icon.ico")
            work_dir = str(target_path)
            
            # Comando PowerShell para criar o atalho
            ps_command = (
                f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut(\"$([Environment]::GetFolderPath('Desktop'))\\RJE Avaliações.lnk\"); "
                f"$s.TargetPath = '{exe_path}'; "
                f"$s.WorkingDirectory = '{work_dir}'; "
                f"$s.IconLocation = '{icon_path}'; "
                f"$s.Save()"
            )
            
            subprocess.run(["powershell", "-Command", ps_command], capture_output=True, check=True)
            
        except Exception as e:
            messagebox.showwarning("Aviso", f"Não foi possível criar o atalho no Desktop: {e}\n\nVocê pode criar um atalho manualmente para C:\\RJE_Avaliacoes\\RJE_Avaliacoes.exe")
