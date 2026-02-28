import datetime
import customtkinter as ctk
import requests
import threading
from database import db
from utils.geo_utils import get_current_city


# ────────────────────────────── Paleta de cores ──────────────────────────────
# Cada tuple = (light_mode, dark_mode)

COLORS = {
    # Cards de resumo
    "card_alunos_bg":       ("#e3f2fd", "#1a2740"),
    "card_alunos_accent":   ("#42a5f5", "#5c9ce6"),
    "card_agenda_bg":       ("#e8f5e9", "#1a3324"),
    "card_agenda_accent":   ("#66bb6a", "#5dba62"),
    "card_aval_bg":         ("#fff3e0", "#3a2a14"),
    "card_aval_accent":     ("#ffa726", "#e6952e"),
    "card_treinos_bg":      ("#f3e5f5", "#2d1a38"),
    "card_treinos_accent":  ("#ab47bc", "#b35cc5"),

    # Cards hover
    "card_alunos_hover":    ("#bbdefb", "#233654"),
    "card_agenda_hover":    ("#c8e6c9", "#244936"),
    "card_aval_hover":      ("#ffe0b2", "#4d3a20"),
    "card_treinos_hover":   ("#e1bee7", "#3f264d"),

    # Status badges
    "status_pendente":      ("#ff9800", "#ff9800"),
    "status_concluido":     ("#4caf50", "#4caf50"),
    "status_cancelado":     ("#f44336", "#f44336"),

    # Agendamento cards
    "ag_card_bg":           ("gray92", "gray18"),
    "ag_card_hover":        ("gray86", "gray25"),
    "ag_today_bg":          ("#e0f2f1", "#1b3332"),
    "ag_today_hover":       ("#b2dfdb", "#254a48"),
    "ag_date_box":          ("gray82", "gray28"),

    # Aniversariantes
    "bday_card_bg":         ("gray94", "gray22"),
    "bday_card_hover":      ("white", "gray30"),
    "bday_today_bg":        ("#fff9c4", "#3a3520"),
    "bday_today_hover":     ("#fff59d", "#4d4a2b"),

    # Seções
    "section_title":        ("gray40", "gray60"),
    "subtitle_text":        ("gray50", "gray55"),

    # Empty state
    "empty_icon":           ("gray75", "gray40"),
    "empty_text":           ("gray55", "gray50"),
}


def _c(key: str) -> tuple:
    """Retorna a tupla de cor (light, dark)."""
    return COLORS[key]


# ──────────────────────────── Nomes PT-BR manuais ────────────────────────────
_DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira",
                "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
_DIA_CURTO = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
_MESES = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
          "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


def _data_extenso(d: datetime.date) -> str:
    return f"{_DIAS_SEMANA[d.weekday()]}, {d.day} de {_MESES[d.month]} de {d.year}"


