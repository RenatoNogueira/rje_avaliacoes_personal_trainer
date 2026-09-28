import customtkinter as ctk
import datetime
import os
import shutil
import sqlite3
import zipfile
from pathlib import Path
from tkinter import filedialog, messagebox

import app_paths
from utils.app_support import open_path, log

from .theme import _c, font_body, font_subtitle, font_small, create_view_header, create_action_button, create_empty_state, create_section_title, bind_card_hover
from database import db
from .utils import setup_enter_navigation, delete_files_with_prefix, create_tooltip, show_toast, bind_live_search
from utils.geo_utils import get_current_city
from utils.image_utils import create_circular_image


class SettingsView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        professor_var: ctk.StringVar,
        appearance_var: ctk.StringVar,
        color_theme_var: ctk.StringVar,
        refresh_var: ctk.StringVar,
        cidade_var: ctk.StringVar,
        accent_color_var: ctk.StringVar,
        current_user: dict | None = None,
    ) -> None:
        super().__init__(master)

        self.professor_var = professor_var
        self.appearance_var = appearance_var
        self.color_theme_var = color_theme_var
        self.refresh_var = refresh_var
        self.cidade_var = cidade_var
        self.accent_color_var = accent_color_var
        self.current_user = current_user

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        self.header = create_view_header(self, "⚙️", "Configurações", "Ajuste as preferências do sistema")
        self.header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Tabs Container
        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        tab_geral = self.tabs.add("Geral")
        
        is_admin = bool(self.current_user and self.current_user.get("is_admin"))
        
        # Só cria a aba de usuários se for admin
        if is_admin:
            tab_usuarios = self.tabs.add("Gestão de Usuários")
        
        # --- Tab Geral ---
        tab_geral.grid_columnconfigure(0, weight=1)
        
        scroll_geral = ctk.CTkScrollableFrame(tab_geral, fg_color="transparent")
        scroll_geral.pack(fill="both", expand=True)
        scroll_geral.grid_columnconfigure(1, weight=1)

        row = 0
        create_section_title(scroll_geral, "Preferências do Sistema").grid(row=row, column=0, columnspan=2, padx=16, pady=(18, 8), sticky="w")
        row += 1

        ctk.CTkLabel(scroll_geral, text="Nome do professor:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        entry_prof = ctk.CTkEntry(scroll_geral, textvariable=self.professor_var)
        entry_prof.grid(row=row, column=1, padx=10, pady=5, sticky="ew")

        row += 1
        ctk.CTkLabel(scroll_geral, text="Auto-atualização Dashboard (s):").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        self.entry_refresh = ctk.CTkEntry(scroll_geral, textvariable=self.refresh_var, width=100)
        self.entry_refresh.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        create_tooltip(self.entry_refresh, "Intervalo em segundos para atualizar o Dashboard. Use 0 para desativar.")
        
        row += 1
        ctk.CTkLabel(scroll_geral, text="Cidade (para Previsão do Tempo):").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        self.entry_cidade = ctk.CTkEntry(scroll_geral, textvariable=self.cidade_var)
        self.entry_cidade.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        
        # Botão para auto-detectar
        btn_detect = ctk.CTkButton(
            scroll_geral, text="📍 Detectar Automaticamente", 
            width=200, height=28,
            command=self._on_detect_city
        )
        btn_detect.grid(row=row+1, column=1, padx=10, pady=(0, 10), sticky="w")
        create_tooltip(btn_detect, "Usa seu IP para identificar a cidade atual")

        # (o botão ocupa a linha seguinte; antes o título "Aparência" ficava sobreposto a ele)
        row += 2
        create_section_title(scroll_geral, "Aparência").grid(row=row, column=0, columnspan=2, padx=16, pady=(18, 8), sticky="w")
        
        row += 1
        ctk.CTkLabel(scroll_geral, text="Tema:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        appearance_frame = ctk.CTkFrame(scroll_geral, fg_color="transparent")
        appearance_frame.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        
        btn_light = ctk.CTkRadioButton(appearance_frame, text="Claro", variable=self.appearance_var, value="light", command=self._on_appearance_change)
        btn_light.pack(side="left", padx=(0, 10))
        btn_dark = ctk.CTkRadioButton(appearance_frame, text="Escuro", variable=self.appearance_var, value="dark", command=self._on_appearance_change)
        btn_dark.pack(side="left", padx=(0, 10))
        btn_system = ctk.CTkRadioButton(appearance_frame, text="Sistema", variable=self.appearance_var, value="system", command=self._on_appearance_change)
        btn_system.pack(side="left", padx=(0, 10))

        row += 1
        ctk.CTkLabel(scroll_geral, text="Cor Principal:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        self.combo_theme = ctk.CTkComboBox(scroll_geral, values=["dark-blue", "blue", "green"], variable=self.color_theme_var, command=self._on_color_theme_change)
        self.combo_theme.grid(row=row, column=1, padx=10, pady=5, sticky="w")

        row += 1
        btn_save_geral = create_action_button(
            scroll_geral, "💾 Salvar Preferências", "btn_save", self._on_save_prefs, width=200
        )
        btn_save_geral.grid(row=row, column=1, padx=10, pady=20, sticky="w")

        row += 1
        create_section_title(scroll_geral, "Manutenção de Dados").grid(row=row, column=0, columnspan=2, padx=16, pady=(18, 8), sticky="w")

        row += 1
        btn_frame = ctk.CTkFrame(scroll_geral, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        btn_backup = create_action_button(btn_frame, "📦 Criar Backup", "btn_new", self._on_backup, width=150)
        btn_backup.pack(side="left", padx=(0, 10))
        create_tooltip(btn_backup, "Gera um arquivo .zip com o banco de dados, fotos e configurações")
        
        btn_restore = create_action_button(btn_frame, "🔄 Restaurar Backup", "btn_delete", self._on_restore, width=150)
        btn_restore.pack(side="left", padx=(0, 10))
        create_tooltip(btn_restore, "Restaura um backup (.zip ou .db). Uma cópia de segurança do estado atual é feita antes.")
        
        btn_open_folder = create_action_button(btn_frame, "📂 Pasta de Dados", "btn_save", self._on_open_data_folder, width=180)
        btn_open_folder.pack(side="left", padx=(0, 10))

        row += 1
        db_path_label = ctk.CTkLabel(
            scroll_geral,
            text=f"Dados em: {app_paths.DATA_ROOT}   •   Backups automáticos diários em: {app_paths.BACKUP_DIR / 'auto'}",
            font=ctk.CTkFont(size=10), text_color="gray", justify="left", wraplength=900,
        )
        db_path_label.grid(row=row, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="w")

        # ── Segurança: alterar a própria senha ──
        row += 1
        create_section_title(scroll_geral, "Segurança").grid(row=row, column=0, columnspan=2, padx=16, pady=(18, 8), sticky="w")
        row += 1
        ctk.CTkLabel(scroll_geral, text="Senha atual:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        self.entry_senha_atual = ctk.CTkEntry(scroll_geral, show="*", width=260)
        self.entry_senha_atual.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1
        ctk.CTkLabel(scroll_geral, text="Nova senha:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        self.entry_senha_nova = ctk.CTkEntry(scroll_geral, show="*", width=260, placeholder_text="mínimo 6 caracteres")
        self.entry_senha_nova.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        row += 1
        ctk.CTkLabel(scroll_geral, text="Confirmar nova senha:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        self.entry_senha_conf = ctk.CTkEntry(scroll_geral, show="*", width=260)
        self.entry_senha_conf.grid(row=row, column=1, padx=10, pady=5, sticky="w")
        self.entry_senha_conf.bind("<Return>", lambda e: self._on_change_password(), add="+")
        row += 1
        create_action_button(scroll_geral, "🔒 Alterar minha senha", "btn_save", self._on_change_password, width=200).grid(
            row=row, column=1, padx=10, pady=(10, 20), sticky="w"
        )

        # --- Tab Usuários ---
        if is_admin:
            tab_usuarios.grid_columnconfigure(0, weight=1)
            tab_usuarios.grid_rowconfigure(0, weight=1)

            # Layout 2 colunas para Usuários
            users_content = ctk.CTkFrame(tab_usuarios, fg_color="transparent")
            users_content.pack(fill="both", expand=True)
            users_content.grid_columnconfigure(0, weight=1)
            users_content.grid_columnconfigure(1, weight=2)
            users_content.grid_rowconfigure(1, weight=1) # Row 1 expande (lista), Row 0 é filtro

            # Left Panel Container (Filtro + Lista)
            left_panel = ctk.CTkFrame(users_content, fg_color="transparent")
            left_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 10))
            left_panel.grid_rowconfigure(1, weight=1)
            left_panel.grid_columnconfigure(0, weight=1)

            # Filtros (Esquerda Topo)
            filter_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
            filter_frame.grid(row=0, column=0, padx=0, pady=(0, 10), sticky="ew")
            
            self.entry_filtro_tel = ctk.CTkEntry(filter_frame, placeholder_text="Filtrar por nome, usuário ou telefone...")
            self.entry_filtro_tel.pack(side="left", fill="x", expand=True, padx=(0, 5))
            bind_live_search(self.entry_filtro_tel, self._load_users)
            
            ctk.CTkButton(filter_frame, text="🔍", width=40, command=self._load_users).pack(side="right")

            # Lista (Esquerda Corpo)
            self.scroll_users = ctk.CTkScrollableFrame(left_panel, fg_color=_c("panel_bg"), corner_radius=0)
            self.scroll_users.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")

            # Form (Direita)
            form_user = ctk.CTkFrame(users_content)
            form_user.grid(row=0, column=1, rowspan=2, padx=(10, 0), pady=0, sticky="nsew")
            form_user.grid_columnconfigure(1, weight=1)

            create_section_title(form_user, "Dados do Usuário").grid(row=0, column=0, columnspan=2, padx=16, pady=(18, 8), sticky="w")

            ctk.CTkLabel(form_user, text="Usuário:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
            self.entry_user_username = ctk.CTkEntry(form_user)
            self.entry_user_username.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

            ctk.CTkLabel(form_user, text="Nome Completo:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
            self.entry_user_nome = ctk.CTkEntry(form_user)
            self.entry_user_nome.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

            ctk.CTkLabel(form_user, text="CREF:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
            self.entry_user_cref = ctk.CTkEntry(form_user)
            self.entry_user_cref.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

            ctk.CTkLabel(form_user, text="Senha:").grid(row=4, column=0, padx=10, pady=5, sticky="e")
            self.entry_user_senha = ctk.CTkEntry(form_user, show="*")
            self.entry_user_senha.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

            self.var_user_admin = ctk.BooleanVar(value=False)
            self.chk_user_admin = ctk.CTkCheckBox(form_user, text="Administrador", variable=self.var_user_admin)
            self.chk_user_admin.grid(row=5, column=1, padx=10, pady=5, sticky="w")

            self.var_user_ativo = ctk.BooleanVar(value=True)
            self.chk_user_ativo = ctk.CTkCheckBox(form_user, text="Personal (Ativo)", variable=self.var_user_ativo)
            self.chk_user_ativo.grid(row=6, column=1, padx=10, pady=5, sticky="w")

            self.var_user_trial = ctk.BooleanVar(value=False)
            self.chk_user_trial = ctk.CTkCheckBox(form_user, text="Usuário de Teste (Trial 30 dias)", variable=self.var_user_trial)
            self.chk_user_trial.grid(row=7, column=1, padx=10, pady=5, sticky="w")

            # Botões User
            btn_user_frame = ctk.CTkFrame(form_user, fg_color="transparent")
            btn_user_frame.grid(row=8, column=0, columnspan=2, padx=10, pady=20, sticky="ew")
            
            create_action_button(btn_user_frame, "+ Novo", "btn_new", self._on_user_novo, width=90).pack(side="left", padx=(0, 5))
            create_action_button(btn_user_frame, "💾 Salvar", "btn_save", self._on_user_salvar, width=90).pack(side="left", padx=(0, 5))
            
            # Botões de perigo na direita
            create_action_button(btn_user_frame, "🗑️ Excluir", "btn_delete", self._on_user_excluir, width=90).pack(side="right")
            create_action_button(btn_user_frame, "🚫 Desativar", "btn_pdf", self._on_user_desativar, width=100).pack(side="right", padx=(0, 5))

            self.selected_user_id: int | None = None
            self._load_users()
            
        setup_enter_navigation(self.tabs)

    def _on_save_prefs(self) -> None:
        try:
            v = int(str(self.refresh_var.get()).strip() or 0)
            if v < 0:
                raise ValueError
            if 0 < v < 10:
                v = 10
            self.refresh_var.set(str(v))
        except ValueError:
            messagebox.showwarning("Configurações", "Informe um número inteiro de segundos (0 desativa).")
            self.entry_refresh.focus_set()
            return
        app = self.winfo_toplevel()
        if hasattr(app, "_save_settings"):
            app._save_settings(notify=True)

    def _on_change_password(self) -> None:
        if not self.current_user:
            return
        atual = self.entry_senha_atual.get()
        nova = self.entry_senha_nova.get()
        conf = self.entry_senha_conf.get()
        row = db.fetch_one("SELECT senha_hash FROM usuarios WHERE id = ?", (int(self.current_user["id"]),))
        ok, _ = db.verify_password(atual, row["senha_hash"] if row else None)
        if not ok:
            messagebox.showwarning("Segurança", "A senha atual não confere.")
            self.entry_senha_atual.focus_set()
            return
        if len(nova) < 6:
            messagebox.showwarning("Segurança", "A nova senha deve ter pelo menos 6 caracteres.")
            self.entry_senha_nova.focus_set()
            return
        if nova != conf:
            messagebox.showwarning("Segurança", "A confirmação não confere com a nova senha.")
            self.entry_senha_conf.focus_set()
            return
        if nova == atual:
            messagebox.showwarning("Segurança", "A nova senha deve ser diferente da atual.")
            return
        db.execute("UPDATE usuarios SET senha_hash = ? WHERE id = ?",
                   (db.hash_password(nova), int(self.current_user["id"])), commit=True)
        for e in (self.entry_senha_atual, self.entry_senha_nova, self.entry_senha_conf):
            e.delete(0, "end")
        show_toast(self, "Senha alterada com sucesso", 2500, kind="success")

    def _on_detect_city(self):
        city = get_current_city()
        if city:
            self.cidade_var.set(city)
            show_toast(self, f"Cidade detectada: {city}", 2500, kind="success")
        else:
            messagebox.showerror("Erro", "Não foi possível detectar sua localização automaticamente.")

    def _on_appearance_change(self) -> None:
        value = self.appearance_var.get()
        ctk.set_appearance_mode(value)

    def _on_color_theme_change(self, value: str) -> None:
        ctk.set_default_color_theme(value)

    def _load_users(self) -> None:
        # Limpa lista
        if hasattr(self, "scroll_users"):
            for widget in self.scroll_users.winfo_children():
                widget.destroy()
            
            filtro_tel = ""
            if hasattr(self, "entry_filtro_tel"):
                filtro_tel = self.entry_filtro_tel.get().strip()

            query = """
                SELECT id, username, nome, cref, is_admin, ativo, is_trial, foto_perfil, telefone
                FROM usuarios
            """
            params = []
            
            if filtro_tel:
                query += " WHERE telefone LIKE ? OR nome LIKE ? OR username LIKE ?"
                params.extend([f"%{filtro_tel}%"] * 3)
                
            query += " ORDER BY username"

            rows = db.fetch_all(query, tuple(params))
            
            if not rows:
                create_empty_state(self.scroll_users, "👤", "Nenhum usuário encontrado").pack(pady=40)
                return

            for row in rows:
                self._create_user_card(row)

    def _create_user_card(self, row_obj: sqlite3.Row) -> None:
        row = dict(row_obj)
        bg = _c("list_card_bg")
        hover = _c("list_card_hover")
        
        card = ctk.CTkFrame(self.scroll_users, fg_color=bg, corner_radius=12)
        card.pack(fill="x", pady=4, padx=5)
        
        # Accent bar lateral
        accent = ctk.CTkFrame(card, width=4, fg_color=_c("list_card_accent"), corner_radius=2)
        accent.pack(side="left", fill="y", padx=(10, 0), pady=10)

        # Frame interno para layout horizontal (Foto + Info)
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", padx=10, pady=10)
        
        # Foto
        foto_path = app_paths.resolve_data_path(row["foto_perfil"])
        lbl_foto = ctk.CTkLabel(content, text="👤", width=40, height=40, fg_color="gray50", corner_radius=20)
        if foto_path:
            try:
                from pathlib import Path
                if Path(foto_path).exists():
                    pil_img = create_circular_image(foto_path, (80, 80))
                    if pil_img:
                        ctk_img = ctk.CTkImage(pil_img, size=(40, 40))
                        lbl_foto.configure(image=ctk_img, text="", fg_color="transparent")
            except Exception: pass
        lbl_foto.pack(side="left", padx=(0, 10))

        # Info Wrapper
        info_wrapper = ctk.CTkFrame(content, fg_color="transparent")
        info_wrapper.pack(side="left", fill="both", expand=True)

        status_color = "green" if row["ativo"] else "red"
        status_text = "Ativo" if row["ativo"] else "Inativo"
        
        role_parts = []
        if row["is_admin"]: role_parts.append("ADMIN")
        else: role_parts.append("PERSONAL")
        if row["is_trial"]: role_parts.append("TRIAL")
        role_text = " | ".join(role_parts)
        
        header = ctk.CTkFrame(info_wrapper, fg_color="transparent")
        header.pack(fill="x")
        
        lbl_user = ctk.CTkLabel(header, text=row["username"], font=ctk.CTkFont(size=14, weight="bold"))
        lbl_user.pack(side="left")
        
        lbl_role = ctk.CTkLabel(header, text=role_text, font=font_small(), text_color="gray")
        lbl_role.pack(side="right")
        
        lbl_nome = ctk.CTkLabel(info_wrapper, text=row["nome"] or "-", font=font_small(), text_color=_c("view_header_subtitle"), anchor="w")
        lbl_nome.pack(fill="x")
        
        footer = ctk.CTkFrame(info_wrapper, fg_color="transparent")
        footer.pack(fill="x", pady=(2, 0))
        
        lbl_status = ctk.CTkLabel(footer, text=status_text, font=font_small(), text_color=status_color)
        lbl_status.pack(side="left")
        
        cref = row.get("cref")
        if cref:
            ctk.CTkLabel(footer, text=f" | CREF: {cref}", font=font_small(), text_color="gray").pack(side="left")

        # Bind events
        for w in (card, content, lbl_foto, info_wrapper, header, lbl_user, lbl_nome, footer, lbl_status, lbl_role):
            w.bind("<Button-1>", lambda e, uid=row["id"]: self._on_user_card_click(uid))
            
        bind_card_hover(card, bg, hover)

    def _on_user_card_click(self, user_id: int) -> None:
        self.selected_user_id = user_id
        row = db.fetch_one(
            """
            SELECT id, username, nome, cref, is_admin, ativo, is_trial
            FROM usuarios
            WHERE id = ?
            """,
            (self.selected_user_id,),
        )
        if row is None:
            return
        self.entry_user_username.delete(0, "end")
        self.entry_user_username.insert(0, row["username"] or "")
        self.entry_user_nome.delete(0, "end")
        self.entry_user_nome.insert(0, row["nome"] or "")
        self.entry_user_cref.delete(0, "end")
        self.entry_user_cref.insert(0, row["cref"] or "")
        self.entry_user_senha.delete(0, "end")
        self.var_user_admin.set(bool(row["is_admin"]))
        self.var_user_ativo.set(bool(row["ativo"]))
        self.var_user_trial.set(bool(row["is_trial"]))

    def _on_user_novo(self) -> None:
        self.selected_user_id = None
        self.entry_user_username.delete(0, "end")
        self.entry_user_nome.delete(0, "end")
        self.entry_user_cref.delete(0, "end")
        self.entry_user_senha.delete(0, "end")
        self.var_user_admin.set(False)
        self.var_user_ativo.set(True)
        self.var_user_trial.set(False)

    def _on_user_salvar(self) -> None:
        username = self.entry_user_username.get().strip()
        nome = self.entry_user_nome.get().strip()
        senha = self.entry_user_senha.get()
        cref = self.entry_user_cref.get().strip() or None
        is_admin = 1 if self.var_user_admin.get() else 0
        ativo = 1 if self.var_user_ativo.get() else 0
        is_trial = 1 if self.var_user_trial.get() else 0

        if not username:
            messagebox.showwarning("Usuários", "Informe o nome de usuário.")
            return
        if senha and len(senha) < 6:
            messagebox.showwarning("Usuários", "A senha deve ter pelo menos 6 caracteres.")
            return

        # Não permite remover o último administrador ativo (evita ficar sem acesso à gestão)
        if self.selected_user_id is not None and (not is_admin or not ativo):
            outros_admins = db.fetch_one(
                "SELECT COUNT(*) AS n FROM usuarios WHERE is_admin = 1 AND ativo = 1 AND id != ?",
                (self.selected_user_id,),
            )
            atual = db.fetch_one("SELECT is_admin, ativo FROM usuarios WHERE id = ?", (self.selected_user_id,))
            if atual and atual["is_admin"] and atual["ativo"] and (outros_admins["n"] if outros_admins else 0) == 0:
                messagebox.showwarning("Usuários", "Este é o único administrador ativo. Crie outro administrador antes de alterá-lo.")
                return

        from database import db as _db

        if self.selected_user_id is None:
            if not senha:
                messagebox.showwarning("Usuários", "Informe a senha para novo usuário.")
                return
            senha_hash = _db.hash_password(senha)
            try:
                _db.execute(
                    """
                    INSERT INTO usuarios (username, senha_hash, nome, cref, is_admin, ativo, is_trial)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (username, senha_hash, nome or None, cref, is_admin, ativo, is_trial),
                    commit=True,
                )
            except sqlite3.IntegrityError:
                messagebox.showerror("Usuários", f"O usuário \"{username}\" já existe. Escolha outro nome de usuário.")
                return
            except Exception as exc:
                messagebox.showerror(
                    "Usuários",
                    f"Erro ao salvar usuário: {exc}",
                )
                return
        else:
            # Update
            if senha:
                senha_hash = _db.hash_password(senha)
                try:
                    _db.execute(
                        """
                        UPDATE usuarios
                        SET username = ?, nome = ?, cref = ?, is_admin = ?, ativo = ?, is_trial = ?, senha_hash = ?
                        WHERE id = ?
                        """,
                        (username, nome or None, cref, is_admin, ativo, is_trial, senha_hash, self.selected_user_id),
                        commit=True,
                    )
                except Exception as exc:
                    messagebox.showerror("Usuários", f"Erro ao atualizar: {exc}")
                    return
            else:
                try:
                    _db.execute(
                        """
                        UPDATE usuarios
                        SET username = ?, nome = ?, cref = ?, is_admin = ?, ativo = ?, is_trial = ?
                        WHERE id = ?
                        """,
                        (username, nome or None, cref, is_admin, ativo, is_trial, self.selected_user_id),
                        commit=True,
                    )
                except Exception as exc:
                    messagebox.showerror("Usuários", f"Erro ao atualizar: {exc}")
                    return

        self._load_users()
        self._on_user_novo()
        show_toast(self, "Usuário salvo", 2000, kind="success")

    def _on_user_desativar(self) -> None:
        if self.selected_user_id is None:
            messagebox.showwarning("Usuários", "Selecione um usuário na lista.")
            return
        if self.current_user and self.selected_user_id == self.current_user.get("id"):
            messagebox.showwarning(
                "Usuários",
                "Você não pode desativar o próprio usuário logado.",
            )
            return
        from database import db as _db
        try:
            _db.execute(
                "UPDATE usuarios SET ativo = 0 WHERE id = ?",
                (self.selected_user_id,),
                commit=True,
            )
        except Exception as exc:
            messagebox.showerror(
                "Usuários",
                f"Erro ao desativar usuário: {exc}",
            )
            return
        self._load_users()
        self._on_user_novo()

    def _on_user_excluir(self) -> None:
        if self.selected_user_id is None:
            messagebox.showwarning("Usuários", "Selecione um usuário na lista para excluir.")
            return
            
        if self.current_user and self.selected_user_id == self.current_user.get("id"):
            messagebox.showwarning(
                "Usuários",
                "Você não pode excluir o próprio usuário logado.",
            )
            return
            
        confirm = messagebox.askyesno(
            "Confirmar Exclusão",
            "ATENÇÃO: A exclusão de um usuário é permanente e pode afetar registros vinculados (alunos, treinos, etc).\n\n"
            "Deseja realmente excluir este usuário permanentemente?"
        )
        if not confirm:
            return

        from database import db as _db
        try:
            # Opção 1: Exclusão lógica (soft delete) se integridade referencial for problema
            # Opção 2: Exclusão física (DELETE)
            # Como o usuário pediu "excluir", vamos tentar DELETE físico.
            # Se houver constraints de FK, pode falhar ou precisar de cascade.
            # Vamos assumir que se falhar, avisamos.
            
            # Cleanup physical files (profile photo)
            usuarios_media_dir = app_paths.MEDIA_DIR / "usuarios"
            
            # Delete user photos (pattern: user_{id}_*)
            delete_files_with_prefix(usuarios_media_dir, f"user_{self.selected_user_id}_")

            _db.execute(
                "DELETE FROM usuarios WHERE id = ?",
                (self.selected_user_id,),
                commit=True,
            )
            messagebox.showinfo("Usuários", "Usuário excluído com sucesso.")
        except Exception as exc:
            messagebox.showerror(
                "Usuários",
                f"Erro ao excluir usuário: {exc}\n\nTente desativá-lo em vez de excluir se ele possuir registros vinculados.",
            )
            return
            
        self._load_users()
        self._on_user_novo()

    def _on_backup(self) -> None:
        """Backup completo em .zip: banco (cópia consistente), fotos e configurações."""
        if not Path(db.db_path).exists():
            messagebox.showerror("Backup", "Arquivo de banco de dados não encontrado.")
            return

        stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
        dest_path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("Backup RJE (zip)", "*.zip")],
            initialdir=str(app_paths.documents_dir()),
            initialfile=f"backup_rje_avaliacoes_{stamp}.zip",
            title="Salvar backup",
        )
        if not dest_path:
            return

        top = self.winfo_toplevel()
        try:
            top.configure(cursor="watch")
            top.update_idletasks()
            tmp_db = app_paths.BACKUP_DIR / f"_tmp_{stamp}.db"
            db.backup_to(tmp_db)
            with zipfile.ZipFile(dest_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(tmp_db, "data/rje_avaliacoes.db")
                if app_paths.SETTINGS_PATH.exists():
                    zf.write(app_paths.SETTINGS_PATH, "data/settings.json")
                branding = app_paths.DATA_DIR / "branding"
                for folder, arc_root in ((app_paths.MEDIA_DIR, "media"), (branding, "data/branding")):
                    if folder.exists():
                        for f in folder.rglob("*"):
                            if f.is_file():
                                zf.write(f, f"{arc_root}/{f.relative_to(folder).as_posix()}")
            tmp_db.unlink(missing_ok=True)
        except Exception as exc:
            log.exception("Erro no backup")
            messagebox.showerror("Backup", f"Erro ao criar backup: {exc}")
            return
        finally:
            top.configure(cursor="")

        show_toast(self, "Backup criado com sucesso", 2500, kind="success")

    @staticmethod
    def _is_sqlite(path: Path) -> bool:
        try:
            with open(path, "rb") as f:
                return f.read(16) == b"SQLite format 3\x00"
        except Exception:
            return False

    def _on_restore(self) -> None:
        source_path = filedialog.askopenfilename(
            filetypes=[("Backup RJE", "*.zip *.db"), ("Todos os arquivos", "*.*")],
            initialdir=str(app_paths.documents_dir()),
            title="Selecionar arquivo de backup",
        )
        if not source_path:
            return

        if not messagebox.askyesno(
            "Restaurar backup",
            "Os dados atuais serão substituídos pelos do backup selecionado.\n\n"
            "Uma cópia de segurança do estado atual será criada automaticamente antes.\n\n"
            "Deseja continuar?",
            icon="warning",
        ):
            return

        src = Path(source_path)
        stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        try:
            # 1) cópia de segurança do estado atual
            db.backup_to(app_paths.BACKUP_DIR / f"antes_da_restauracao_{stamp}.db")

            if src.suffix.lower() == ".zip":
                with zipfile.ZipFile(src) as zf:
                    names = zf.namelist()
                    if "data/rje_avaliacoes.db" not in names:
                        messagebox.showerror("Restaurar", "O arquivo .zip não parece ser um backup do RJE Avaliações.")
                        return
                    tmp_dir = app_paths.BACKUP_DIR / f"_restore_{stamp}"
                    # extração segura (bloqueia caminhos fora da pasta de destino)
                    for name in names:
                        target = (tmp_dir / name).resolve()
                        if tmp_dir.resolve() not in target.parents:
                            continue
                        if name.endswith("/"):
                            continue
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(name) as fsrc, open(target, "wb") as fdst:
                            shutil.copyfileobj(fsrc, fdst)
                    new_db = tmp_dir / "data" / "rje_avaliacoes.db"
                    if not self._is_sqlite(new_db):
                        messagebox.showerror("Restaurar", "O banco de dados dentro do backup está corrompido.")
                        return
                    shutil.copyfile(new_db, db.db_path)
                    if (tmp_dir / "data" / "settings.json").exists():
                        shutil.copyfile(tmp_dir / "data" / "settings.json", app_paths.SETTINGS_PATH)
                    for sub, dest in (("media", app_paths.MEDIA_DIR), ("data/branding", app_paths.DATA_DIR / "branding")):
                        s_dir = tmp_dir / sub
                        if s_dir.exists():
                            shutil.copytree(s_dir, dest, dirs_exist_ok=True, copy_function=shutil.copyfile)
                    shutil.rmtree(tmp_dir, ignore_errors=True)
            else:
                if not self._is_sqlite(src):
                    messagebox.showerror("Restaurar", "O arquivo selecionado não é um banco de dados válido.")
                    return
                shutil.copyfile(src, db.db_path)
            # garante colunas novas caso o backup seja de versão antiga
            db._initialize_schema()
        except Exception as exc:
            log.exception("Erro na restauração")
            messagebox.showerror("Restaurar", f"Erro ao restaurar backup: {exc}")
            return

        messagebox.showinfo(
            "Restaurar",
            "Backup restaurado com sucesso.\n\nVocê será direcionado para o login para recarregar os dados.",
        )
        app = self.winfo_toplevel()
        if hasattr(app, "logout"):
            app.after(100, lambda: app.logout(save_settings=False))

    def _on_open_data_folder(self) -> None:
        if not open_path(app_paths.DATA_ROOT):
            messagebox.showinfo("Pasta de dados", str(app_paths.DATA_ROOT))
