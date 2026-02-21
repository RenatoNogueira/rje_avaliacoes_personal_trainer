from pathlib import Path
from tkinter import filedialog, messagebox
import json
import datetime

import customtkinter as ctk
from .utils import setup_enter_navigation, create_tooltip, show_toast

from database import db
from reports.treino_pdf import gerar_pdf_treino


class TreinosView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        professor_var: ctk.StringVar | None = None,
        get_current_user=None,
    ) -> None:
        super().__init__(master)

        self.selected_treino_id = None
        self.selected_exercicio_id = None
        self.professor_nome_var = professor_var or ctk.StringVar()
        self.get_current_user = get_current_user or (lambda: None)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        title = ctk.CTkLabel(
            header_frame,
            text="Montagem de Treinos",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(side="left")

        # Container Principal
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        content.grid_columnconfigure(0, weight=1, minsize=300)  # Lista (30%)
        content.grid_columnconfigure(1, weight=2, minsize=400)  # Detalhes (70%)
        content.grid_rowconfigure(0, weight=1)

        # --- Coluna da Esquerda: Filtros e Lista ---
        left_panel = ctk.CTkFrame(content)
        left_panel.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        left_panel.grid_rowconfigure(2, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        # Filtros
        filter_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        filter_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        filter_frame.grid_columnconfigure(0, weight=1)

        self.entry_filtro_aluno = ctk.CTkEntry(filter_frame, placeholder_text="🔍 Buscar aluno...")
        self.entry_filtro_aluno.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="ew")
        
        self.combo_filtro_usuario = ctk.CTkComboBox(filter_frame, values=["Todos os profissionais"])
        self.combo_filtro_usuario.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="ew")

        btn_filtrar = ctk.CTkButton(filter_frame, text="Filtrar", width=80, command=self.load_treinos)
        btn_filtrar.grid(row=0, column=2, padx=(5, 0), pady=5, sticky="e")

        # Lista (Scrollable)
        self.scroll_list_treinos = ctk.CTkScrollableFrame(left_panel)
        self.scroll_list_treinos.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # --- Coluna da Direita: Formulário ---
        right_panel = ctk.CTkFrame(content)
        right_panel.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(0, weight=1)

        form_scroll = ctk.CTkScrollableFrame(right_panel, fg_color="transparent")
        form_scroll.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        form_scroll.grid_columnconfigure(1, weight=1)

        # Seção 1: Dados do Treino
        row = 0
        ctk.CTkLabel(form_scroll, text="Dados do Treino", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=row, column=0, columnspan=2, padx=10, pady=(20, 10), sticky="w"
        )
        row += 1

        ctk.CTkLabel(form_scroll, text="Professor:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        self.entry_professor = ctk.CTkEntry(form_scroll, textvariable=self.professor_nome_var)
        self.entry_professor.grid(row=row, column=1, padx=10, pady=5, sticky="ew")

        row += 1
        ctk.CTkLabel(form_scroll, text="Aluno:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        self.combo_aluno = ctk.CTkComboBox(form_scroll, values=[])
        self.combo_aluno.grid(row=row, column=1, padx=10, pady=5, sticky="ew")

        row += 1
        ctk.CTkLabel(form_scroll, text="Nome do Treino:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        self.entry_nome_treino = ctk.CTkEntry(form_scroll)
        self.entry_nome_treino.grid(row=row, column=1, padx=10, pady=5, sticky="ew")

        row += 1
        ctk.CTkLabel(form_scroll, text="Objetivo:").grid(row=row, column=0, padx=10, pady=5, sticky="e")
        self.entry_objetivo = ctk.CTkEntry(form_scroll)
        self.entry_objetivo.grid(row=row, column=1, padx=10, pady=5, sticky="ew")

        row += 1
        # Metadados
        meta_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        meta_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        meta_frame.grid_columnconfigure(0, weight=1)
        meta_frame.grid_columnconfigure(1, weight=1)
        self.label_criado_por = ctk.CTkLabel(meta_frame, text="Criado por: -", font=ctk.CTkFont(size=11), text_color="gray")
        self.label_criado_por.grid(row=0, column=0, sticky="w")
        self.label_atualizado_por = ctk.CTkLabel(meta_frame, text="Última atualização: -", font=ctk.CTkFont(size=11), text_color="gray")
        self.label_atualizado_por.grid(row=0, column=1, sticky="e")

        # Seção 2: Exercícios
        row += 1
        ctk.CTkLabel(form_scroll, text="Exercícios", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=row, column=0, columnspan=2, padx=10, pady=(20, 10), sticky="w"
        )
        
        row += 1
        # Lista de Exercícios (Scrollable interna)
        self.scroll_exercicios = ctk.CTkScrollableFrame(form_scroll, height=200, label_text="Lista de Exercícios")
        self.scroll_exercicios.grid(row=row, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        
        row += 1
        # Formulário de Exercício (Card para adicionar/editar)
        ex_form = ctk.CTkFrame(form_scroll)
        ex_form.grid(row=row, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        ex_form.grid_columnconfigure((1, 3, 5), weight=1)

        ctk.CTkLabel(ex_form, text="Exercício:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_nome_exercicio = ctk.CTkEntry(ex_form)
        self.entry_nome_exercicio.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky="ew")
        
        btn_catalogo = ctk.CTkButton(ex_form, text="🔍 Catálogo", width=80, command=self.on_buscar_catalogo, fg_color="#f39c12", hover_color="#d35400")
        btn_catalogo.grid(row=0, column=4, columnspan=2, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(ex_form, text="Séries:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.entry_series = ctk.CTkEntry(ex_form, width=60)
        self.entry_series.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(ex_form, text="Reps:").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.entry_reps = ctk.CTkEntry(ex_form, width=60)
        self.entry_reps.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(ex_form, text="Carga:").grid(row=1, column=4, padx=5, pady=5, sticky="e")
        self.entry_carga = ctk.CTkEntry(ex_form, width=60)
        self.entry_carga.grid(row=1, column=5, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(ex_form, text="Descanso:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.entry_descanso = ctk.CTkEntry(ex_form, width=80)
        self.entry_descanso.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(ex_form, text="Divisão:").grid(row=2, column=2, padx=5, pady=5, sticky="e")
        self.combo_divisao = ctk.CTkComboBox(ex_form, values=["A", "B", "C", "D"], width=60)
        self.combo_divisao.grid(row=2, column=3, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(ex_form, text="Obs:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.entry_obs = ctk.CTkEntry(ex_form)
        self.entry_obs.grid(row=3, column=1, columnspan=5, padx=5, pady=5, sticky="ew")

        # Botões de Exercício
        btn_ex_frame = ctk.CTkFrame(ex_form, fg_color="transparent")
        btn_ex_frame.grid(row=4, column=0, columnspan=6, padx=5, pady=10, sticky="ew")
        
        btn_novo_ex = ctk.CTkButton(btn_ex_frame, text="Limpar Campos", width=100, command=self.on_novo_exercicio, fg_color="gray")
        btn_novo_ex.pack(side="left", padx=5)
        
        btn_salvar_ex = ctk.CTkButton(btn_ex_frame, text="Adicionar/Atualizar Exercício", command=self.on_salvar_exercicio)
        btn_salvar_ex.pack(side="left", padx=5, fill="x", expand=True)
        
        btn_del_ex = ctk.CTkButton(btn_ex_frame, text="Remover", width=100, command=self.on_excluir_exercicio, fg_color="#e74c3c", hover_color="#c0392b")
        btn_del_ex.pack(side="right", padx=5)

        setup_enter_navigation(form_scroll)

        # Botões de Ação (Footer)
        actions_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        actions_frame.grid(row=1, column=0, padx=15, pady=15, sticky="ew")
        actions_frame.grid_columnconfigure(0, weight=1)

        btn_novo_treino = ctk.CTkButton(
            actions_frame,
            text="+ Novo Treino",
            command=self.on_novo_treino,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            width=80
        )
        btn_novo_treino.pack(side="left", padx=(0, 10))
        create_tooltip(btn_novo_treino, "Criar uma nova ficha de treino")

        btn_salvar_treino = ctk.CTkButton(
            actions_frame,
            text="💾 Salvar",
            command=self.on_salvar_treino,
            width=80
        )
        btn_salvar_treino.pack(side="left", padx=(0, 10))
        create_tooltip(btn_salvar_treino, "Salvar treino atual")

        btn_pdf = ctk.CTkButton(
            actions_frame,
            text="📄 PDF",
            command=self.on_gerar_pdf,
            fg_color="#3498db",
            hover_color="#2980b9",
            width=80
        )
        btn_pdf.pack(side="left", padx=(0, 10))
        create_tooltip(btn_pdf, "Gerar ficha de treino em PDF")

        btn_excluir_treino = ctk.CTkButton(
            actions_frame,
            text="🗑️ Excluir",
            command=self.on_excluir_treino,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            width=80
        )
        btn_excluir_treino.pack(side="right")
        create_tooltip(btn_excluir_treino, "Excluir treino permanentemente")

        self.load_alunos()
        self._load_usuarios_filtro()
        self.on_novo_treino()
        self.load_treinos()

    def _load_usuarios_filtro(self) -> None:
        rows = db.fetch_all(
            """
            SELECT id, username, nome
            FROM usuarios
            WHERE ativo = 1
            ORDER BY nome, username
            """
        )
        values = ["Todos os profissionais"]
        for row in rows:
            texto = row["nome"] or row["username"]
            values.append(f"{row['id']:04d} - {texto}")
        self.combo_filtro_usuario.configure(values=values)
        if values:
            self.combo_filtro_usuario.set(values[0])

    def load_alunos(self) -> None:
        rows = db.fetch_all(
            """
            SELECT id, nome
            FROM alunos
            ORDER BY nome
            """
        )
        values = [f"{row['id']:04d} - {row['nome']}" for row in rows]
        self.combo_aluno.configure(values=values)
        if values:
            self.combo_aluno.set(values[0])
        else:
            self.combo_aluno.set("")

    def _get_selected_aluno_id(self) -> int | None:
        value = self.combo_aluno.get().strip()
        if not value:
            return None
        try:
            id_str = value.split("-")[0].strip()
            return int(id_str)
        except ValueError:
            return None

    def load_treinos(self) -> None:
        # Limpa lista
        for widget in self.scroll_list_treinos.winfo_children():
            widget.destroy()

        filtro = self.entry_filtro_aluno.get().strip()
        usuario_value = self.combo_filtro_usuario.get().strip() if hasattr(self, "combo_filtro_usuario") else ""
        usuario_id = None
        if usuario_value and not usuario_value.startswith("Todos"):
            try:
                id_str = usuario_value.split("-")[0].strip()
                usuario_id = int(id_str)
            except Exception:
                usuario_id = None
        
        user = self.get_current_user() if self.get_current_user else None
        is_admin = bool(user and user.get("is_admin"))
        user_id_logado = user.get("id") if user else None

        params: list[str | int] = []
        query = """
            SELECT t.id, t.nome_do_treino, t.objetivo, t.data_criacao,
                   al.nome AS nome_aluno,
                   u.username AS username_criacao, u.nome AS nome_criacao
            FROM treinos t
            JOIN alunos al ON al.id = t.id_aluno
            LEFT JOIN usuarios u ON u.id = t.id_usuario_criacao
            WHERE 1=1
        """

        # Se NÃO for admin, filtra apenas treinos criados pelo usuário
        if not is_admin and user_id_logado:
            query += " AND t.id_usuario_criacao = ?"
            params.append(user_id_logado)

        if filtro:
            query += " AND al.nome LIKE ?"
            params.append(f"%{filtro}%")
            
        # Se um filtro específico de usuário foi selecionado (e o usuário atual for admin, ou filtro redundante)
        if usuario_id is not None:
             # Se não for admin, o filtro acima já restringiu. Se for admin, aplica filtro da UI.
             if is_admin:
                query += " AND t.id_usuario_criacao = ?"
                params.append(usuario_id)

        query += " ORDER BY t.data_criacao DESC"

        rows = db.fetch_all(query, tuple(params))

        if not rows:
            ctk.CTkLabel(self.scroll_list_treinos, text="Nenhum treino encontrado.", text_color="gray").pack(pady=20)
            return

        for row in rows:
            self._create_treino_card(row)

    def _create_treino_card(self, row: dict) -> None:
        card = ctk.CTkFrame(self.scroll_list_treinos, fg_color=("gray90", "gray20"), corner_radius=8)
        card.pack(fill="x", pady=4, padx=2)

        data_br = row["data_criacao"]
        try:
            if row["data_criacao"]:
                d = datetime.date.fromisoformat(row["data_criacao"].split(" ")[0])
                data_br = d.strftime("%d/%m/%Y")
        except Exception:
            pass

        # Header: Nome do Treino
        lbl_treino = ctk.CTkLabel(card, text=row["nome_do_treino"], font=ctk.CTkFont(size=14, weight="bold"))
        lbl_treino.pack(fill="x", padx=10, pady=(8, 2), anchor="w")

        # Subtitle: Aluno
        lbl_aluno = ctk.CTkLabel(card, text=f"Aluno: {row['nome_aluno']}", font=ctk.CTkFont(size=12))
        lbl_aluno.pack(fill="x", padx=10, pady=(0, 2), anchor="w")

        # Footer: Data e Prof
        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.pack(fill="x", padx=10, pady=(0, 8))
        
        lbl_data = ctk.CTkLabel(footer, text=data_br, font=ctk.CTkFont(size=11), text_color="gray")
        lbl_data.pack(side="left")
        
        prof_nome = row["nome_criacao"] or row["username_criacao"] or ""
        if prof_nome:
            lbl_prof = ctk.CTkLabel(footer, text=f"Prof: {prof_nome}", font=ctk.CTkFont(size=11), text_color="gray")
            lbl_prof.pack(side="right")

        # Bind events
        for w in (card, lbl_treino, lbl_aluno, footer, lbl_data):
            w.bind("<Button-1>", lambda e, tid=row["id"]: self.load_treino_details(tid))
            w.bind("<Enter>", lambda e, c=card: c.configure(border_width=1, border_color="gray50"))
            w.bind("<Leave>", lambda e, c=card: c.configure(border_width=0))
        if prof_nome and 'lbl_prof' in locals():
             lbl_prof.bind("<Button-1>", lambda e, tid=row["id"]: self.load_treino_details(tid))

    def load_treino_details(self, treino_id: int) -> None:
        self.selected_treino_id = treino_id
        row = db.fetch_one(
            """
            SELECT t.id, t.id_aluno, t.nome_do_treino, t.objetivo, t.data_criacao,
                   t.id_usuario_criacao, t.id_usuario_atualizacao,
                   al.nome AS nome_aluno,
                   uc.username AS username_criacao, uc.nome AS nome_criacao,
                   uu.username AS username_atualizacao, uu.nome AS nome_atualizacao
            FROM treinos t
            JOIN alunos al ON al.id = t.id_aluno
            LEFT JOIN usuarios uc ON uc.id = t.id_usuario_criacao
            LEFT JOIN usuarios uu ON uu.id = t.id_usuario_atualizacao
            WHERE t.id = ?
            """,
            (self.selected_treino_id,),
        )
        if row is None:
            return

        aluno_str = f"{row['id_aluno']:04d} - {row['nome_aluno']}"
        self.combo_aluno.set(aluno_str)

        self.entry_nome_treino.delete(0, "end")
        self.entry_nome_treino.insert(0, row["nome_do_treino"] or "")

        self.entry_objetivo.delete(0, "end")
        self.entry_objetivo.insert(0, row["objetivo"] or "")

        criado = row["nome_criacao"] or row["username_criacao"] or "-"
        atualizado = row["nome_atualizacao"] or row["username_atualizacao"] or "-"
        self.label_criado_por.configure(text=f"Criado por: {criado}")
        self.label_atualizado_por.configure(text=f"Última atualização: {atualizado}")

        self.load_exercicios()

    def on_buscar_catalogo(self) -> None:
        if hasattr(self, "catalog_window") and self.catalog_window.winfo_exists():
            try:
                self.catalog_window.deiconify()
                self.catalog_window.state("normal")
                self.catalog_window.lift()
                self.catalog_window.focus_force()
                self.catalog_window.attributes("-topmost", True)
                self.catalog_window.after(200, lambda: self.catalog_window.attributes("-topmost", False))
            except Exception:
                pass
            return

        self.catalog_page_size = 100
        self.catalog_offset = 0
        self.catalog_has_more = True
        self.catalog_current_term = ""
        self.catalog_selected_ids = set()

        self.catalog_window = ctk.CTkToplevel(self)
        self.catalog_window.title("Catálogo de exercícios")
        self.catalog_window.geometry("800x500")
        try:
            self.catalog_window.transient(self.winfo_toplevel())
            self.catalog_window.lift()
            self.catalog_window.focus_force()
            self.catalog_window.grab_set()
            self.catalog_window.attributes("-topmost", True)
            self.catalog_window.after(200, lambda: self.catalog_window.attributes("-topmost", False))
        except Exception:
            pass

        frame = ctk.CTkFrame(self.catalog_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="Buscar:").grid(
            row=0, column=0, padx=(0, 5), pady=5, sticky="e"
        )
        self.entry_catalog_busca = ctk.CTkEntry(frame)
        self.entry_catalog_busca.grid(
            row=0, column=1, padx=(0, 5), pady=5, sticky="ew"
        )

        btn_buscar = ctk.CTkButton(
            frame,
            text="Buscar",
            width=80,
            command=self.load_catalog_results,
        )
        btn_buscar.grid(row=0, column=2, padx=(5, 0), pady=5, sticky="w")

        self.catalog_results = ctk.CTkScrollableFrame(frame)
        self.catalog_results.grid(
            row=1, column=0, columnspan=3, padx=0, pady=(5, 0), sticky="nsew"
        )
        self.catalog_results.grid_columnconfigure(0, weight=1)
        self.catalog_checkboxes = {}

        self.entry_catalog_busca.bind(
            "<KeyRelease>",
            lambda event: self.load_catalog_results(reset=True),
            add="+",
        )
        self.entry_catalog_busca.bind("<Return>", lambda event: self._catalog_accept_first())

        action_frame = ctk.CTkFrame(frame)
        action_frame.grid(row=2, column=0, columnspan=3, padx=0, pady=(6, 0), sticky="ew")
        action_frame.grid_columnconfigure((0, 1), weight=1)
        btn_select = ctk.CTkButton(
            action_frame,
            text="Selecionar",
            command=self._catalog_accept_first,
        )
        btn_select.grid(row=0, column=0, padx=5, pady=0, sticky="e")
        btn_select_multi = ctk.CTkButton(
            action_frame,
            text="Adicionar selecionados",
            command=self._catalog_add_selected_to_treino,
        )
        btn_select_multi.grid(row=0, column=1, padx=5, pady=0, sticky="w")

        self.catalog_window.focus_set()
        self.load_catalog_results(reset=True)

    def load_catalog_results(self, reset: bool = False) -> None:
        termo = self.entry_catalog_busca.get().strip().lower()

        if (
            reset
            or not hasattr(self, "catalog_current_term")
            or termo != self.catalog_current_term
        ):
            self.catalog_current_term = termo
            self.catalog_selected_ids = set()
        for child in self.catalog_results.winfo_children():
            child.destroy()

        if not termo:
            ctk.CTkLabel(
                self.catalog_results,
                text="Digite um termo para buscar exercícios no catálogo.",
            ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
            return

        filtro_like = f"%{termo}%"
        rows = db.fetch_all(
            """
            SELECT id, raw_json
            FROM exercicios_catalogo
            WHERE lower(raw_json) LIKE ?
            ORDER BY id
            LIMIT 100
            """,
            (filtro_like,),
        )

        if not rows:
            ctk.CTkLabel(
                self.catalog_results,
                text="Nenhum exercício encontrado.",
            ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
            return

        self.catalog_checkboxes = {}
        for i, row in enumerate(rows):
            try:
                data = json.loads(row["raw_json"])
            except Exception:
                continue

            nome = str(data.get("name") or "")
            
            # Adaptação para o novo JSON
            category = str(data.get("category") or "")
            
            primary_muscles = data.get("primaryMuscles")
            if isinstance(primary_muscles, list):
                musculos = ", ".join(primary_muscles)
            else:
                musculos = str(primary_muscles or "")
                
            equipment = str(data.get("equipment") or "")

            detalhes = " | ".join(
                item
                for item in (category, musculos, equipment)
                if item
            )
            line = f"{row['id']:05d} | {nome}"
            if detalhes:
                line += f" | {detalhes}"

            chk = ctk.CTkCheckBox(
                self.catalog_results,
                text=line,
                command=lambda cid=row["id"]: self._on_catalog_checkbox(cid),
            )
            if row["id"] in self.catalog_selected_ids:
                chk.select()
            chk.grid(row=i, column=0, padx=0, pady=(0, 2), sticky="w")
            self.catalog_checkboxes[row["id"]] = chk

    def _on_catalog_checkbox(self, catalog_id: int) -> None:
        if not hasattr(self, "catalog_selected_ids"):
            self.catalog_selected_ids = set()
        widget = self.catalog_checkboxes.get(catalog_id)
        if widget is None:
            return
        if widget.get():
            self.catalog_selected_ids.add(catalog_id)
        else:
            self.catalog_selected_ids.discard(catalog_id)

    def _catalog_accept_first(self) -> None:
        termo = self.entry_catalog_busca.get().strip().lower()
        if termo:
            filtro_like = f"%{termo}%"
            row = db.fetch_one(
                """
                SELECT id, raw_json
                FROM exercicios_catalogo
                WHERE lower(raw_json) LIKE ?
                ORDER BY id
                LIMIT 1
                """,
                (filtro_like,),
            )
        else:
            row = db.fetch_one(
                """
                SELECT id, raw_json
                FROM exercicios_catalogo
                ORDER BY id
                LIMIT 1
                """
            )
        if row is None:
            return
        try:
            data = json.loads(row["raw_json"])
        except Exception:
            return
        nome = str(data.get("name") or "")
        
        # Adaptação para o novo JSON
        primary_muscles = data.get("primaryMuscles")
        musculos = ""
        if isinstance(primary_muscles, list):
            musculos = ", ".join(primary_muscles)
        elif primary_muscles:
            musculos = str(primary_muscles)
            
        category = str(data.get("category") or "")
        
        obs_text = " | ".join(filter(None, [category, musculos]))
        
        if nome:
            self.entry_nome_exercicio.delete(0, "end")
            self.entry_nome_exercicio.insert(0, nome)
        if obs_text:
            self.entry_obs.delete(0, "end")
            self.entry_obs.insert(0, obs_text)
        try:
            self.catalog_window.destroy()
        except Exception:
            pass

    def _catalog_add_selected_to_treino(self) -> None:
        if not getattr(self, "catalog_selected_ids", None):
            messagebox.showwarning(
                "Treinos",
                "Selecione um ou mais exercícios no catálogo clicando nas linhas.",
            )
            return

        if self.selected_treino_id is None:
            self.on_salvar_treino()
            if self.selected_treino_id is None:
                return

        series = self.entry_series.get().strip() or None
        reps = self.entry_reps.get().strip() or None
        carga = self.entry_carga.get().strip() or None
        descanso = self.entry_descanso.get().strip() or None
        obs_base = self.entry_obs.get().strip() or None
        divisao = self.combo_divisao.get().strip() or "A"

        for catalog_id in sorted(self.catalog_selected_ids):
            row = db.fetch_one(
                """
                SELECT raw_json
                FROM exercicios_catalogo
                WHERE id = ?
                """,
                (catalog_id,),
            )
            if row is None:
                continue
            try:
                data = json.loads(row["raw_json"])
            except Exception:
                continue
            nome = str(data.get("name") or "")
            if not nome:
                continue
            db.execute(
                """
                INSERT INTO exercicios_treino
                    (id_treino, nome_exercicio, series, repeticoes,
                     carga, descanso, observacoes, divisao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.selected_treino_id,
                    nome,
                    series,
                    reps,
                    carga,
                    descanso,
                    obs_base,
                    divisao,
                ),
                commit=True,
            )

        self.load_exercicios()

    def on_novo_treino(self) -> None:
        self.selected_treino_id = None
        self.selected_exercicio_id = None

        if self.combo_aluno.cget("values"):
            self.combo_aluno.set(self.combo_aluno.cget("values")[0])
        else:
            self.combo_aluno.set("")

        self.entry_nome_treino.delete(0, "end")
        self.entry_objetivo.delete(0, "end")

        self.load_exercicios()

        self.on_novo_exercicio()
        if hasattr(self, "label_criado_por"):
            self.label_criado_por.configure(text="Criado por: -")
        if hasattr(self, "label_atualizado_por"):
            self.label_atualizado_por.configure(text="Última atualização: -")

    def on_salvar_treino(self) -> None:
        id_aluno = self._get_selected_aluno_id()
        if id_aluno is None:
            messagebox.showwarning("Treinos", "Selecione um aluno para o treino.")
            return

        nome_treino = self.entry_nome_treino.get().strip()
        if not nome_treino:
            messagebox.showwarning("Treinos", "Informe o nome do treino.")
            return

        objetivo = self.entry_objetivo.get().strip() or None

        user = self.get_current_user() if self.get_current_user else None
        user_id = None
        if user is not None:
            try:
                user_id = int(user.get("id"))
            except Exception:
                user_id = None

        if self.selected_treino_id is None:
            db.execute(
                """
                INSERT INTO treinos
                    (id_aluno, nome_do_treino, objetivo,
                     id_usuario_criacao, id_usuario_atualizacao)
                VALUES (?, ?, ?, ?, ?)
                """,
                (id_aluno, nome_treino, objetivo, user_id, user_id),
                commit=True,
            )
            row = db.fetch_one(
                "SELECT last_insert_rowid() AS id",
                (),
            )
            if row is not None:
                self.selected_treino_id = int(row["id"])
        else:
            db.execute(
                """
                UPDATE treinos
                SET id_aluno = ?, nome_do_treino = ?, objetivo = ?,
                    id_usuario_atualizacao = ?
                WHERE id = ?
                """,
                (id_aluno, nome_treino, objetivo, user_id, self.selected_treino_id),
                commit=True,
            )

        self.load_treinos()
        self.load_exercicios()
        messagebox.showinfo("Treinos", "Treino salvo com sucesso.")

    def on_excluir_treino(self) -> None:
        if self.selected_treino_id is None:
            show_toast(self, "Selecione um treino para excluir.", 3000)
            return
        
        if not messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja excluir este treino e todos os seus exercícios?"):
            return
            
        show_toast(self, "Excluindo treino...", 1500)
        self.after(500, self._confirm_excluir)

    def _confirm_excluir(self):
        db.execute("DELETE FROM exercicios_treino WHERE id_treino = ?", (self.selected_treino_id,), commit=False)
        db.execute("DELETE FROM treinos WHERE id = ?", (self.selected_treino_id,), commit=True)
        self.on_novo_treino()
        self.load_treinos()
        messagebox.showinfo("Treinos", "Treino excluído com sucesso.")

    def load_exercicios(self) -> None:
        # Limpa lista
        for widget in self.scroll_exercicios.winfo_children():
            widget.destroy()

        if self.selected_treino_id is None:
            ctk.CTkLabel(self.scroll_exercicios, text="Salve o treino antes de adicionar exercícios.", text_color="gray").pack(pady=10)
            return

        rows = db.fetch_all(
            """
            SELECT id, nome_exercicio, series, repeticoes, carga, descanso, divisao
            FROM exercicios_treino
            WHERE id_treino = ?
            ORDER BY divisao, id
            """,
            (self.selected_treino_id,),
        )

        if not rows:
            ctk.CTkLabel(self.scroll_exercicios, text="Nenhum exercício cadastrado.", text_color="gray").pack(pady=10)
            return

        for row in rows:
            self._create_exercicio_row(row)

    def _create_exercicio_row(self, row: dict) -> None:
        frame = ctk.CTkFrame(self.scroll_exercicios, fg_color=("gray95", "gray25"))
        frame.pack(fill="x", pady=2, padx=2)

        # Layout: [Div] Nome | Séries x Reps | Carga | Descanso | [X]
        # Usando grid dentro do frame
        frame.grid_columnconfigure(1, weight=1)
        
        # Divisão Badge
        div = row["divisao"] or "A"
        lbl_div = ctk.CTkLabel(frame, text=div, width=30, height=30, fg_color="#3498db", text_color="white", corner_radius=6)
        lbl_div.grid(row=0, column=0, padx=5, pady=5)

        info_text = f"{row['nome_exercicio']}"
        details = []
        if row['series'] or row['repeticoes']:
            details.append(f"{row['series'] or '?'}x{row['repeticoes'] or '?'}")
        if row['carga']:
            details.append(f"{row['carga']}")
        if row['descanso']:
            details.append(f"Desc: {row['descanso']}")
            
        if details:
            info_text += f"  ({ ' | '.join(details) })"

        lbl = ctk.CTkLabel(frame, text=info_text, anchor="w")
        lbl.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Botão Excluir na linha
        btn_del = ctk.CTkButton(
            frame, 
            text="🗑️", 
            width=30, 
            height=30, 
            fg_color="transparent", 
            text_color="#c0392b", 
            hover_color=("gray85", "gray30"),
            command=lambda eid=row["id"]: self._on_delete_exercicio_row(eid)
        )
        btn_del.grid(row=0, column=2, padx=5, pady=5)
        create_tooltip(btn_del, "Remover exercício")

        # Bind click
        for w in (frame, lbl, lbl_div):
            w.bind("<Button-1>", lambda e, eid=row["id"]: self.load_exercicio_details(eid))
            w.bind("<Enter>", lambda e, c=frame: c.configure(fg_color=("gray90", "gray30")))
            w.bind("<Leave>", lambda e, c=frame: c.configure(fg_color=("gray95", "gray25")))

    def _on_delete_exercicio_row(self, exercicio_id: int) -> None:
        if not messagebox.askyesno("Confirmar", "Deseja remover este exercício?"):
            return
            
        db.execute(
            "DELETE FROM exercicios_treino WHERE id = ?",
            (exercicio_id,),
            commit=True,
        )
        
        # Se o exercício excluído estava sendo editado, limpa o form
        if self.selected_exercicio_id == exercicio_id:
            self.on_novo_exercicio()
            
        self.load_exercicios()

    def load_exercicio_details(self, exercicio_id: int) -> None:
        self.selected_exercicio_id = exercicio_id
        row = db.fetch_one(
            """
            SELECT id, nome_exercicio, series, repeticoes, carga, descanso, observacoes, divisao
            FROM exercicios_treino
            WHERE id = ?
            """,
            (self.selected_exercicio_id,),
        )
        if row is None:
            return

        self.entry_nome_exercicio.delete(0, "end")
        self.entry_nome_exercicio.insert(0, row["nome_exercicio"] or "")

        self.entry_series.delete(0, "end")
        self.entry_series.insert(0, row["series"] or "")

        self.entry_reps.delete(0, "end")
        self.entry_reps.insert(0, row["repeticoes"] or "")

        self.entry_carga.delete(0, "end")
        self.entry_carga.insert(0, row["carga"] or "")

        self.entry_descanso.delete(0, "end")
        self.entry_descanso.insert(0, row["descanso"] or "")
        
        div = row["divisao"] or "A"
        self.combo_divisao.set(div)

        self.entry_obs.delete(0, "end")
        self.entry_obs.insert(0, row["observacoes"] or "")

    def on_novo_exercicio(self) -> None:
        self.selected_exercicio_id = None
        self.entry_nome_exercicio.delete(0, "end")
        self.entry_series.delete(0, "end")
        self.entry_reps.delete(0, "end")
        self.entry_carga.delete(0, "end")
        self.entry_descanso.delete(0, "end")
        self.entry_obs.delete(0, "end")
        # Mantém a última divisão selecionada
        # self.combo_divisao.set("A") 

    def on_salvar_exercicio(self) -> None:
        if self.selected_treino_id is None:
            self.on_salvar_treino()
            if self.selected_treino_id is None:
                return

        nome_exercicio = self.entry_nome_exercicio.get().strip()
        if not nome_exercicio:
            messagebox.showwarning("Treinos", "Informe o nome do exercício.")
            return

        series = self.entry_series.get().strip() or None
        reps = self.entry_reps.get().strip() or None
        carga = self.entry_carga.get().strip() or None
        descanso = self.entry_descanso.get().strip() or None
        obs = self.entry_obs.get().strip() or None
        divisao = self.combo_divisao.get().strip() or "A"

        if self.selected_exercicio_id is None:
            db.execute(
                """
                INSERT INTO exercicios_treino
                    (id_treino, nome_exercicio, series, repeticoes,
                     carga, descanso, observacoes, divisao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.selected_treino_id,
                    nome_exercicio,
                    series,
                    reps,
                    carga,
                    descanso,
                    obs,
                    divisao,
                ),
                commit=True,
            )
        else:
            db.execute(
                """
                UPDATE exercicios_treino
                SET nome_exercicio = ?, series = ?, repeticoes = ?,
                    carga = ?, descanso = ?, observacoes = ?, divisao = ?
                WHERE id = ?
                """,
                (
                    nome_exercicio,
                    series,
                    reps,
                    carga,
                    descanso,
                    obs,
                    divisao,
                    self.selected_exercicio_id,
                ),
                commit=True,
            )

        self.load_exercicios()
        messagebox.showinfo("Treinos", "Exercício salvo no treino com sucesso.")

    def on_excluir_exercicio(self) -> None:
        if self.selected_exercicio_id is None:
            return

        db.execute(
            "DELETE FROM exercicios_treino WHERE id = ?",
            (self.selected_exercicio_id,),
            commit=True,
        )

        self.on_novo_exercicio()
        self.load_exercicios()
        messagebox.showinfo("Treinos", "Exercício removido do treino com sucesso.")

    def on_gerar_pdf(self) -> None:
        if self.selected_treino_id is None:
            messagebox.showwarning(
                "Treinos",
                "Selecione um treino na lista para gerar a ficha em PDF.",
            )
            return

        treino = db.fetch_one(
            """
            SELECT t.id, t.id_aluno, t.nome_do_treino, t.objetivo, t.data_criacao
            FROM treinos t
            WHERE t.id = ?
            """,
            (self.selected_treino_id,),
        )
        if treino is None:
            return

        aluno = db.fetch_one(
            "SELECT id, nome, cpf, cep FROM alunos WHERE id = ?",
            (treino["id_aluno"],),
        )
        if aluno is None:
            return

        exercicios_rows = db.fetch_all(
            """
            SELECT nome_exercicio, series, repeticoes, carga, descanso, observacoes, divisao
            FROM exercicios_treino
            WHERE id_treino = ?
            ORDER BY divisao, id
            """,
            (self.selected_treino_id,),
        )

        initial_dir = str(Path.cwd())
        aluno_nome = str(aluno["nome"]).replace(" ", "_")
        default_filename = f"treino_{self.selected_treino_id}_{aluno_nome}.pdf"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialdir=initial_dir,
            initialfile=default_filename,
            title="Salvar ficha de treino em PDF",
        )
        if not file_path:
            return

        dados_treino = dict(treino)
        dados_aluno = dict(aluno)
        professor_nome = self.professor_nome_var.get().strip()

        gerar_pdf_treino(
            dados_treino=dados_treino,
            dados_aluno=dados_aluno,
            exercicios=[dict(row) for row in exercicios_rows],
            professor_nome=professor_nome,
            output_path=Path(file_path),
        )
