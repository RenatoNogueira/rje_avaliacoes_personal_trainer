import customtkinter as ctk
import webbrowser
from utils.updater import Updater

class AboutDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        
        self.title("Sobre")
        self.geometry("420x520")
        self.resizable(False, False)
        
        # Configuração da Janela Modal
        self.transient(master)
        self.grab_set()
        self.focus_force()
        
        # Container Principal (Card)
        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color=("white", "#2b2b2b"))
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Logo Area (Topo)
        self.logo_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.logo_frame.pack(pady=(30, 10))
        
        # Círculo de fundo para o ícone
        logo_bg = ctk.CTkFrame(self.logo_frame, width=100, height=100, corner_radius=50, fg_color=("gray90", "gray20"))
        logo_bg.pack()
        logo_bg.pack_propagate(False) # Mantém tamanho fixo
        
        # Usando pack com expand=True para centralizar melhor o emoji que pode ter bounding box instável
        ctk.CTkLabel(logo_bg, text="🏋️", font=ctk.CTkFont(size=48)).pack(expand=True, fill="both")
        
        # Info do Sistema
        ctk.CTkLabel(
            self.main_frame, 
            text="RJE Avaliações", 
            font=ctk.CTkFont(family="Roboto", size=24, weight="bold")
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            self.main_frame, 
            text=f"Versão {Updater(self).current_version}", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=(0, 5))

        # Botão de Atualização
        self.btn_update = ctk.CTkButton(
            self.main_frame,
            text="Verificar Atualizações",
            command=self.check_updates,
            height=28,
            width=160,
            fg_color="transparent",
            border_width=1,
            border_color="gray",
            text_color=("gray10", "gray90"),
            hover_color=("gray90", "gray30")
        )
        self.btn_update.pack(pady=(0, 15))

        # Descrição com borda ou fundo sutil
        self.desc_frame = ctk.CTkFrame(self.main_frame, fg_color=("gray95", "#1f1f1f"), corner_radius=10)
        self.desc_frame.pack(padx=30, pady=(0, 20), fill="x")
        
        ctk.CTkLabel(
            self.desc_frame, 
            text="Sistema completo para gestão de\nPersonal Trainers. Controle de alunos,\navaliações físicas, treinos e agenda.", 
            font=ctk.CTkFont(size=13),
            justify="center",
            text_color=("gray30", "gray80")
        ).pack(padx=10, pady=15)

        # Links / Contato
        self.contact_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.contact_frame.pack(pady=(0, 20))
        
        ctk.CTkLabel(self.contact_frame, text="Desenvolvido por:", font=ctk.CTkFont(size=11, weight="bold")).pack()
        
        link_label = ctk.CTkLabel(
            self.contact_frame, 
            text="RJE Tecnologia", 
            font=ctk.CTkFont(size=12, underline=True),
            text_color=("#3498db", "#5dade2"),
            cursor="hand2"
        )
        link_label.pack()
        # link_label.bind("<Button-1>", lambda e: webbrowser.open("https://www.google.com")) 
        
        # Footer (Copyright)
        ctk.CTkLabel(
            self.main_frame, 
            text="© 2026 Todos os direitos reservados.", 
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(side="bottom", pady=(0, 20))
        
        # Botão Fechar discreto
        ctk.CTkButton(
            self.main_frame,
            text="Fechar",
            width=100,
            height=30,
            fg_color="transparent",
            border_width=1,
            border_color=("gray70", "gray40"),
            text_color=("gray10", "gray90"),
            hover_color=("gray90", "gray30"),
            command=self.destroy
        ).pack(side="bottom", pady=(0, 15))

    def check_updates(self):
        self.btn_update.configure(state="disabled", text="Verificando...")
        self.updater = Updater(self)
        self.updater.check_for_updates_async(self.on_update_checked)

    def on_update_checked(self, has_update):
        # Callback executado na thread, precisa agendar na UI thread se ctk não for thread-safe (geralmente tkinter requer after)
        # Mas ctk muitas vezes lida ok, vamos usar after para garantir
        self.after(0, lambda: self._update_ui_after_check(has_update))

    def _update_ui_after_check(self, has_update):
        if has_update:
            self.btn_update.configure(
                state="normal", 
                text=f"Atualizar para {self.updater.latest_version}",
                fg_color="#2ecc71", 
                text_color="white",
                hover_color="#27ae60",
                border_width=0,
                command=self.updater.perform_update
            )
        else:
            self.btn_update.configure(
                state="disabled", 
                text="Sistema Atualizado", 
                fg_color="transparent",
                border_color="green",
                text_color="green"
            )