def _saudacao() -> tuple[str, str]:
    """Retorna (saudação, emoji) baseado na hora do dia."""
    h = datetime.datetime.now().hour
    if h < 12:
        return "Bom dia", "☀️"
    elif h < 18:
        return "Boa tarde", "🌤️"
    else:
        return "Boa noite", "🌙"


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, get_refresh_seconds=None, cidade_var=None) -> None:
        super().__init__(master)
        self.get_refresh_seconds = get_refresh_seconds or (lambda: 60)
        self.cidade_var = cidade_var
        self.weather_data = None
        self.api_key = "05ccf28850c068aa559dc33c5f4cac4e"
        
        # Variáveis para animação
        self.weather_pulse_val = 24
        self.weather_pulse_dir = 1
        self._animate_weather()

        # Layout Principal
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_summary_cards()
        self._build_main_content()

        # Inicializa dados
        self.refresh_data()
        self._start_timer()

    # ═══════════════════════════ HEADER ════════════════════════════════════
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=28, pady=(28, 6), sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        
        # Coluna do meio: Previsão do Tempo
        self.weather_frame = ctk.CTkFrame(header, fg_color="transparent")
        self.weather_frame.grid(row=0, column=1, sticky="w", padx=(40, 0))
        
        self.weather_icon_lbl = ctk.CTkLabel(
            self.weather_frame, text="", font=ctk.CTkFont(size=24)
        )
        self.weather_icon_lbl.pack(side="left", padx=(0, 5))
        
        self.weather_temp_lbl = ctk.CTkLabel(
            self.weather_frame, text="Carregando clima...", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.weather_temp_lbl.pack(side="left")
        
        self.weather_desc_lbl = ctk.CTkLabel(
            self.weather_frame, text="", font=ctk.CTkFont(size=12), text_color=_c("subtitle_text")
        )
        self.weather_desc_lbl.pack(side="left", padx=(8, 0))

        # Coluna esquerda: saudação + data
        info = ctk.CTkFrame(header, fg_color="transparent")
        info.grid(row=0, column=0, sticky="w")

        saudacao, emoji = _saudacao()
        self.greeting_label = ctk.CTkLabel(
            info,
            text=f"{emoji}  {saudacao}!",
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        self.greeting_label.pack(anchor="w")

        self.date_label = ctk.CTkLabel(
            info,
            text=_data_extenso(datetime.date.today()),
            font=ctk.CTkFont(size=13),
            text_color=_c("subtitle_text"),
        )
        self.date_label.pack(anchor="w", pady=(2, 0))

        # Coluna direita: botão atualizar estilizado
        btn_refresh = ctk.CTkButton(
            header,
            text="⟳  Atualizar",
            width=120,
            height=36,
            corner_radius=18,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.refresh_data,
        )
        btn_refresh.grid(row=0, column=2, sticky="ne", pady=6)

    # ═══════════════════════════ SUMMARY CARDS ════════════════════════════
    def _build_summary_cards(self):
        # Separador sutil
        sep = ctk.CTkFrame(self, height=1, fg_color=("gray85", "gray30"))
        sep.grid(row=1, column=0, padx=28, pady=(14, 10), sticky="ew")

        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.grid(row=2, column=0, padx=28, pady=0, sticky="ew")
        self.cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="cards")

        # Card 1 - Alunos
        self.card_alunos, self.lbl_alunos, self.lbl_alunos_sub = self._make_summary_card(
            self.cards_frame, col=0,
            icon="👥", title="Total de Alunos", value="0", subtitle="cadastrados",
            bg=_c("card_alunos_bg"), accent=_c("card_alunos_accent"),
            hover=_c("card_alunos_hover"),
        )

        # Card 2 - Agendamentos Hoje
        self.card_agenda, self.lbl_agendamentos, self.lbl_agenda_sub = self._make_summary_card(
            self.cards_frame, col=1,
            icon="📅", title="Agendamentos Hoje", value="0", subtitle="programados",
            bg=_c("card_agenda_bg"), accent=_c("card_agenda_accent"),
            hover=_c("card_agenda_hover"),
        )

        # Card 3 - Avaliações do Mês
        self.card_aval, self.lbl_avaliacoes, self.lbl_aval_sub = self._make_summary_card(
            self.cards_frame, col=2,
            icon="⚖️", title="Avaliações no Mês", value="0", subtitle="realizadas",
            bg=_c("card_aval_bg"), accent=_c("card_aval_accent"),
            hover=_c("card_aval_hover"),
        )

        # Card 4 - Treinos
        self.card_treinos, self.lbl_treinos, self.lbl_treinos_sub = self._make_summary_card(
            self.cards_frame, col=3,
            icon="💪", title="Treinos Cadastrados", value="0", subtitle="ativos",
            bg=_c("card_treinos_bg"), accent=_c("card_treinos_accent"),
            hover=_c("card_treinos_hover"),
        )

    def _make_summary_card(self, parent, col, icon, title, value, subtitle,
                           bg, accent, hover):
        """Cria um card de resumo moderno com accent bar e hover."""
        padx_left = (0, 6) if col == 0 else (6, 6)
        padx_right = (6, 0) if col == 3 else padx_left

        card = ctk.CTkFrame(parent, fg_color=bg, corner_radius=14)
        card.grid(row=0, column=col, padx=padx_right if col == 3 else padx_left,
                  pady=4, sticky="nsew")

        # Accent bar no topo
        accent_bar = ctk.CTkFrame(card, height=4, fg_color=accent, corner_radius=2)
        accent_bar.pack(fill="x", padx=16, pady=(8, 0))

        # Conteúdo
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=(6, 12))

        # Linha do ícone + valor
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x")

        lbl_icon = ctk.CTkLabel(top_row, text=icon, font=ctk.CTkFont(size=30))
        lbl_icon.pack(side="left")

        lbl_value = ctk.CTkLabel(
            top_row, text=value,
            font=ctk.CTkFont(size=32, weight="bold"),
        )
        lbl_value.pack(side="right")

        # Título
        lbl_title = ctk.CTkLabel(
            content, text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=_c("section_title"),
        )
        lbl_title.pack(anchor="w", pady=(8, 0))

        # Subtítulo
        lbl_sub = ctk.CTkLabel(
            content, text=subtitle,
            font=ctk.CTkFont(size=11),
            text_color=_c("subtitle_text"),
        )
        lbl_sub.pack(anchor="w")

        # Hover effects
        def on_enter(e):
            card.configure(fg_color=hover)

        def on_leave(e):
            card.configure(fg_color=bg)

        for w in [card, content, top_row, lbl_icon, lbl_value, lbl_title, lbl_sub, accent_bar]:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

        return card, lbl_value, lbl_sub

    # ═══════════════════════════ MAIN CONTENT ═════════════════════════════
    def _build_main_content(self):
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.grid(row=3, column=0, padx=28, pady=(14, 28), sticky="nsew")
        main_content.grid_columnconfigure(0, weight=3, minsize=480)
        main_content.grid_columnconfigure(1, weight=1, minsize=280)
        main_content.grid_rowconfigure(0, weight=1)

        # ─────── Esquerda: Próximos Agendamentos ──────────
        left_panel = ctk.CTkFrame(main_content, corner_radius=14)
        left_panel.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")
        left_panel.grid_rowconfigure(1, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        # Header do painel
        header_ag = ctk.CTkFrame(left_panel, fg_color="transparent")
        header_ag.grid(row=0, column=0, padx=18, pady=(16, 8), sticky="ew")
        header_ag.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_ag, text="📋  Próximos Agendamentos",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self.badge_ag_count = ctk.CTkLabel(
            header_ag, text="0",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=_c("card_agenda_accent"),
            text_color="white",
            corner_radius=10,
            width=28, height=22,
        )
        self.badge_ag_count.grid(row=0, column=1, padx=(8, 0))

        # Lista scrollable
        self.table_container = ctk.CTkScrollableFrame(
            left_panel, fg_color="transparent", corner_radius=0,
        )
        self.table_container.grid(row=1, column=0, padx=8, pady=(0, 12), sticky="nsew")
        self.table_container.grid_columnconfigure(0, weight=1)

        # ─────── Direita: Aniversariantes + Estatísticas ──────────
        right_panel = ctk.CTkFrame(main_content, fg_color="transparent")
        right_panel.grid(row=0, column=1, padx=(8, 0), pady=0, sticky="nsew")
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_rowconfigure(1, weight=0)
        right_panel.grid_columnconfigure(0, weight=1)

        # Card Aniversariantes
        self.bday_card = ctk.CTkFrame(right_panel, corner_radius=14)
        self.bday_card.grid(row=0, column=0, pady=(0, 10), sticky="nsew")
        self.bday_card.grid_rowconfigure(1, weight=1)
        self.bday_card.grid_columnconfigure(0, weight=1)

        bday_header = ctk.CTkFrame(self.bday_card, fg_color="transparent")
        bday_header.grid(row=0, column=0, padx=16, pady=(14, 6), sticky="ew")
        bday_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            bday_header, text="🎂  Aniversariantes do Mês",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self.badge_bday_count = ctk.CTkLabel(
            bday_header, text="0",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=_c("card_aval_accent"),
            text_color="white",
            corner_radius=10,
            width=28, height=22,
        )
        self.badge_bday_count.grid(row=0, column=1, padx=(6, 0))

        self.scroll_bday = ctk.CTkScrollableFrame(
            self.bday_card, fg_color="transparent", corner_radius=0,
        )
        self.scroll_bday.grid(row=1, column=0, padx=6, pady=(0, 10), sticky="nsew")

        # Card Estatísticas Rápidas
        stats_card = ctk.CTkFrame(right_panel, corner_radius=14)
        stats_card.grid(row=1, column=0, sticky="ew")
        stats_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            stats_card, text="📊  Estatísticas Rápidas",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=(14, 10), sticky="w")

        # Mini-card: Treinos
        stat1 = ctk.CTkFrame(stats_card, fg_color=_c("card_treinos_bg"), corner_radius=10)
        stat1.grid(row=1, column=0, padx=12, pady=(0, 6), sticky="ew")

        stat1_inner = ctk.CTkFrame(stat1, fg_color="transparent")
        stat1_inner.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(stat1_inner, text="💪", font=ctk.CTkFont(size=18)).pack(side="left")
        self.label_treinos_ativos = ctk.CTkLabel(
            stat1_inner, text="Treinos Cadastrados: 0",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        )
        self.label_treinos_ativos.pack(side="left", padx=(8, 0), fill="x", expand=True)

        # Mini-card: Média de Idade
        stat2 = ctk.CTkFrame(stats_card, fg_color=_c("card_alunos_bg"), corner_radius=10)
        stat2.grid(row=2, column=0, padx=12, pady=(0, 14), sticky="ew")

        stat2_inner = ctk.CTkFrame(stat2, fg_color="transparent")
        stat2_inner.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(stat2_inner, text="📈", font=ctk.CTkFont(size=18)).pack(side="left")
        self.label_media_idade = ctk.CTkLabel(
            stat2_inner, text="Média de Idade: 0 anos",
            font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
        )
        self.label_media_idade.pack(side="left", padx=(8, 0), fill="x", expand=True)

    # ═══════════════════════════ AGENDAMENTO CARD ═════════════════════════
    def _create_agendamento_card(self, row: dict, index: int) -> None:
        """Cria um card de agendamento estilizado."""
        data_obj = datetime.date.fromisoformat(row["data"])
        dia_semana = _DIA_CURTO[data_obj.weekday()]
        data_fmt = data_obj.strftime("%d/%m")
        is_today = row["data"] == datetime.date.today().isoformat()

        bg = _c("ag_today_bg") if is_today else _c("ag_card_bg")
        hover_color = _c("ag_today_hover") if is_today else _c("ag_card_hover")

        card = ctk.CTkFrame(self.table_container, fg_color=bg, corner_radius=12)
        card.pack(fill="x", pady=2, padx=4)

        # ── Layout: [HOJE?] [DATE BOX] [INFO] [STATUS BADGE] ──

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=6)

        # Badge "HOJE" se for hoje
        if is_today:
            today_badge = ctk.CTkLabel(
                inner, text="HOJE",
                font=ctk.CTkFont(size=9, weight="bold"),
                fg_color=_c("card_agenda_accent"),
                text_color="white",
                corner_radius=6,
                width=40, height=18,
            )
            today_badge.pack(side="left", padx=(0, 8))

        # Date Box
        date_box = ctk.CTkFrame(inner, width=52, height=52,
                                fg_color=_c("ag_date_box"), corner_radius=10)
        date_box.pack(side="left", padx=(0, 12))
        date_box.pack_propagate(False)

        ctk.CTkLabel(
            date_box, text=dia_semana,
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=_c("subtitle_text"),
        ).pack(pady=(7, 0))
        ctk.CTkLabel(
            date_box, text=data_fmt,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(pady=(0, 5))

        # Info
        info_frame = ctk.CTkFrame(inner, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            info_frame, text=row["nome_aluno"],
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w")

        tipo_icons = {
            "Avaliação": "⚖️",
            "Treino": "💪",
            "Consulta": "📋",
        }
        tipo_icon = tipo_icons.get(row["tipo"], "📌")
        details = f"{tipo_icon}  {row['tipo']}  •  🕐 {row['horario']}h"
        ctk.CTkLabel(
            info_frame, text=details,
            font=ctk.CTkFont(size=11),
            text_color=_c("subtitle_text"),
        ).pack(anchor="w", pady=(2, 0))

        # Status Badge (pill shape)
        status = row["status"]
        status_colors = {
            "Pendente": _c("status_pendente"),
            "Concluído": _c("status_concluido"),
            "Cancelado": _c("status_cancelado"),
        }
        badge_color = status_colors.get(status, ("gray", "gray"))

        status_badge = ctk.CTkLabel(
            inner, text=f"  {status}  ",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=badge_color,
            text_color="white",
            corner_radius=10,
            height=24,
        )
        status_badge.pack(side="right", padx=(8, 0))

        # Hover effect
        def on_enter(e):
            card.configure(fg_color=hover_color)

        def on_leave(e):
            card.configure(fg_color=bg)

        for w in [card, inner, info_frame, date_box]:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

    # ═══════════════════════════ BIRTHDAY CARD ════════════════════════════
    def _create_bday_card(self, row: dict, index: int) -> None:
        """Cria um card de aniversariante com hover e destaque."""
        today = datetime.date.today()
        try:
            dn = datetime.date.fromisoformat(row["data_nascimento"])
            dia = dn.day
            mes = dn.month
            dia_str = f"{dia:02d}"
            is_today = (dia == today.day and mes == today.month)
            idade = today.year - dn.year
        except Exception:
            dia_str = "??"
            is_today = False
            idade = 0

        bg = _c("bday_today_bg") if is_today else _c("bday_card_bg")
        hover = _c("bday_today_hover") if is_today else _c("bday_card_hover")

        card = ctk.CTkFrame(self.scroll_bday, fg_color=bg, corner_radius=10)
        card.pack(fill="x", pady=2, padx=3)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=5)

        # Ícone
        icon_text = "🎉" if is_today else "🎂"
        ctk.CTkLabel(inner, text=icon_text, font=ctk.CTkFont(size=18)).pack(side="left", padx=(0, 6))

        # Info
        info_frame = ctk.CTkFrame(inner, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        name_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        name_row.pack(fill="x")

        ctk.CTkLabel(
            name_row, text=row["nome"],
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left")

        if is_today:
            ctk.CTkLabel(
                name_row, text="  HOJE! 🎉",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=_c("card_aval_accent"),
            ).pack(side="left")

        sub_text = f"Dia {dia_str}"
        if idade > 0:
            sub_text += f"  •  {idade} anos"
        ctk.CTkLabel(
            info_frame, text=sub_text,
            font=ctk.CTkFont(size=10),
            text_color=_c("subtitle_text"),
        ).pack(anchor="w")

        # Hover
        def on_enter(e):
            card.configure(fg_color=hover)

        def on_leave(e):
            card.configure(fg_color=bg)

        for w in [card, inner, info_frame, name_row]:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

    # ═══════════════════════════ EMPTY STATES ═════════════════════════════
    def _show_empty_state(self, container, icon: str, message: str):
        """Mostra um empty state amigável com ícone grande."""
        frame = ctk.CTkFrame(container, fg_color="transparent")
        frame.pack(fill="both", expand=True, pady=40)

        ctk.CTkLabel(
            frame, text=icon,
            font=ctk.CTkFont(size=48),
            text_color=_c("empty_icon"),
        ).pack()

        ctk.CTkLabel(
            frame, text=message,
            font=ctk.CTkFont(size=13),
            text_color=_c("empty_text"),
        ).pack(pady=(8, 0))

    # ═══════════════════════════ TIMER ════════════════════════════════════
    def _start_timer(self):
        try:
            secs = int(self.get_refresh_seconds() or 0)
            if secs > 0:
                self.after(secs * 1000, self._refresh_timer)
        except Exception:
            pass

    def _refresh_timer(self) -> None:
        try:
            self.refresh_data()
        finally:
            self._start_timer()

    # ═══════════════════════════ REFRESH DATA ═════════════════════════════
    def refresh_data(self) -> None:
        # Busca clima em thread separada
        if self.cidade_var:
            threading.Thread(target=self._fetch_weather, daemon=True).start()

        today = datetime.date.today()
        today_iso = today.isoformat()
        current_month = today.strftime("%m")

        # Atualiza saudação (pode mudar se passou do meio-dia/noite)
        saudacao, emoji = _saudacao()
        if hasattr(self, "greeting_label"):
            self.greeting_label.configure(text=f"{emoji}  {saudacao}!")
        if hasattr(self, "date_label"):
            self.date_label.configure(text=_data_extenso(today))

        # ── 1. Total de Alunos ──
        row = db.fetch_one("SELECT COUNT(*) AS total FROM alunos")
        total_alunos = row["total"] if row is not None else 0
        if hasattr(self, "lbl_alunos"):
            self.lbl_alunos.configure(text=str(total_alunos))
            self.lbl_alunos_sub.configure(text="cadastrados")

        # ── 2. Agendamentos Hoje e Próximos ──
        ag_rows = db.fetch_all(
            """
            SELECT a.id, a.data, a.horario, a.tipo, al.nome AS nome_aluno, a.status
            FROM agendamentos a
            JOIN alunos al ON al.id = a.id_aluno
            WHERE a.data >= ?
            ORDER BY a.data ASC, a.horario ASC
            LIMIT 20
            """,
            (today_iso,),
        )

        ag_hoje = [r for r in ag_rows if r["data"] == today_iso]
        total_ag = len(ag_hoje)

        if hasattr(self, "lbl_agendamentos"):
            self.lbl_agendamentos.configure(text=str(total_ag))
            self.lbl_agenda_sub.configure(text="programados para hoje")

        # Badge de contagem total
        if hasattr(self, "badge_ag_count"):
            self.badge_ag_count.configure(text=str(len(ag_rows)))

        # Lista de Agendamentos
        for widget in self.table_container.winfo_children():
            widget.destroy()

        if not ag_rows:
            self._show_empty_state(
                self.table_container,
                "📅",
                "Nenhum agendamento próximo"
            )
        else:
            for i, ag in enumerate(ag_rows):
                self._create_agendamento_card(ag, i)

        # ── 3. Avaliações no Mês ──
        av_row = db.fetch_one(
            "SELECT COUNT(*) as total FROM avaliacoes_fisicas WHERE strftime('%m', data) = ?",
            (current_month,)
        )
        total_av = av_row["total"] if av_row else 0
        if hasattr(self, "lbl_avaliacoes"):
            self.lbl_avaliacoes.configure(text=str(total_av))
            self.lbl_aval_sub.configure(
                text=f"em {_MESES[int(current_month)]}"
            )

        # ── 4. Aniversariantes do Mês ──
        bday_rows = db.fetch_all(
            "SELECT nome, data_nascimento FROM alunos WHERE strftime('%m', data_nascimento) = ? ORDER BY strftime('%d', data_nascimento)",
            (current_month,)
        )

        if hasattr(self, "badge_bday_count"):
            self.badge_bday_count.configure(text=str(len(bday_rows)))

        for widget in self.scroll_bday.winfo_children():
            widget.destroy()

        if not bday_rows:
            self._show_empty_state(
                self.scroll_bday,
                "🎂",
                "Nenhum aniversariante\neste mês"
            )
        else:
            for i, bday in enumerate(bday_rows):
                self._create_bday_card(bday, i)

        # ── 5. Estatísticas Extras ──
        treinos_row = db.fetch_one("SELECT COUNT(*) as total FROM treinos")
        total_treinos = treinos_row["total"] if treinos_row else 0
        if hasattr(self, "label_treinos_ativos"):
            self.label_treinos_ativos.configure(text=f"Treinos Cadastrados: {total_treinos}")
        if hasattr(self, "lbl_treinos"):
            self.lbl_treinos.configure(text=str(total_treinos))

        # Média de idade
        avg_age = 0
        if total_alunos > 0:
            age_rows = db.fetch_all(
                "SELECT data_nascimento FROM alunos WHERE data_nascimento IS NOT NULL AND data_nascimento != ''"
            )
            if age_rows:
                total_years = 0
                count = 0
                this_year = today.year
                for r in age_rows:
                    try:
                        y = int(r["data_nascimento"][:4])
                        total_years += (this_year - y)
                        count += 1
                    except Exception:
                        pass
                if count > 0:
                    avg_age = int(total_years / count)

        if hasattr(self, "label_media_idade"):
            self.label_media_idade.configure(text=f"Média de Idade: {avg_age} anos")

    def _fetch_weather(self):
        cidade = None
        if self.cidade_var and self.cidade_var.get():
            cidade = self.cidade_var.get()
        else:
            # Tenta detectar automaticamente
            cidade = get_current_city()
            
        if not cidade:
            self.after(0, lambda: self.weather_temp_lbl.configure(text="Localização não detectada"))
            return
            
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={self.api_key}&units=metric&lang=pt_br"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                temp = int(data["main"]["temp"])
                desc = data["weather"][0]["description"].capitalize()
                icon_code = data["weather"][0]["icon"]
                
                # Mapeamento simples de ícones para emojis
                emoji_map = {
                    "01d": "☀️", "01n": "🌙",
                    "02d": "🌤️", "02n": "☁️",
                    "03d": "☁️", "03n": "☁️",
                    "04d": "☁️", "04n": "☁️",
                    "09d": "🌦️", "09n": "🌧️",
                    "10d": "🌧️", "10n": "🌧️",
                    "11d": "⛈️", "11n": "⛈️",
                    "13d": "❄️", "13n": "❄️",
                    "50d": "🌫️", "50n": "🌫️",
                }
                emoji = emoji_map.get(icon_code, "🌤️")
                
                # Agenda atualização da UI na thread principal
                self.after(0, lambda: self._update_weather_ui(temp, desc, emoji, cidade))
            else:
                self.after(0, lambda: self.weather_temp_lbl.configure(text="Clima indisponível"))
        except Exception:
            self.after(0, lambda: self.weather_temp_lbl.configure(text="Erro ao carregar clima"))

    def _update_weather_ui(self, temp, desc, emoji, cidade):
        if hasattr(self, "weather_temp_lbl"):
            self.weather_temp_lbl.configure(text=f"{temp}°C em {cidade}")
        if hasattr(self, "weather_desc_lbl"):
            self.weather_desc_lbl.configure(text=f"• {desc}")
        if hasattr(self, "weather_icon_lbl"):
            self.weather_icon_lbl.configure(text=emoji)

    def _animate_weather(self):
        """Micro-animação de pulsação para o ícone do clima"""
        if not hasattr(self, "weather_icon_lbl") or not self.weather_icon_lbl.winfo_exists():
            return
            
        # Altera o tamanho da fonte levemente para criar efeito de pulso
        current_size = self.weather_pulse_val
        if current_size >= 28:
            self.weather_pulse_dir = -0.5
        elif current_size <= 22:
            self.weather_pulse_dir = 0.5
            
        self.weather_pulse_val += self.weather_pulse_dir
        
        try:
            self.weather_icon_lbl.configure(font=ctk.CTkFont(size=int(self.weather_pulse_val)))
        except Exception:
            pass
            
        self.after(50, self._animate_weather)
