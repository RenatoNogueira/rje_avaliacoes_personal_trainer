import customtkinter as ctk
from .theme import _c, font_title, font_subtitle, font_body, create_info_badge, create_action_button
from .utils import set_window_icon
from utils.updater import Updater

class AboutDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        
        self.title("Sobre o RJE Avaliações")
        self.geometry("450x560")
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
                    logo_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(85, 85))
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
        
        self.version_badge = create_info_badge(ver_frame, f"Versão {Updater(self).current_version}")
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
        self.btn_update.pack(pady=(0, 25))

        # Footer / Créditos
        footer_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            footer_frame, 
            text="© 2026 RJE Tecnologia", 
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=_c("view_header_subtitle")
        ).pack()
        
        ctk.CTkLabel(
            footer_frame, 
            text="Todos os direitos reservados.", 
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack()
        
        # Botão Fechar
        self.btn_close = ctk.CTkButton(
            self.main_frame,
            text="Fechar",
            width=90,
            height=28,
            fg_color="transparent",
            border_width=1,
            border_color=_c("card_border"),
            text_color=_c("view_header_title"),
            hover_color=_c("card_hover"),
            command=self.destroy
        )
        self.btn_close.pack(side="bottom", pady=(0, 15))


    def check_updates(self):
        self.btn_update.configure(state="disabled", text="Verificando...")
        self.updater = Updater(self)
        self.updater.check_for_updates_async(self.on_update_checked)

    def on_update_checked(self, has_update):
        # Callback executado na thread, precisa agendar na UI thread se ctk não for thread-safe (geralmente tkinter requer after)
        # Mas ctk muitas vezes lida ok, vamos usar after para garantir
        self.after(0, lambda: self._update_ui_after_check(has_update))

    def _update_ui_after_check(self, has_update):
        if has_update is True:
            self.btn_update.configure(
                state="normal", 
                text=f"Atualizar para {self.updater.latest_version}",
                fg_color="#2ecc71", 
                text_color="white",
                hover_color="#27ae60",
                border_width=0,
                command=self.updater.perform_update
            )
        elif has_update is False:
            self.btn_update.configure(
                state="disabled", 
                text="Sistema Atualizado", 
                fg_color="transparent",
                border_color="green",
                text_color="green"
            )
        else:
            # Caso de erro (has_update pode ser None se o callback falhar ou retornar erro)
            self.btn_update.configure(
                state="normal", 
                text="Falha na verificação", 
                fg_color="transparent",
                border_color="#e74c3c",
                text_color="#e74c3c",
                command=self.check_updates
            )
