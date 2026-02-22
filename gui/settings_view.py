import os
import shutil
from tkinter import filedialog, messagebox

import customtkinter as ctk
from .utils import setup_enter_navigation

from database import db
from utils.image_utils import create_circular_image


class SettingsView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        professor_var: ctk.StringVar,
        appearance_var: ctk.StringVar,
        color_theme_var: ctk.StringVar,
        refresh_var: ctk.StringVar,
        current_user: dict | None = None,
    ) -> None:
        super().__init__(master)

        self.professor_var = professor_var
        self.appearance_var = appearance_var
        self.color_theme_var = color_theme_var
        self.refresh_var = refresh_var
        self.current_user = current_user

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        title = ctk.CTkLabel(
            header_frame,
            text="Configurações",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(side="left")

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
        ctk.CTkLabel(scroll_geral, text="Preferências do Sistema", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=row, column=0, columnspan=2, padx=10, pady=(10, 10), sticky="w"
        )
        row += 1

        ctk.CTkLabel(scroll_geral, text="Nome do professor:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        entry_prof = ctk.CTkEntry(scroll_geral, textvariable=self.professor_var)
        entry_prof.grid(row=row, column=1, padx=10, pady=5, sticky="ew")

        row += 1
        ctk.CTkLabel(scroll_geral, text="Auto-atualização Dashboard (s):").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        self.entry_refresh = ctk.CTkEntry(scroll_geral, textvariable=self.refresh_var, width=100)
        self.entry_refresh.grid(row=row, column=1, padx=10, pady=5, sticky="w")

        row += 1
        ctk.CTkLabel(scroll_geral, text="Aparência", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=row, column=0, columnspan=2, padx=10, pady=(20, 10), sticky="w"
        )
        
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
        ctk.CTkLabel(scroll_geral, text="Manutenção de Dados", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=row, column=0, columnspan=2, padx=10, pady=(20, 10), sticky="w"
        )

        row += 1
        btn_frame = ctk.CTkFrame(scroll_geral, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        btn_backup = ctk.CTkButton(btn_frame, text="Criar Backup", command=self._on_backup, width=120)
        btn_backup.pack(side="left", padx=(0, 10))
        
        btn_restore = ctk.CTkButton(btn_frame, text="Restaurar Backup", command=self._on_restore, fg_color="#aa3333", hover_color="#992222", width=120)
        btn_restore.pack(side="left", padx=(0, 10))
        
        btn_open_folder = ctk.CTkButton(btn_frame, text="Abrir Pasta de Dados", command=self._on_open_data_folder, width=140, fg_color="gray")
        btn_open_folder.pack(side="left", padx=(0, 10))

        row += 1
        db_path_label = ctk.CTkLabel(scroll_geral, text=f"Caminho: {db.db_path}", font=ctk.CTkFont(size=10), text_color="gray")
        db_path_label.grid(row=row, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="w")

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
            
            self.entry_filtro_tel = ctk.CTkEntry(filter_frame, placeholder_text="Filtrar por telefone...")
            self.entry_filtro_tel.pack(side="left", fill="x", expand=True, padx=(0, 5))
            self.entry_filtro_tel.bind("<Return>", lambda e: self._load_users())
            
            ctk.CTkButton(filter_frame, text="🔍", width=40, command=self._load_users).pack(side="right")

            # Lista (Esquerda Corpo)
            self.scroll_users = ctk.CTkScrollableFrame(left_panel)
            self.scroll_users.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")

            # Form (Direita)
            form_user = ctk.CTkFrame(users_content)
            form_user.grid(row=0, column=1, rowspan=2, padx=(10, 0), pady=0, sticky="nsew")
            form_user.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(form_user, text="Dados do Usuário", font=ctk.CTkFont(size=16, weight="bold")).grid(
                row=0, column=0, columnspan=2, padx=10, pady=(15, 10), sticky="w"
            )

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
            
            btn_user_novo = ctk.CTkButton(btn_user_frame, text="+ Novo", command=self._on_user_novo, width=80, fg_color="#2ecc71", hover_color="#27ae60")
            btn_user_novo.pack(side="left", padx=(0, 5))
            
            btn_user_salvar = ctk.CTkButton(btn_user_frame, text="Salvar", command=self._on_user_salvar, width=80)
            btn_user_salvar.pack(side="left", padx=(0, 5))
            
            btn_user_desativar = ctk.CTkButton(btn_user_frame, text="Desativar", command=self._on_user_desativar, fg_color="#e67e22", hover_color="#d35400", width=80)
            btn_user_desativar.pack(side="right", padx=(5, 0))
            
            btn_user_excluir = ctk.CTkButton(btn_user_frame, text="Excluir", command=self._on_user_excluir, fg_color="#c0392b", hover_color="#922b21", width=80)
            btn_user_excluir.pack(side="right")

            self.selected_user_id: int | None = None
            self._load_users()
            
        setup_enter_navigation(self.tabs)

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
                query += " WHERE telefone LIKE ?"
                params.append(f"%{filtro_tel}%")
                
            query += " ORDER BY username"

            rows = db.fetch_all(query, tuple(params))
            
            if not rows:
                ctk.CTkLabel(self.scroll_users, text="Nenhum usuário.", text_color="gray").pack(pady=10)
                return

            for row in rows:
                self._create_user_card(row)

    def _create_user_card(self, row: dict) -> None:
        card = ctk.CTkFrame(self.scroll_users, fg_color=("gray90", "gray20"), corner_radius=6)
        card.pack(fill="x", pady=2, padx=2)
        
        # Frame interno para layout horizontal (Foto + Info)
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", padx=5, pady=5)
        
        # Foto
        foto_path = row["foto_perfil"]
        lbl_foto = ctk.CTkLabel(content, text="👤", width=36, height=36, fg_color="gray50", corner_radius=18)
        if foto_path:
            try:
                from pathlib import Path
                if Path(foto_path).exists():
                    pil_img = create_circular_image(foto_path, (72, 72)) # Dobro para HiDPI
                    if pil_img:
                        ctk_img = ctk.CTkImage(pil_img, size=(36, 36))
                        lbl_foto.configure(image=ctk_img, text="", fg_color="transparent")
            except Exception:
                pass
        lbl_foto.pack(side="left", padx=(0, 8))

        # Info Wrapper
        info_wrapper = ctk.CTkFrame(content, fg_color="transparent")
        info_wrapper.pack(side="left", fill="both", expand=True)

        status_color = "green" if row["ativo"] else "red"
        status_text = "Personal" if row["ativo"] else "Inativo"
        
        role_parts = []
        if row["is_admin"]:
            role_parts.append("ADMIN")
        else:
            role_parts.append("USER")
            
        if row["is_trial"]:
            role_parts.append("TRIAL")
            
        role_text = " | ".join(role_parts)
        
        header = ctk.CTkFrame(info_wrapper, fg_color="transparent")
        header.pack(fill="x", pady=(0, 0))
        
        lbl_user = ctk.CTkLabel(header, text=row["username"], font=ctk.CTkFont(size=13, weight="bold"))
        lbl_user.pack(side="left")
        
        lbl_role = ctk.CTkLabel(header, text=role_text, font=ctk.CTkFont(size=10, weight="bold"), text_color="gray")
        lbl_role.pack(side="right")
        
        lbl_nome = ctk.CTkLabel(info_wrapper, text=row["nome"] or "-", font=ctk.CTkFont(size=12))
        lbl_nome.pack(fill="x", anchor="w")
        
        footer = ctk.CTkFrame(info_wrapper, fg_color="transparent")
        footer.pack(fill="x", pady=(2, 0))
        
        lbl_status = ctk.CTkLabel(footer, text=status_text, font=ctk.CTkFont(size=11), text_color=status_color)
        lbl_status.pack(side="left")
        
        if row["telefone"]:
             ctk.CTkLabel(footer, text=f" | Tel: {row['telefone']}", font=ctk.CTkFont(size=11), text_color="gray").pack(side="left")
        
        if row["cref"]:
            ctk.CTkLabel(footer, text=f"CREF: {row['cref']}", font=ctk.CTkFont(size=11), text_color="gray").pack(side="right")

        # Bind events
        for w in (card, content, lbl_foto, info_wrapper, header, lbl_user, lbl_nome, footer, lbl_status, lbl_role):
            w.bind("<Button-1>", lambda e, uid=row["id"]: self._on_user_card_click(uid))
            w.bind("<Enter>", lambda e, c=card: c.configure(border_width=1, border_color="gray50"))
            w.bind("<Leave>", lambda e, c=card: c.configure(border_width=0))

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
        source_path = db.db_path
        if not source_path.exists():
            messagebox.showerror(
                "Backup",
                "Arquivo de banco de dados não encontrado.",
            )
            return

        default_name = source_path.name
        dest_path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("Banco de dados SQLite", "*.db"), ("Todos os arquivos", "*.*")],
            initialfile=default_name,
            title="Salvar backup do banco de dados",
        )
        if not dest_path:
            return

        try:
            shutil.copy(str(source_path), dest_path)
        except Exception as exc:
            messagebox.showerror(
                "Backup",
                f"Erro ao criar backup: {exc}",
            )
            return

        messagebox.showinfo(
            "Backup",
            "Backup do banco de dados criado com sucesso.",
        )

    def _on_restore(self) -> None:
        confirm = messagebox.askyesno(
            "Restaurar banco de dados",
            "Esta ação vai substituir o banco de dados atual.\n"
            "Recomenda-se criar um backup antes.\n\n"
            "Deseja continuar?",
        )
        if not confirm:
            return

        source_path = filedialog.askopenfilename(
            filetypes=[("Banco de dados SQLite", "*.db"), ("Todos os arquivos", "*.*")],
            title="Selecionar arquivo de backup do banco de dados",
        )
        if not source_path:
            return

        dest_path = db.db_path
        try:
            shutil.copy(source_path, str(dest_path))
        except Exception as exc:
            messagebox.showerror(
                "Restaurar banco de dados",
                f"Erro ao restaurar banco de dados: {exc}",
            )
            return

        messagebox.showinfo(
            "Restaurar banco de dados",
            "Banco de dados restaurado com sucesso.\n"
            "Feche e abra o sistema para ver os dados atualizados.",
        )

    def _on_open_data_folder(self) -> None:
        folder = db.db_path.parent
        try:
            if os.name == "nt":
                os.startfile(folder)
            else:
                messagebox.showinfo("Pasta de dados", str(folder))
        except Exception as exc:
            messagebox.showerror(
                "Pasta de dados",
                f"Não foi possível abrir a pasta: {exc}",
            )

