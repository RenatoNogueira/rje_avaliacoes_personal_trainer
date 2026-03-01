"""
Módulo centralizado de tema / design system para o RJE Avaliações.

Fornece cores, fontes e fábricas de widgets reutilizáveis para manter
a consistência visual em todas as telas.
"""

import customtkinter as ctk


# ─────────────────────────── Paleta de Cores ──────────────────────────────────
# Cada valor = (light_mode, dark_mode)

COLORS = {
    # ── Geral / superfícies ──
    "header_bg":            ("transparent", "transparent"),
    "section_title":        ("gray40", "gray60"),
    "subtitle_text":        ("gray50", "gray55"),

    # ── Cards genéricos ──
    "card_bg":              ("gray94", "gray18"),
    "card_hover":           ("gray88", "gray25"),
    "card_border":          ("gray80", "gray30"),

    # ── Cards de resumo (dashboard) ──
    "card_alunos_bg":       ("#e3f2fd", "#1a2740"),
    "card_alunos_accent":   ("#42a5f5", "#5c9ce6"),
    "card_alunos_hover":    ("#bbdefb", "#233654"),
    "card_agenda_bg":       ("#e8f5e9", "#1a3324"),
    "card_agenda_accent":   ("#66bb6a", "#5dba62"),
    "card_agenda_hover":    ("#c8e6c9", "#244936"),
    "card_aval_bg":         ("#fff3e0", "#3a2a14"),
    "card_aval_accent":     ("#ffa726", "#e6952e"),
    "card_aval_hover":      ("#ffe0b2", "#4d3a20"),
    "card_treinos_bg":      ("#f3e5f5", "#2d1a38"),
    "card_treinos_accent":  ("#ab47bc", "#b35cc5"),
    "card_treinos_hover":   ("#e1bee7", "#3f264d"),

    # ── Status / badges ──
    "status_pendente":      ("#ff9800", "#ff9800"),
    "status_concluido":     ("#4caf50", "#4caf50"),
    "status_cancelado":     ("#f44336", "#f44336"),

    # ── Agendamento cards ──
    "ag_card_bg":           ("gray92", "gray18"),
    "ag_card_hover":        ("gray86", "gray25"),
    "ag_today_bg":          ("#e0f2f1", "#1b3332"),
    "ag_today_hover":       ("#b2dfdb", "#254a48"),
    "ag_date_box":          ("gray82", "gray28"),

    # ── Aniversariantes ──
    "bday_card_bg":         ("gray94", "gray22"),
    "bday_card_hover":      ("white", "gray30"),
    "bday_today_bg":        ("#fff9c4", "#3a3520"),
    "bday_today_hover":     ("#fff59d", "#4d4a2b"),

    # ── Empty state ──
    "empty_icon":           ("gray75", "gray40"),
    "empty_text":           ("gray55", "gray50"),

    # ── Botões de ação ──
    "btn_new":              ("#2ecc71", "#27ae60"),
    "btn_new_hover":        ("#27ae60", "#219a52"),
    "btn_save":             ("#3498db", "#2980b9"),
    "btn_save_hover":       ("#2980b9", "#2471a3"),
    "btn_delete":           ("#e74c3c", "#c0392b"),
    "btn_delete_hover":     ("#c0392b", "#a93226"),
    "btn_pdf":              ("#3498db", "#2980b9"),
    "btn_pdf_hover":        ("#2980b9", "#2471a3"),
    "btn_catalog":          ("#f39c12", "#d35400"),
    "btn_catalog_hover":    ("#d35400", "#ba4a00"),

    # ── Lista / panel lateral ──
    "panel_bg":             ("gray96", "gray14"),
    "list_card_bg":         ("gray92", "gray20"),
    "list_card_hover":      ("gray86", "gray28"),
    "list_card_accent":     ("#3b82f6", "#60a5fa"),
    "list_card_selected":   ("#dbeafe", "#1e3a5f"),

    # ── Header de view ──
    "view_header_icon_bg":  ("#e0e7ff", "#1e293b"),
    "view_header_title":    ("gray10", "gray95"),
    "view_header_subtitle": ("gray50", "gray55"),

    # ── Formulário / seções internas ──
    "section_accent":       ("#3b82f6", "#60a5fa"),
    "section_bg":           ("gray96", "gray16"),
    "input_border_focus":   ("#3b82f6", "#60a5fa"),

    # ── Login ──
    "login_gradient_start": ("#667eea", "#667eea"),
    "login_gradient_end":   ("#764ba2", "#764ba2"),
    "login_card_bg":        ("white", "#1a1a2e"),
    "login_input_bg":       ("gray96", "gray18"),
    "login_btn":            ("#667eea", "#667eea"),
    "login_btn_hover":      ("#5a6fd6", "#5a6fd6"),
    "login_error":          ("#ef4444", "#f87171"),

    # ── About ──
    "about_card_bg":        ("gray96", "gray18"),
    "about_badge_bg":       ("#dbeafe", "#1e3a5f"),
    "about_badge_text":     ("#1d4ed8", "#93c5fd"),
}


