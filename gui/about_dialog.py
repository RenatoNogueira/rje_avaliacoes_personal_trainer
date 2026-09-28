import customtkinter as ctk
from .theme import _c, font_title, font_subtitle, font_body, create_info_badge, create_action_button
from .utils import set_window_icon
from utils.updater import Updater
from version import __version__
import app_paths

class AboutDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        
        self.title("Sobre o RJE Avaliações")
        self.geometry("450x610")
        self.resizable(False, False)
        
        # Configuração da Janela Modal
        self.transient(master)
        self.grab_set()
        self.focus_force()
        
        # Container Principal (Fundo Suave)
        self.configure(fg_color=_c("panel_bg"))
        
        # Card Central
        self.main_frame = ctk.CTkFrame(self, corner_radius=20, fg_color=_c("login_card_bg"))
        self.main_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        # Logo Hero Area
        self.logo_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.logo_frame.pack(pady=(35, 10))
        
        # Círculo de fundo com borda sutil
        logo_bg = ctk.CTkFrame(
            self.logo_frame, width=110, height=110, corner_radius=55, 
            fg_color=_c("view_header_icon_bg")
        )
        logo_bg.pack()
        logo_bg.pack_propagate(False)
        
        logo_image = None
        logo_path = getattr(master, "logo_path", None)
        set_window_icon(self, logo_path)
        
        if logo_path:
            from pathlib import Path
            from PIL import Image
            if Path(logo_path).exists():
                try:
                    pil_img = Image.open(logo_path)
                    w, h = pil_img.size
                    k = 85 / max(w, h) if max(w, h) else 1
                    logo_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img,
                                              size=(max(1, int(w * k)), max(1, int(h * k))))
                except Exception:
                    pass

        if logo_image:
            ctk.CTkLabel(logo_bg, text="", image=logo_image).pack(expand=True)
        else:
            ctk.CTkLabel(logo_bg, text="🏋️", font=ctk.CTkFont(size=54)).pack(expand=True)
        
        # Títulos
        ctk.CTkLabel(
            self.main_frame, 
            text="RJE Avaliações", 
            font=ctk.CTkFont(family="Inter", size=28, weight="bold"),
            text_color=_c("view_header_title")
        ).pack(pady=(12, 4))
        
        # Badge de Versão
        ver_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        ver_frame.pack(pady=(0, 15))
        
        self.version_badge = create_info_badge(ver_frame, f"Versão {__version__}")
        self.version_badge.pack()

        # Descrição em um "inset card"
        self.desc_frame = ctk.CTkFrame(self.main_frame, fg_color=_c("section_bg"), corner_radius=12)
        self.desc_frame.pack(padx=30, pady=(0, 20), fill="x")
        
        ctk.CTkLabel(
            self.desc_frame, 
            text="Plataforma de alta performance para\nprofissionais de educação física.\nGestão de alunos, protocolos e resultados.", 
            font=font_subtitle(),
            justify="center",
            text_color=_c("view_header_subtitle")
        ).pack(padx=15, pady=18)

        # Botão de Atualização Estilizado
        self.btn_update = create_action_button(
            self.main_frame,
            text="Verificar Atualizações",
            color_key="btn_save",
            command=self.check_updates,
            width=200
        )
        self.btn_update.pack(pady=(0, 10))

        # Label de Erro Detalhado (Oculta por padrão)
        self.lbl_error = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#e74c3c",
            wraplength=350
        )
        self.lbl_error.pack(pady=(0, 6))

        # Informações úteis para suporte
        ctk.CTkLabel(
            self.main_frame,
            text=f"Dados: {app_paths.DATA_ROOT}\nAtalhos: pressione F1 na tela principal",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            justify="center",
            wraplength=360,
        ).pack(pady=(0, 12))

        self.bind("<Escape>", lambda e: self.destroy())

    def check_updates(self):
        self.lbl_error.configure(text="")
        self.btn_update.configure(state="disabled", text="Verificando...")
        self.updater = Updater(self)
        self.updater.check_for_updates_async(self.on_update_checked)

    def on_update_checked(self, has_update, error_msg=None):
        self.after(0, lambda: self._update_ui_after_check(has_update, error_msg))

    def _update_ui_after_check(self, has_update, error_msg=None):
        if has_update is True:
            self.lbl_error.configure(text="")
            self.btn_update.configure(
                state="normal", 
                text=f"Atualizar para {self.updater.latest_version}",
                fg_color="#2ecc71", 
                text_color="white",
                hover_color="#27ae60",
                border_width=0,
                command=self.updater.perform_update
            )
            from .utils import show_toast
            show_toast(self, "Nova versão disponível!", 3000)
        elif has_update is False:
            self.lbl_error.configure(text="")
            self.btn_update.configure(
                state="disabled", 
                text="Sistema Atualizado", 
                fg_color="transparent",
                border_color="green",
                text_color="green"
            )
        else:
            # Caso de erro
            self.btn_update.configure(
                state="normal", 
                text="Tentar Novamente", 
                fg_color="transparent",
                border_color="#e74c3c",
                text_color="#e74c3c",
                command=self.check_updates
            )
            # Mostra erro detalhado na label
            self.lbl_error.configure(text=f"Erro: {error_msg}" if error_msg else "Falha ao conectar com GitHub")
            
            if error_msg:
                from .utils import show_toast
                show_toast(self, "Falha na verificação", 3000)
