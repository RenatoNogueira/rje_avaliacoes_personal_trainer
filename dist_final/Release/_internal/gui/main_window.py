import json
from pathlib import Path

import customtkinter as ctk

from database import db  # noqa: F401
from .dashboard_view import DashboardView
from .alunos_view import AlunosView
from .agenda_view import AgendaView
from .avaliacoes_view import AvaliacoesView
from .treinos_view import TreinosView
from .settings_view import SettingsView
from .login_dialog import LoginDialog
from .about_dialog import AboutDialog
from .theme import _c, font_body, font_subtitle, font_title, create_view_header, set_accent_color
from .utils import create_tooltip, set_window_icon
from utils.updater import Updater


class Application(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.withdraw()

        self.title("RJE Avaliações - Personal Trainer")
        set_window_icon(self)
        
        # Maximizar janela ao iniciar
        try:
            self.state("zoomed")
        except:
            self.geometry("1100x650")

        self._init_settings()
        ctk.set_appearance_mode(self.appearance_mode_var.get())
        ctk.set_default_color_theme(self.color_theme_var.get())

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_user: dict | None = None

        self._create_sidebar()
        self._create_content_area()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.after(0, self._open_login_dialog)
        
        # Verificar atualizações silenciosamente
        self.updater = Updater(self)
        self.updater.check_for_updates_async(self._on_auto_check_update)

    def _on_auto_check_update(self, has_update: bool) -> None:
        if has_update:
            self.after(0, self._show_update_alert)

    def _show_update_alert(self) -> None:
        self.btn_update_avail.grid(row=0, column=1, sticky="e", padx=5)
        self._blink_update_button()

    def _blink_update_button(self) -> None:
        if not hasattr(self, "btn_update_avail") or not self.btn_update_avail.winfo_exists():
            return
            
        if self.update_blink_state:
            self.btn_update_avail.configure(fg_color="#f39c12")
        else:
            self.btn_update_avail.configure(fg_color="#e67e22") # Um tom um pouco diferente ou transparente
            # Se preferir que suma e apareça (mais chamativo):
            # self.btn_update_avail.configure(text_color="white" if self.update_blink_state else "#f39c12")
            
        self.update_blink_state = not self.update_blink_state
        self.after(600, self._blink_update_button)

    def _on_update_click(self) -> None:
        from tkinter import messagebox
        if messagebox.askyesno("Atualização Disponível", f"Nova versão {self.updater.latest_version} disponível.\nDeseja atualizar agora?"):
            self.updater.perform_update()

    def _create_sidebar(self) -> None:
        self.sidebar_expanded = True
        self.sidebar_width = 220
        self.sidebar_collapsed_width = 60

        self.sidebar = ctk.CTkFrame(self, width=self.sidebar_width, corner_radius=0, fg_color=_c("panel_bg"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)
        self.sidebar.grid_propagate(False) # Mantém largura fixa

        # Header Frame
        self.header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=10, pady=(20, 10), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        # Botão Menu (Hambúrguer)
        self.btn_menu = ctk.CTkButton(
            self.header_frame,
            text="☰",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            text_color=("gray10", "gray90"),
            command=self.toggle_sidebar
        )
        self.btn_menu.grid(row=0, column=0, sticky="w")

        # Botão Update (Oculto inicialmente, agora como texto de alerta)
        self.btn_update_avail = ctk.CTkButton(
            self.header_frame,
            text="▲ Atualizar",
            width=80,
            height=28,
            fg_color="#f39c12",
            hover_color="#d35400",
            text_color="white",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_update_click,
            corner_radius=6
        )
        self.update_blink_state = True
        # Grid será feito no callback se houver update
        create_tooltip(self.btn_update_avail, "Nova atualização disponível!")

        # Logo Label (Ocultar ao colapsar)
        self.logo_label = ctk.CTkLabel(self.header_frame, text="")
        self.logo_label.grid(row=1, column=0, columnspan=2, pady=(10, 6), sticky="w")

        # Title Labels (Ocultar ao colapsar)
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="RJE Avaliações",
            font=font_title(),
            text_color=_c("view_header_title")
        )
        self.title_label.grid(row=2, column=0, columnspan=2, sticky="w")

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Personal Trainer",
            font=font_body(),
            text_color=_c("view_header_subtitle"),
        )
        self.subtitle_label.grid(row=3, column=0, columnspan=2, pady=(0, 4), sticky="w")

        # Container do Menu (para garantir que os botões caibam)
        self.menu_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.menu_frame.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        self.menu_frame.grid_columnconfigure(0, weight=1)
        
        # A sidebar principal precisa expandir a linha do menu_frame
        self.sidebar.grid_rowconfigure(2, weight=1)
        # E remover o peso da linha 10 antiga (espaçador) se vamos usar o menu_frame
        self.sidebar.grid_rowconfigure(10, weight=0)


        # Seção Principal
        self.menu_label = ctk.CTkLabel(
            self.menu_frame,
            text="MENU PRINCIPAL",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray",
        )
        self.menu_label.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")

        # Botões
        # Mapeamento de texto completo para ícone apenas
        self.btn_map = {
            "dashboard": {"full": "📊  Dashboard", "icon": "📊", "tip": "Visão geral"},
            "alunos": {"full": "👥  Alunos", "icon": "👥", "tip": "Gestão de Alunos"},
            "agenda": {"full": "📅  Agenda", "icon": "📅", "tip": "Agendamentos"},
            "avaliacoes": {"full": "⚖️  Avaliações", "icon": "⚖️", "tip": "Avaliações Físicas"},
            "treinos": {"full": "💪  Treinos", "icon": "💪", "tip": "Montagem de Treinos"},
            "settings": {"full": "⚙️  Configurações", "icon": "⚙️", "tip": "Configurações do Sistema"},
            "profissional": {"full": "🆔  Profissional", "icon": "🆔", "tip": "Perfil Profissional"},
            "about": {"full": "ℹ️  Sobre", "icon": "ℹ️", "tip": "Sobre o Sistema"},
            "sair": {"full": "🚪  Sair", "icon": "🚪", "tip": "Sair do Sistema"}
        }

        self.btn_dashboard = self._create_sidebar_button(self.menu_frame, self.btn_map["dashboard"]["full"], self.show_dashboard)
        self.btn_dashboard.grid(row=1, column=0, padx=10, pady=2, sticky="ew")

        self.btn_alunos = self._create_sidebar_button(self.menu_frame, self.btn_map["alunos"]["full"], self.show_alunos)
        self.btn_alunos.grid(row=2, column=0, padx=10, pady=2, sticky="ew")

        self.btn_agenda = self._create_sidebar_button(self.menu_frame, self.btn_map["agenda"]["full"], self.show_agenda)
        self.btn_agenda.grid(row=3, column=0, padx=10, pady=2, sticky="ew")

        self.btn_avaliacoes = self._create_sidebar_button(self.menu_frame, self.btn_map["avaliacoes"]["full"], self.show_avaliacoes)
        self.btn_avaliacoes.grid(row=4, column=0, padx=10, pady=2, sticky="ew")

        self.btn_treinos = self._create_sidebar_button(self.menu_frame, self.btn_map["treinos"]["full"], self.show_treinos)
        self.btn_treinos.grid(row=5, column=0, padx=10, pady=2, sticky="ew")

        # Seção Sistema
        self.sys_label = ctk.CTkLabel(
            self.menu_frame,
            text="SISTEMA",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray",
        )
        self.sys_label.grid(row=6, column=0, padx=20, pady=(15, 5), sticky="w")

        self.btn_settings = self._create_sidebar_button(self.menu_frame, self.btn_map["settings"]["full"], self.show_settings)
        self.btn_settings.grid(row=7, column=0, padx=10, pady=2, sticky="ew")

        self.btn_profissional = self._create_sidebar_button(self.menu_frame, self.btn_map["profissional"]["full"], self.show_profissional)
        self.btn_profissional.grid(row=8, column=0, padx=10, pady=2, sticky="ew")

        self.btn_about = self._create_sidebar_button(self.menu_frame, self.btn_map["about"]["full"], self.show_about)
        self.btn_about.grid(row=9, column=0, padx=10, pady=2, sticky="ew")

        # Espaçador para empurrar Sair para baixo
        self.menu_frame.grid_rowconfigure(10, weight=1)

        self.btn_sair = ctk.CTkButton(
            self.menu_frame,
            text=self.btn_map["sair"]["full"],
            fg_color="transparent",
            text_color=_c("view_header_title"),
            hover_color=_c("btn_pdf_hover"),
            anchor="w",
            command=self.logout,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.btn_sair.grid(row=11, column=0, padx=10, pady=20, sticky="ew")
        
        # Tooltips references
        self.tooltips = {}
        
        self._apply_branding_to_sidebar()

    def toggle_sidebar(self):
        if self.sidebar_expanded:
            # Colapsar
            self.sidebar_expanded = False
            self.sidebar.configure(width=self.sidebar_collapsed_width)
            
            # Ocultar textos
            self.logo_label.grid_remove()
            self.title_label.grid_remove()
            self.subtitle_label.grid_remove()
            self.menu_label.grid_remove()
            self.sys_label.grid_remove()
            
            # Ajustar botões para ícones centralizados e adicionar tooltips
            self._update_btn_style(self.btn_dashboard, self.btn_map["dashboard"]["icon"], "center", self.btn_map["dashboard"]["tip"])
            self._update_btn_style(self.btn_alunos, self.btn_map["alunos"]["icon"], "center", self.btn_map["alunos"]["tip"])
            self._update_btn_style(self.btn_agenda, self.btn_map["agenda"]["icon"], "center", self.btn_map["agenda"]["tip"])
            self._update_btn_style(self.btn_avaliacoes, self.btn_map["avaliacoes"]["icon"], "center", self.btn_map["avaliacoes"]["tip"])
            self._update_btn_style(self.btn_treinos, self.btn_map["treinos"]["icon"], "center", self.btn_map["treinos"]["tip"])
            self._update_btn_style(self.btn_settings, self.btn_map["settings"]["icon"], "center", self.btn_map["settings"]["tip"])
            self._update_btn_style(self.btn_profissional, self.btn_map["profissional"]["icon"], "center", self.btn_map["profissional"]["tip"])
            self._update_btn_style(self.btn_about, self.btn_map["about"]["icon"], "center", self.btn_map["about"]["tip"])
            self._update_btn_style(self.btn_sair, self.btn_map["sair"]["icon"], "center", self.btn_map["sair"]["tip"])
            
        else:
            # Expandir
            self.sidebar_expanded = True
            self.sidebar.configure(width=self.sidebar_width)
            
            # Mostrar textos
            self.logo_label.grid()
            self.title_label.grid()
            self.subtitle_label.grid()
            self.menu_label.grid()
            self.sys_label.grid()
            
            # Restaurar botões e remover tooltips
            self._update_btn_style(self.btn_dashboard, self.btn_map["dashboard"]["full"], "w")
            self._update_btn_style(self.btn_alunos, self.btn_map["alunos"]["full"], "w")
            self._update_btn_style(self.btn_agenda, self.btn_map["agenda"]["full"], "w")
            self._update_btn_style(self.btn_avaliacoes, self.btn_map["avaliacoes"]["full"], "w")
            self._update_btn_style(self.btn_treinos, self.btn_map["treinos"]["full"], "w")
            self._update_btn_style(self.btn_settings, self.btn_map["settings"]["full"], "w")
            self._update_btn_style(self.btn_profissional, self.btn_map["profissional"]["full"], "w")
            self._update_btn_style(self.btn_about, self.btn_map["about"]["full"], "w")
            self._update_btn_style(self.btn_sair, self.btn_map["sair"]["full"], "w")

    def _update_btn_style(self, btn, text, anchor="center", tip_text=None):
        # Se estamos colapsando (anchor="center"), o texto é o ícone
        # Se estamos expandindo (anchor="w"), o texto é o label completo
        
        if anchor == "center":
            # Modo Colapsado: Ícone grande centralizado
            # Importante: width=0 deixa o botão encolher para caber na sidebar estreita
            btn.configure(text=text, anchor="center", font=ctk.CTkFont(size=24), width=0)
            btn.grid_configure(padx=0)
        else:
            # Modo Expandido: Texto normal alinhado à esquerda
            # width=None ou um valor fixo se preferir
            btn.configure(text=text, anchor="w", font=ctk.CTkFont(size=13), width=140)
            btn.grid_configure(padx=10)

        # Gerenciamento de Tooltips
        btn_id = str(btn)
        
        # 1. Tentar remover a tooltip antiga (se existir)
        # Como não temos acesso direto ao objeto interno da tooltip antiga para destruí-lo explicitamente via API pública,
        # e a classe ToolTip cria uma Toplevel, precisamos garantir que ela seja destruída.
        # A nossa implementação de create_tooltip retorna uma instância de ToolTip.
        
        old_tooltip = self.tooltips.get(btn_id)
        if old_tooltip:
            # Tenta esconder/destruir a janela da tooltip se estiver aberta
            try:
                old_tooltip.hidetip()
            except Exception:
                pass
            # remove a referência
            del self.tooltips[btn_id]

        # 2. Se houver novo texto de tooltip, cria uma nova
        if tip_text:
            self.tooltips[btn_id] = create_tooltip(btn, tip_text)
        else:
            # Se não houver texto (modo expandido), apenas garantimos que não há binds
            # (O unbind já foi feito acima se existia tooltip anterior)
            pass

    def _create_sidebar_button(self, parent, text: str, command) -> ctk.CTkButton:
        btn = ctk.CTkButton(
            parent,
            text=text,
            command=command,
            height=40,
            anchor="w",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            fg_color="transparent",
            text_color=_c("view_header_title"),
            hover_color=_c("card_hover"),
        )
        # Store initial colors for selection logic
        btn._original_fg = "transparent"
        btn._original_text = _c("view_header_title")
        return btn

    def _create_content_area(self) -> None:
        self.content = ctk.CTkFrame(self)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.current_view = None

    def _init_settings(self) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        data_dir = base_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        self._settings_path = data_dir / "settings.json"
        
        # Define caminho da logo padrão se não houver nas configurações
        assets_dir = base_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        default_logo = str(assets_dir / "logo_rje.png")

        defaults = {
            "professor_nome": "",
            "appearance_mode": "dark",
            "color_theme": "dark-blue",
            "marca_nome": "",
            "logo_path": default_logo,
            "contato_email": "",
            "contato_telefone": "",
            "contato_cref": "",
            "cidade": "",  # Empty triggers auto-detection
            "accent_color": "", # Empty = default theme
            "dashboard_refresh_seconds": 60,
        }
        if self._settings_path.exists():
            try:
                with self._settings_path.open("r", encoding="utf-8") as f:
                    loaded = json.load(f)
                defaults.update({k: v for k, v in loaded.items() if k in defaults})
            except Exception:
                pass

        self.professor_nome_var = ctk.StringVar(value=defaults["professor_nome"])
        self.marca_nome_var = ctk.StringVar(value=defaults["marca_nome"])
        self.email_var = ctk.StringVar(value=defaults.get("contato_email", ""))
        self.telefone_var = ctk.StringVar(value=defaults.get("contato_telefone", ""))
        self.cref_var = ctk.StringVar(value=defaults.get("contato_cref", ""))
        self.cidade_var = ctk.StringVar(value=defaults.get("cidade", ""))
        self.accent_color_var = ctk.StringVar(value=defaults.get("accent_color", ""))
        
        # Aplica a cor de destaque ao carregar
        if self.accent_color_var.get():
            set_accent_color(self.accent_color_var.get())
        
        # Garante que use a logo padrão se a config estiver vazia
        self.logo_path = str(defaults["logo_path"] or default_logo)
        
        self._logo_image = None
        self.appearance_mode_var = ctk.StringVar(value=defaults["appearance_mode"])
        self.color_theme_var = ctk.StringVar(value=defaults["color_theme"])
        self.dashboard_refresh_seconds_var = ctk.StringVar(
            value=str(defaults.get("dashboard_refresh_seconds", 60))
        )
        self._apply_branding_to_sidebar()

    def _save_settings(self) -> None:
        data = {
            "professor_nome": self.professor_nome_var.get().strip(),
            "appearance_mode": self.appearance_mode_var.get(),
            "color_theme": self.color_theme_var.get(),
            "marca_nome": self.marca_nome_var.get().strip(),
            "logo_path": self.logo_path,
            "contato_email": self.email_var.get().strip(),
            "contato_telefone": self.telefone_var.get().strip(),
            "contato_cref": self.cref_var.get().strip(),
            "cidade": self.cidade_var.get().strip(),
            "accent_color": self.accent_color_var.get().strip(),
            "dashboard_refresh_seconds": int(self.dashboard_refresh_seconds_var.get() or 60),
        }
        try:
            with self._settings_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Também salva no banco de dados para o usuário atual, se logado
            if self.current_user and "id" in self.current_user:
                db.execute(
                    "UPDATE usuarios SET cidade = ? WHERE id = ?",
                    (data["cidade"], int(self.current_user["id"])),
                    commit=True
                )
                # Atualiza objeto em memória
                self.current_user["cidade"] = data["cidade"]
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")

    def logout(self) -> None:
        self._save_settings()
        # Fecha a view atual
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None
            
        # Oculta a janela principal
        self.withdraw()
        
        # Limpa dados do usuário
        self.current_user = None
        
        # Abre o login novamente
        self.after(100, self._open_login_dialog)

    def _on_close(self) -> None:
        self._save_settings()
        self.destroy()

    def _show_view(self, view_class, **kwargs) -> None:
        if self.current_view is not None:
            self.current_view.destroy()
        self.current_view = view_class(self.content, **kwargs)
        self.current_view.grid(row=0, column=0, sticky="nsew")
        self._update_sidebar_selection(view_class)

    def _update_sidebar_selection(self, active_view_class) -> None:
        # Reset all buttons
        buttons = [
            (self.btn_dashboard, DashboardView),
            (self.btn_alunos, AlunosView),
            (self.btn_agenda, AgendaView),
            (self.btn_avaliacoes, AvaliacoesView),
            (self.btn_treinos, TreinosView),
            (self.btn_settings, SettingsView),
            (self.btn_profissional, None), # Handled separately below if needed
        ]
        
        # Mapping class to button
        class_map = {
            DashboardView: self.btn_dashboard,
            AlunosView: self.btn_alunos,
            AgendaView: self.btn_agenda,
            AvaliacoesView: self.btn_avaliacoes,
            TreinosView: self.btn_treinos,
            SettingsView: self.btn_settings,
        }
        
        # Import ProfissionalView here to avoid circular
        from .profissional_view import ProfissionalView
        class_map[ProfissionalView] = self.btn_profissional

        for cls, btn in class_map.items():
            if cls == active_view_class:
                btn.configure(
                    fg_color=_c("card_agenda_accent"), 
                    text_color="white",
                    hover_color=_c("btn_save_hover")
                )
            else:
                btn.configure(
                    fg_color="transparent", 
                    text_color=_c("view_header_title"),
                    hover_color=_c("card_hover")
                )

    def show_dashboard(self) -> None:
        self._show_view(
            DashboardView,
            get_refresh_seconds=lambda: max(
                0, int(self.dashboard_refresh_seconds_var.get() or 60)
            ),
            cidade_var=self.cidade_var,
        )

    def show_alunos(self) -> None:
        self._show_view(AlunosView)

    def show_agenda(self) -> None:
        self._show_view(AgendaView, get_current_user=lambda: self.current_user)

    def show_avaliacoes(self) -> None:
        self._show_view(
            AvaliacoesView,
            professor_var=self.professor_nome_var,
            cref_var=self.cref_var,
            get_current_user=lambda: self.current_user,
        )

    def show_treinos(self) -> None:
        self._show_view(
            TreinosView,
            professor_var=self.professor_nome_var,
            cref_var=self.cref_var,
            get_current_user=lambda: self.current_user,
        )

    def show_settings(self) -> None:
        self._show_view(
            SettingsView,
            professor_var=self.professor_nome_var,
            appearance_var=self.appearance_mode_var,
            color_theme_var=self.color_theme_var,
            refresh_var=self.dashboard_refresh_seconds_var,
            cidade_var=self.cidade_var,
            accent_color_var=self.accent_color_var,
            current_user=self.current_user,
        )

    def show_profissional(self) -> None:
        from .profissional_view import ProfissionalView
        self._show_view(
            ProfissionalView,
            professor_var=self.professor_nome_var,
            marca_var=self.marca_nome_var,
            email_var=self.email_var,
            telefone_var=self.telefone_var,
            cref_var=self.cref_var,
            get_logo_path=lambda: self.logo_path,
            set_branding=self._set_branding,
            current_user=self.current_user,
            on_update_profile=self._update_user_profile,
            cidade_var=self.cidade_var,
            accent_color_var=self.accent_color_var
        )

    def _update_user_profile(self, user_id: int, foto_path: str, telefone: str, cref: str) -> None:
        try:
            db.execute(
                "UPDATE usuarios SET foto_perfil = ?, telefone = ?, cref = ?, cidade = ? WHERE id = ?",
                (foto_path, telefone, cref, self.cidade_var.get(), user_id),
                commit=True
            )
            # Atualiza objeto current_user em memória
            if self.current_user and int(self.current_user["id"]) == user_id:
                self.current_user = dict(self.current_user) # copia
                self.current_user["foto_perfil"] = foto_path
                self.current_user["telefone"] = telefone
                self.current_user["cref"] = cref
                self.current_user["cidade"] = self.cidade_var.get()
        except Exception as e:
            print(f"Erro ao atualizar perfil: {e}")

    def show_about(self) -> None:
        AboutDialog(self)

    def _apply_branding_to_sidebar(self) -> None:
        # Removido a exibição da logo na sidebar conforme solicitado
        if hasattr(self, "logo_label"):
            self.logo_label.configure(image=None)
            self.logo_label.configure(text="")
            self._logo_image = None
        
        # Define o ícone da janela (Title Bar) usando a logo configurada
        set_window_icon(self, self.logo_path)
        
        # Tenta aplicar para todas as janelas filhas existentes (modais)
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkToplevel):
                set_window_icon(widget, self.logo_path)

    def _get_current_user_id(self) -> int | None:
        if not self.current_user:
            return None
        try:
            return int(self.current_user.get("id"))
        except Exception:
            return None

    def _open_login_dialog(self) -> None:
        if hasattr(self, "_login_window") and self._login_window is not None:
            try:
                # Se já existe, apenas traz pra frente
                self._login_window.lift()
                self._login_window.focus_force()
                return
            except Exception:
                self._login_window = None

        def on_login_success(user_data):
            self.current_user = user_data
            self._login_window = None
            
            # Recarrega configurações se necessário
            self._init_settings()
            
            # Sincroniza o nome do professor se ainda não estiver preenchido
            if not self.professor_nome_var.get().strip():
                nome_prof = user_data.get("nome") or user_data.get("username") or ""
                self.professor_nome_var.set(nome_prof)
            
            # Sincroniza CREF se ainda não estiver preenchido
            if not self.cref_var.get().strip():
                cref_user = user_data.get("cref") or ""
                self.cref_var.set(cref_user)
            
            # Sincroniza cidade do usuário (preferência individual)
            cidade_user = user_data.get("cidade") or ""
            if cidade_user:
                self.cidade_var.set(cidade_user)
            elif not self.cidade_var.get().strip():
                # Se ambos vazios, deixamos vazio para auto-detecção
                pass

            self._apply_branding_to_sidebar()
            
            # Mostra a janela principal
            self.deiconify()
            self.state("zoomed") # Garante maximizado
            self.lift()
            
            # Reconstrói a sidebar para atualizar permissões (ex: botão settings) se necessário
            # Mas como a sidebar é fixa, talvez só precise atualizar o conteúdo da dashboard
            self.show_dashboard()

        def on_cancel():
            # Se cancelar no login e não tiver usuário logado, fecha o app
            if not self.current_user:
                self.destroy()
            else:
                # Se já estava logado (improvável nesse fluxo), apenas fecha o dialog
                pass

        self._login_window = LoginDialog(self, on_login_success, on_cancel)
        
        # Tenta aplicar ícone
        set_window_icon(self._login_window, getattr(self, "logo_path", None))

    def _set_branding(self, logo_path: str, marca: str, email: str, telefone: str, cref: str, accent_color: str = None) -> None:
        self.logo_path = logo_path or ""
        self.marca_nome_var.set(marca or "")
        self.email_var.set(email or "")
        self.telefone_var.set(telefone or "")
        self.cref_var.set(cref or "")
        if accent_color is not None:
            self.accent_color_var.set(accent_color)
            set_accent_color(accent_color)
        self.cidade_var.set(self.cidade_var.get()) # Keeps current city if not passed
        self._apply_branding_to_sidebar()
        self._save_settings()