# Dicionário de overrides (pode ser preenchido em tempo de execução)
COLOR_OVERRIDES = {}


def set_accent_color(hex_color: str):
    """
    Define uma cor de destaque customizada para o sistema.
    Atualiza as chaves que devem seguir a cor da marca do usuário.
    """
    if not hex_color:
        COLOR_OVERRIDES.clear()
        return

    # Mapeia as chaves que devem ser afetadas pela cor customizada
    accent_keys = [
        "card_alunos_accent", "card_agenda_accent", "card_aval_accent", 
        "card_treinos_accent", "btn_save", "btn_pdf", "list_card_accent",
        "section_accent", "input_border_focus", "login_btn"
    ]
    
    for key in accent_keys:
        COLOR_OVERRIDES[key] = (hex_color, hex_color)
    
    # Adiciona versões mais escuras/claras para hover se necessário
    # Por enquanto, usaremos a mesma cor para simplificar ou uma variação fixa
    hover_keys = ["btn_save_hover", "btn_pdf_hover", "login_btn_hover"]
    for key in hover_keys:
        COLOR_OVERRIDES[key] = (hex_color, hex_color)


def _c(key: str) -> tuple:
    """Retorna a tupla de cor (light, dark) para a chave informada, considerando overrides."""
    return COLOR_OVERRIDES.get(key, COLORS[key])


# ──────────────────────────── Presets de Fontes ───────────────────────────────

def font_title():
    return ctk.CTkFont(size=24, weight="bold")

def font_subtitle():
    return ctk.CTkFont(size=13)

def font_body():
    return ctk.CTkFont(size=13)

def font_small():
    return ctk.CTkFont(size=11)

def font_section():
    return ctk.CTkFont(size=15, weight="bold")


# ────────────────────────── Fábricas de Widgets ───────────────────────────────

def create_view_header(parent, icon: str, title: str, subtitle: str = ""):
    """
    Cria um header padronizado para cada view.
    Retorna o frame do header.

        ┌──────────────────────────────────────┐
        │  [icon_circle]  Title                │
        │                 Subtitle             │
        └──────────────────────────────────────┘
    """
    header = ctk.CTkFrame(parent, fg_color="transparent")

    # Ícone circular
    icon_frame = ctk.CTkFrame(
        header,
        width=48, height=48,
        corner_radius=24,
        fg_color=_c("view_header_icon_bg"),
    )
    icon_frame.pack(side="left", padx=(0, 14))
    icon_frame.pack_propagate(False)

    icon_label = ctk.CTkLabel(
        icon_frame, text=icon,
        font=ctk.CTkFont(size=22),
    )
    icon_label.place(relx=0.5, rely=0.5, anchor="center")

    # Textos
    text_frame = ctk.CTkFrame(header, fg_color="transparent")
    text_frame.pack(side="left", fill="x", expand=True)

    ctk.CTkLabel(
        text_frame, text=title,
        font=font_title(),
        text_color=_c("view_header_title"),
        anchor="w",
    ).pack(anchor="w")

    if subtitle:
        ctk.CTkLabel(
            text_frame, text=subtitle,
            font=font_subtitle(),
            text_color=_c("view_header_subtitle"),
            anchor="w",
        ).pack(anchor="w")

    return header


