import json
from pathlib import Path

import customtkinter as ctk

import app_paths
from utils.app_support import auto_backup, install_exception_hooks, log

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
        install_exception_hooks(self)

        # Tamanho mínimo evita que os painéis se sobreponham em telas pequenas
        self.minsize(1024, 640)
        self.geometry("1280x760")
        self._maximize()

        self._init_settings()
        ctk.set_appearance_mode(self.appearance_mode_var.get())
        ctk.set_default_color_theme(self.color_theme_var.get())

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_user: dict | None = None

        self._create_sidebar()
        self._create_content_area()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._bind_shortcuts()

        self.after(0, self._open_login_dialog)
        
        # Verificar atualizações silenciosamente
        self.updater = Updater(self)
        self.updater.check_for_updates_async(self._on_auto_check_update)

    def _maximize(self) -> None:
        try:
            self.state("zoomed")
        except Exception:
            try:
                self.attributes("-zoomed", True)
            except Exception:
                pass

    def _on_auto_check_update(self, has_update, error_msg=None) -> None:
        if has_update:
            self.after(0, self._show_update_alert)

    def _show_update_alert(self) -> None:
        self.btn_update_avail.grid(row=0, column=1, sticky="e", padx=5)
        self._blink_count = 0
        self._blink_update_button()

    def _blink_update_button(self) -> None:
        if not hasattr(self, "btn_update_avail") or not self.btn_update_avail.winfo_exists():
            return
        # Pisca por ~15s e depois fica fixo (piscar indefinidamente distrai o uso)
        self._blink_count = getattr(self, "_blink_count", 0) + 1
        if self._blink_count > 25:
            self.btn_update_avail.configure(fg_color="#f39c12")
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

    def _sidebar_buttons(self):
        return [
            (self.btn_dashboard, "dashboard"),
            (self.btn_alunos, "alunos"),
            (self.btn_agenda, "agenda"),
            (self.btn_avaliacoes, "avaliacoes"),
            (self.btn_treinos, "treinos"),
            (self.btn_settings, "settings"),
            (self.btn_profissional, "profissional"),
            (self.btn_about, "about"),
            (self.btn_sair, "sair"),
        ]

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
            
            for btn, key in self._sidebar_buttons():
                self._update_btn_style(btn, self.btn_map[key]["icon"], "center", self.btn_map[key]["tip"])
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
            
            for btn, key in self._sidebar_buttons():
                self._update_btn_style(btn, self.btn_map[key]["full"], "w")

    def _update_btn_style(self, btn, text, anchor="center", tip_text=None):
        if anchor == "center":
            # Modo Colapsado: Ícone grande centralizado
            btn.configure(text=text, anchor="center", font=ctk.CTkFont(size=24), width=0)
            btn.grid_configure(padx=0)
        else:
            # Modo Expandido: Texto normal alinhado à esquerda
            btn.configure(text=text, anchor="w", font=ctk.CTkFont(size=13), width=140)
            btn.grid_configure(padx=10)

        # Tooltips: criadas uma única vez por botão e apenas habilitadas/desabilitadas.
        # (Antes uma nova tooltip era criada a cada recolhimento, acumulando binds.)
        btn_id = str(btn)
        tip = self.tooltips.get(btn_id)
        if tip is None and tip_text:
            tip = create_tooltip(btn, tip_text)
            self.tooltips[btn_id] = tip
        if tip is not None:
            try:
                tip.hidetip()
            except Exception:
                pass
            tip.text = tip_text or ""
            tip.enabled = bool(tip_text)

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
        self._settings_path = app_paths.SETTINGS_PATH
        
        # Define caminho da logo padrão se não houver nas configurações
        default_logo = app_paths.default_logo_path()

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
            "last_username": "",
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
        
        # Garante que use a logo padrão se a config estiver vazia/inexistente
        resolved = app_paths.resolve_data_path(defaults["logo_path"]) if defaults["logo_path"] else None
        self.logo_path = str(resolved) if resolved and Path(resolved).exists() else default_logo
        
        self._logo_image = None
        self.appearance_mode_var = ctk.StringVar(value=defaults["appearance_mode"])
        self.color_theme_var = ctk.StringVar(value=defaults["color_theme"])
        self.dashboard_refresh_seconds_var = ctk.StringVar(
            value=str(defaults.get("dashboard_refresh_seconds", 60))
        )
        self.last_username = str(defaults.get("last_username") or "")
        self._apply_branding_to_sidebar()

    def _refresh_seconds(self) -> int:
        try:
            return max(0, int(str(self.dashboard_refresh_seconds_var.get()).strip() or 60))
        except (TypeError, ValueError):
            return 60

    def _save_settings(self, notify: bool = False) -> None:
        data = {
            "professor_nome": self.professor_nome_var.get().strip(),
            "appearance_mode": self.appearance_mode_var.get(),
            "color_theme": self.color_theme_var.get(),
            "marca_nome": self.marca_nome_var.get().strip(),
            "logo_path": app_paths.to_storage_path(self.logo_path) or "",
            "contato_email": self.email_var.get().strip(),
            "contato_telefone": self.telefone_var.get().strip(),
            "contato_cref": self.cref_var.get().strip(),
            "cidade": self.cidade_var.get().strip(),
            "accent_color": self.accent_color_var.get().strip(),
            "dashboard_refresh_seconds": self._refresh_seconds(),
            "last_username": getattr(self, "last_username", ""),
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
            if notify:
                from .utils import show_toast
                show_toast(self, "Preferências salvas", 2000, kind="success")
        except Exception as e:
            log.error("Erro ao salvar configurações: %s", e)
            if notify:
                from tkinter import messagebox
                messagebox.showerror("Configurações", f"Não foi possível salvar as preferências.\n\n{e}")

    def logout(self, save_settings: bool = True) -> None:
        if save_settings:
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

    # ─────────────────────────── Atalhos de teclado ──────────────────────────
    def _bind_shortcuts(self) -> None:
        """
        Atalhos globais (somente na janela principal, não em diálogos):
          Ctrl+1..7  navegação entre módulos
          Ctrl+S     salvar            Ctrl+N  novo registro
          Ctrl+P     gerar PDF         Ctrl+F  focar a busca
          F5         atualizar lista   Ctrl+B  recolher/expandir menu
          F1         lista de atalhos
        """
        nav = {
            "1": self.show_dashboard, "2": self.show_alunos, "3": self.show_agenda,
            "4": self.show_avaliacoes, "5": self.show_treinos, "6": self.show_settings,
            "7": self.show_profissional,
        }
        for key, fn in nav.items():
            self.bind_all(f"<Control-Key-{key}>", lambda e, f=fn: self._guard(e, f))

        actions = {
            "<Control-s>": "save", "<Control-S>": "save",
            "<Control-n>": "new", "<Control-N>": "new",
            "<Control-p>": "pdf", "<Control-P>": "pdf",
            "<Control-f>": "search", "<Control-F>": "search",
            "<F5>": "refresh",
        }
        for seq, action in actions.items():
            self.bind_all(seq, lambda e, a=action: self._guard(e, lambda: self._dispatch_action(a)))
        self.bind_all("<Control-b>", lambda e: self._guard(e, self.toggle_sidebar))
        self.bind_all("<F1>", lambda e: self._guard(e, self._show_shortcuts_help))

    def _guard(self, event, fn):
        """Executa o atalho apenas se o foco estiver na janela principal e logado."""
        try:
            if self.current_user is None or self.state() == "withdrawn":
                return None
            if event is not None and event.widget.winfo_toplevel() is not self:
                return None
        except Exception:
            return None
        fn()
        return "break"

    _ACTION_METHODS = {
        "save": ("on_salvar", "on_salvar_treino"),
        "new": ("on_novo", "on_novo_treino"),
        "pdf": ("on_gerar_pdf",),
        "refresh": ("refresh_data", "load_alunos_list", "load_agendamentos", "load_avaliacoes", "load_treinos"),
    }
    _SEARCH_FIELDS = ("entry_filtro_nome", "entry_filtro_aluno", "entry_filtro_tel")

    def _dispatch_action(self, action: str) -> None:
        view = self.current_view
        if view is None:
            return
        if action == "search":
            for attr in self._SEARCH_FIELDS:
                w = getattr(view, attr, None)
                if w is not None:
                    try:
                        w.focus_set()
                        w.select_range(0, "end")
                    except Exception:
                        pass
                    return
            return
        for name in self._ACTION_METHODS.get(action, ()):
            fn = getattr(view, name, None)
            if callable(fn):
                fn()
                return

    def _show_shortcuts_help(self) -> None:
        from tkinter import messagebox
        messagebox.showinfo(
            "Atalhos de teclado",
            "Navegação\n"
            "  Ctrl+1  Dashboard        Ctrl+2  Alunos\n"
            "  Ctrl+3  Agenda           Ctrl+4  Avaliações\n"
            "  Ctrl+5  Treinos          Ctrl+6  Configurações\n"
            "  Ctrl+7  Profissional     Ctrl+B  Recolher menu\n\n"
            "Ações na tela atual\n"
            "  Ctrl+N  Novo registro    Ctrl+S  Salvar\n"
            "  Ctrl+P  Gerar PDF        Ctrl+F  Buscar\n"
            "  F5      Atualizar        Esc     Limpar busca\n\n"
            "Campos de data\n"
            "  Duplo clique ou F4 abre o calendário\n"
            "  Enter avança para o próximo campo",
            parent=self,
        )

    def _show_view(self, view_class, **kwargs) -> None:
        if self.current_view is not None:
            self.current_view.destroy()
        self.configure(cursor="watch")
        self.update_idletasks()
        try:
            self.current_view = view_class(self.content, **kwargs)
            self.current_view.grid(row=0, column=0, sticky="nsew")
        finally:
            self.configure(cursor="")
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
            get_refresh_seconds=self._refresh_seconds,
            cidade_var=self.cidade_var,
            navigate=self.navigate,
        )

    def navigate(self, target: str) -> None:
        """Navegação programática (ex.: clicar em um card do dashboard)."""
        routes = {
            "dashboard": self.show_dashboard,
            "alunos": self.show_alunos,
            "agenda": self.show_agenda,
            "avaliacoes": self.show_avaliacoes,
            "treinos": self.show_treinos,
            "settings": self.show_settings,
            "profissional": self.show_profissional,
        }
        fn = routes.get(target)
        if fn:
            fn()

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
            self.last_username = user_data.get("username") or ""
            
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
            self._update_user_badge()
            self._save_settings()
            
            # Mostra a janela principal
            self.deiconify()
            self._maximize()  # Garante maximizado
            self.lift()
            
            self.show_dashboard()

            # Backup automático diário (silencioso) e alerta de senha padrão
            self.after(1500, lambda: auto_backup(db))
            self.after(800, self._warn_default_password)

        def on_cancel():
            # Se cancelar no login e não tiver usuário logado, fecha o app
            if not self.current_user:
                self.destroy()
            else:
                # Se já estava logado (improvável nesse fluxo), apenas fecha o dialog
                pass

        self._login_window = LoginDialog(self, on_login_success, on_cancel,
                                         last_username=getattr(self, "last_username", ""))
        
        # Tenta aplicar ícone
        set_window_icon(self._login_window, getattr(self, "logo_path", None))

    def _update_user_badge(self) -> None:
        """Mostra quem está logado no cabeçalho do menu lateral."""
        if not self.current_user:
            self.subtitle_label.configure(text="Personal Trainer")
            return
        nome = self.current_user.get("nome") or self.current_user.get("username") or ""
        papel = "Administrador" if self.current_user.get("is_admin") else "Personal Trainer"
        self.subtitle_label.configure(text=f"👤 {nome} · {papel}")
        try:
            create_tooltip(self.subtitle_label, "Usuário conectado. F1 mostra os atalhos de teclado.")
        except Exception:
            pass

    def _warn_default_password(self) -> None:
        try:
            if not self.current_user:
                return
            if db.is_default_admin_password(int(self.current_user["id"])):
                from tkinter import messagebox
                if messagebox.askyesno(
                    "Segurança",
                    "Você está usando a senha padrão do administrador (admin).\n\n"
                    "Recomendamos alterá-la agora para proteger os dados dos seus alunos.\n\n"
                    "Abrir a tela para alterar a senha?",
                    parent=self,
                ):
                    self.show_settings()
        except Exception as exc:
            log.warning("Falha ao verificar senha padrão: %s", exc)

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