def create_styled_card(parent, fg_color=None, accent_color=None,
                       hover_color=None, corner_radius=12, on_click=None):
    """
    Cria um card com accent bar no topo e hover effect.
    Retorna o frame do card.
    """
    bg = fg_color or _c("list_card_bg")
    hover = hover_color or _c("list_card_hover")

    card = ctk.CTkFrame(parent, fg_color=bg, corner_radius=corner_radius)

    # Accent bar
    if accent_color:
        accent_bar = ctk.CTkFrame(
            card, height=3, fg_color=accent_color, corner_radius=2,
        )
        accent_bar.pack(fill="x", padx=12, pady=(10, 0))

    # Hover effect
    def _hover_enter(e):
        card.configure(fg_color=hover)
    def _hover_leave(e):
        card.configure(fg_color=bg)

    card.bind("<Enter>", _hover_enter)
    card.bind("<Leave>", _hover_leave)

    # Click binding
    if on_click:
        card.bind("<Button-1>", lambda e: on_click())

    return card


def bind_card_hover(card, bg, hover):
    """Aplica hover effect a um card existente."""
    def _enter(e):
        card.configure(fg_color=hover)
    def _leave(e):
        card.configure(fg_color=bg)
    card.bind("<Enter>", _enter)
    card.bind("<Leave>", _leave)


def bind_click_recursive(widget, callback):
    """Aplica <Button-1> recursivamente a todos os filhos."""
    widget.bind("<Button-1>", lambda e: callback())
    for child in widget.winfo_children():
        bind_click_recursive(child, callback)


def create_action_button(parent, text: str, color_key: str, command,
                         width=None, **kwargs):
    """
    Cria um botão de ação estilizado.
    color_key: chave em COLORS (ex: 'btn_new', 'btn_delete')
    """
    fg = _c(color_key)
    hover = _c(f"{color_key}_hover")
    btn_kwargs = dict(
        text=text,
        command=command,
        fg_color=fg,
        hover_color=hover,
        corner_radius=8,
        height=36,
        font=ctk.CTkFont(size=13, weight="bold"),
    )
    if width:
        btn_kwargs["width"] = width
    btn_kwargs.update(kwargs)
    return ctk.CTkButton(parent, **btn_kwargs)


def create_empty_state(parent, icon: str, message: str):
    """
    Cria um estado vazio amigável com ícone grande e mensagem.
    Retorna o frame.
    """
    frame = ctk.CTkFrame(parent, fg_color="transparent")

    ctk.CTkLabel(
        frame, text=icon,
        font=ctk.CTkFont(size=48),
        text_color=_c("empty_icon"),
    ).pack(pady=(30, 8))

    ctk.CTkLabel(
        frame, text=message,
        font=font_subtitle(),
        text_color=_c("empty_text"),
    ).pack()

    return frame


def create_section_title(parent, text: str, pack=False):
    """
    Cria um título de seção com acento lateral.
    Retorna o frame contendo o título.
    """
    frame = ctk.CTkFrame(parent, fg_color="transparent")

    accent = ctk.CTkFrame(
        frame, width=4, height=20,
        fg_color=_c("section_accent"),
        corner_radius=2,
    )
    accent.pack(side="left", padx=(0, 10))

    ctk.CTkLabel(
        frame, text=text,
        font=font_section(),
        text_color=_c("view_header_title"),
        anchor="w",
    ).pack(side="left")

    if pack:
        frame.pack(fill="x", padx=16, pady=(18, 8), anchor="w")

    return frame


def create_status_pill(parent, status: str, pack_side="right"):
    """
    Cria um badge de status compacto.
    status: 'Pendente', 'Concluído', 'Cancelado', etc.
    """
    status_lower = status.lower().strip()
    if "conclu" in status_lower or "realiz" in status_lower:
        bg = _c("status_concluido")
        text = "✓ " + status
    elif "cancel" in status_lower:
        bg = _c("status_cancelado")
        text = "✕ " + status
    else:
        bg = _c("status_pendente")
        text = "● " + status

    pill = ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont(size=10, weight="bold"),
        fg_color=bg,
        text_color="white",
        corner_radius=10,
        height=22,
        padx=10,
    )
    pill.pack(side=pack_side, padx=4)
    return pill


def create_info_badge(parent, text: str, bg=None, text_color=None):
    """Cria um badge informativo compacto (ex: data, contagem)."""
    badge_bg = bg or _c("about_badge_bg")
    badge_tc = text_color or _c("about_badge_text")

    return ctk.CTkLabel(
        parent, text=text,
        font=ctk.CTkFont(size=10, weight="bold"),
        fg_color=badge_bg,
        text_color=badge_tc,
        corner_radius=8,
        height=22,
        padx=8,
    )
