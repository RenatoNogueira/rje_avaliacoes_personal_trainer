import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from .input_masks import bind_mask, format_cpf_value, only_digits
from .utils import setup_enter_navigation, create_tooltip, show_toast

from database import db
from reports.agenda_pdf import gerar_pdf_agenda


TIPOS_AGENDAMENTO = ("Avaliação", "Treino", "Consultoria")
STATUS_AGENDAMENTO = ("Pendente", "Concluído", "Cancelado")


class AgendaView(ctk.CTkFrame):
    def __init__(self, master, get_current_user=None) -> None:
        super().__init__(master)

        self.selected_id = None
        self.alunos_cache: dict[int, str] = {}
        self.get_current_user = get_current_user or (lambda: None)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        title = ctk.CTkLabel(
            header_frame,
            text="Agenda",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(side="left")

        # Container Principal
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        content.grid_columnconfigure(0, weight=1, minsize=300)  # Lista (35%)
        content.grid_columnconfigure(1, weight=2, minsize=400)  # Detalhes (65%)
        content.grid_rowconfigure(0, weight=1)

        # --- Coluna da Esquerda: Filtros e Lista ---
        left_panel = ctk.CTkFrame(content)
        left_panel.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        left_panel.grid_rowconfigure(2, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        # Filtros
        filter_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        filter_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        filter_frame.grid_columnconfigure(1, weight=1)

        # Linha 1: Data
        ctk.CTkLabel(filter_frame, text="Data:").grid(row=0, column=0, padx=(0, 5), pady=5, sticky="e")
        self.entry_data_filtro = ctk.CTkEntry(filter_frame, width=100)
        self.entry_data_filtro.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="ew")
        bind_mask(self.entry_data_filtro, "date")

        btn_hoje = ctk.CTkButton(filter_frame, text="Hoje", width=60, command=self.set_data_hoje_filtro, fg_color="gray")
        btn_hoje.grid(row=0, column=2, padx=(5, 0), pady=5, sticky="w")

        # Linha 2: Aluno
        ctk.CTkLabel(filter_frame, text="Aluno:").grid(row=1, column=0, padx=(0, 5), pady=5, sticky="e")
        self.entry_filtro_aluno = ctk.CTkEntry(filter_frame, placeholder_text="Buscar aluno...")
        self.entry_filtro_aluno.grid(row=1, column=1, columnspan=2, padx=(0, 0), pady=5, sticky="ew")

        btn_filtrar = ctk.CTkButton(filter_frame, text="Aplicar Filtros", command=self.load_agendamentos)
        btn_filtrar.grid(row=2, column=0, columnspan=3, padx=0, pady=(5, 0), sticky="ew")

        # Lista (Scrollable)
        self.scroll_list = ctk.CTkScrollableFrame(left_panel)
        self.scroll_list.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # --- Coluna da Direita: Formulário ---
        right_panel = ctk.CTkFrame(content)
        right_panel.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(0, weight=1)

        form_scroll = ctk.CTkScrollableFrame(right_panel, fg_color="transparent")
        form_scroll.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")
        form_scroll.grid_columnconfigure(1, weight=1)

        row = 0
        ctk.CTkLabel(form_scroll, text="Detalhes do Agendamento", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=row, column=0, columnspan=2, padx=10, pady=(20, 10), sticky="w"
        )
        row += 1

        ctk.CTkLabel(form_scroll, text="Aluno:").grid(
            row=row, column=0, padx=10, pady=(10, 5), sticky="e"
        )
        self.combo_aluno = ctk.CTkComboBox(form_scroll, values=[])
        self.combo_aluno.grid(row=row, column=1, padx=10, pady=(10, 5), sticky="ew")

        row += 1
        ctk.CTkLabel(form_scroll, text="Data:").grid(
            row=row, column=0, padx=10, pady=5, sticky="e"
        )
        self.entry_data = ctk.CTkEntry(form_scroll)
        self.entry_data.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        bind_mask(self.entry_data, "date")

        row += 1
        ctk.CTkLabel(form_scroll, text="Horário (HH:MM):").grid(
            row=row, column=0, padx=10, pady=5, sticky="e"
        )
        self.entry_horario = ctk.CTkEntry(form_scroll)
        self.entry_horario.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        bind_mask(self.entry_horario, "time")

        row += 1
        ctk.CTkLabel(form_scroll, text="Tipo:").grid(
            row=row, column=0, padx=10, pady=5, sticky="e"
        )
        self.combo_tipo = ctk.CTkComboBox(form_scroll, values=list(TIPOS_AGENDAMENTO))
        self.combo_tipo.grid(row=row, column=1, padx=10, pady=5, sticky="ew")

        row += 1
        ctk.CTkLabel(form_scroll, text="Status:").grid(
            row=row, column=0, padx=10, pady=5, sticky="e"
        )
        self.combo_status = ctk.CTkComboBox(form_scroll, values=list(STATUS_AGENDAMENTO))
        self.combo_status.grid(row=row, column=1, padx=10, pady=5, sticky="ew")

        row += 1
        # Metadados
        meta_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        meta_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=20, sticky="ew")
        meta_frame.grid_columnconfigure(0, weight=1)
        meta_frame.grid_columnconfigure(1, weight=1)

        self.label_criado_por = ctk.CTkLabel(meta_frame, text="Criado por: -", font=ctk.CTkFont(size=11), text_color="gray")
        self.label_criado_por.grid(row=0, column=0, sticky="w")
        self.label_atualizado_por = ctk.CTkLabel(meta_frame, text="Última atualização: -", font=ctk.CTkFont(size=11), text_color="gray")
        self.label_atualizado_por.grid(row=0, column=1, sticky="e")

        setup_enter_navigation(form_scroll)

        # Botões de Ação (Footer)
        actions_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        actions_frame.grid(row=1, column=0, padx=15, pady=15, sticky="ew")
        actions_frame.grid_columnconfigure(0, weight=1)

        btn_novo = ctk.CTkButton(
            actions_frame,
            text="+ Novo",
            command=self.on_novo,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            width=80
        )
        btn_novo.pack(side="left", padx=(0, 10))
        create_tooltip(btn_novo, "Limpar campos para criar um novo agendamento")

        btn_salvar = ctk.CTkButton(
            actions_frame,
            text="💾 Salvar",
            command=self.on_salvar,
            width=80
        )
        btn_salvar.pack(side="left", padx=(0, 10))
        create_tooltip(btn_salvar, "Gravar agendamento no banco de dados")

        btn_pdf = ctk.CTkButton(
            actions_frame,
            text="📄 PDF",
            command=self.on_gerar_pdf,
            fg_color="#3498db",
            hover_color="#2980b9",
            width=80
        )
        btn_pdf.pack(side="left", padx=(0, 10))
        create_tooltip(btn_pdf, "Gerar relatório PDF dos agendamentos filtrados")

        btn_excluir = ctk.CTkButton(
            actions_frame,
            text="🗑️ Excluir",
            command=self.on_excluir,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            width=80
        )
        btn_excluir.pack(side="right")
        create_tooltip(btn_excluir, "Remover agendamento selecionado permanentemente")

        self.load_alunos()
        self.set_data_hoje_filtro()
        self.on_novo()
        self.load_agendamentos()

    def load_alunos(self) -> None:
        rows = db.fetch_all(
            """
            SELECT id, nome
            FROM alunos
            ORDER BY nome
            """
        )

        self.alunos_cache = {row["id"]: row["nome"] for row in rows}

        values = [f"{row['id']:04d} - {row['nome']}" for row in rows]
        self.combo_aluno.configure(values=values)
        self.combo_aluno.set("")

    def set_data_hoje_filtro(self) -> None:
        hoje = datetime.date.today()
        self.entry_data_filtro.delete(0, "end")
        self.entry_data_filtro.insert(0, hoje.strftime("%d/%m/%Y"))

    def load_agendamentos(self) -> None:
        # Limpa lista
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        data_filtro = self.entry_data_filtro.get().strip()
        data_iso = data_filtro
        try:
            if data_filtro:
                d = datetime.datetime.strptime(data_filtro, "%d/%m/%Y").date()
                data_iso = d.isoformat()
        except Exception:
            pass
        aluno_filtro = ""
        if hasattr(self, "entry_filtro_aluno"):
            aluno_filtro = self.entry_filtro_aluno.get().strip()

        user = self.get_current_user() if self.get_current_user else None
        is_admin = bool(user and user.get("is_admin"))
        user_id = user.get("id") if user else None

        rows = []
        
        # Filtros de SQL base
        where_clauses = []
        params = []
        
        # Se NÃO for admin, filtra apenas os agendamentos criados pelo usuário
        if not is_admin and user_id:
             where_clauses.append("a.id_usuario_criacao = ?")
             params.append(user_id)

        if data_filtro:
            where_clauses.append("a.data = ?")
            params.append(data_iso)
        
        if aluno_filtro:
            where_clauses.append("al.nome LIKE ?")
            params.append(f"%{aluno_filtro}%")
            
        where_sql = " AND ".join(where_clauses)
        if where_sql:
            where_sql = "WHERE " + where_sql
            
        query = f"""
            SELECT a.id, a.data, a.horario, a.tipo, a.status, al.nome AS nome_aluno, al.cpf AS cpf
            FROM agendamentos a
            JOIN alunos al ON al.id = a.id_aluno
            {where_sql}
            ORDER BY a.data DESC, a.horario
        """
        
        # Correção para o parâmetro params, que deve ser tupla
        rows = db.fetch_all(query, tuple(params))

        if not rows:
            ctk.CTkLabel(self.scroll_list, text="Nenhum agendamento encontrado.", text_color="gray").pack(pady=20)
            return

        for row in rows:
            self._create_card(row)

    def _create_card(self, row: dict) -> None:
        card = ctk.CTkFrame(self.scroll_list, fg_color=("gray90", "gray20"), corner_radius=8)
        card.pack(fill="x", pady=4, padx=2)

        data_br = row["data"]
        try:
            if row["data"]:
                data_br = datetime.date.fromisoformat(row["data"]).strftime("%d/%m/%Y")
        except Exception:
            pass
        
        # Header: Hora e Data
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 0))
        
        lbl_hora = ctk.CTkLabel(header, text=f"{data_br} - {row['horario']}", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_hora.pack(side="left")
        
        status_color = "gray"
        if row["status"] == "Concluído": status_color = "green"
        elif row["status"] == "Cancelado": status_color = "red"
        elif row["status"] == "Pendente": status_color = "orange"
        
        lbl_status = ctk.CTkLabel(header, text=row["status"], font=ctk.CTkFont(size=11, weight="bold"), text_color=status_color)
        lbl_status.pack(side="right")

        # Aluno
        lbl_aluno = ctk.CTkLabel(card, text=row["nome_aluno"], font=ctk.CTkFont(size=14))
        lbl_aluno.pack(fill="x", padx=10, pady=(2, 0), anchor="w")

        # Tipo
        lbl_tipo = ctk.CTkLabel(card, text=f"Tipo: {row['tipo']}", font=ctk.CTkFont(size=12), text_color="gray")
        lbl_tipo.pack(fill="x", padx=10, pady=(0, 8), anchor="w")

        # Bind events
        for w in (card, header, lbl_hora, lbl_status, lbl_aluno, lbl_tipo):
            w.bind("<Button-1>", lambda e, aid=row["id"]: self.load_agendamento_details(aid))
            w.bind("<Enter>", lambda e, c=card: c.configure(border_width=1, border_color="gray50"))
            w.bind("<Leave>", lambda e, c=card: c.configure(border_width=0))

    def load_agendamento_details(self, agendamento_id: int) -> None:
        self.selected_id = agendamento_id
        row = db.fetch_one(
            """
            SELECT a.id, a.id_aluno, a.data, a.horario, a.tipo, a.status,
                   al.nome AS nome_aluno,
                   uc.username AS username_criacao, uc.nome AS nome_criacao,
                   uu.username AS username_atualizacao, uu.nome AS nome_atualizacao
            FROM agendamentos a
            JOIN alunos al ON al.id = a.id_aluno
            LEFT JOIN usuarios uc ON uc.id = a.id_usuario_criacao
            LEFT JOIN usuarios uu ON uu.id = a.id_usuario_atualizacao
            WHERE a.id = ?
            """,
            (self.selected_id,),
        )
        if row is None:
            return

        aluno_str = f"{row['id_aluno']:04d} - {row['nome_aluno']}"
        self.combo_aluno.set(aluno_str)

        self.entry_data.delete(0, "end")
        try:
            if row["data"]:
                d = datetime.date.fromisoformat(row["data"])
                self.entry_data.insert(0, d.strftime("%d/%m/%Y"))
        except Exception:
            self.entry_data.insert(0, row["data"] or "")

        self.entry_horario.delete(0, "end")
        self.entry_horario.insert(0, row["horario"] or "")

        self.combo_tipo.set(row["tipo"])
        self.combo_status.set(row["status"])

        criado = row["nome_criacao"] or row["username_criacao"] or "-"
        atualizado = row["nome_atualizacao"] or row["username_atualizacao"] or "-"
        self.label_criado_por.configure(text=f"Criado por: {criado}")
        self.label_atualizado_por.configure(text=f"Última atualização: {atualizado}")

    def on_novo(self) -> None:
        self.selected_id = None

        self.combo_aluno.set("")
        self.entry_data.delete(0, "end")
        self.entry_horario.delete(0, "end")
        self.combo_tipo.set("")
        self.combo_status.set("")

        if hasattr(self, "label_criado_por"):
            self.label_criado_por.configure(text="Criado por: -")
        if hasattr(self, "label_atualizado_por"):
            self.label_atualizado_por.configure(text="Última atualização: -")

    def _get_selected_aluno_id(self) -> int | None:
        value = self.combo_aluno.get().strip()
        if not value:
            return None
        try:
            id_str = value.split("-")[0].strip()
            return int(id_str)
        except ValueError:
            return None

    def on_salvar(self) -> None:
        id_aluno = self._get_selected_aluno_id()
        data_str = self.entry_data.get().strip()
        horario_str = self.entry_horario.get().strip()
        tipo = self.combo_tipo.get().strip()
        status = self.combo_status.get().strip()

        if id_aluno is None:
            messagebox.showwarning("Agenda", "Selecione um aluno para o agendamento.")
            return
        if not data_str:
            messagebox.showwarning("Agenda", "Informe a data do agendamento.")
            return
        if not horario_str:
            messagebox.showwarning("Agenda", "Informe o horário do agendamento.")
            return
        try:
            d = datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
            data = d.isoformat()
        except ValueError:
            messagebox.showwarning(
                "Agenda", "Data inválida. Use o formato DD/MM/AAAA."
            )
            return
        try:
            datetime.time.fromisoformat(horario_str)
        except ValueError:
            messagebox.showwarning(
                "Agenda", "Horário inválido. Use o formato HH:MM (24h)."
            )
            return
        horario = horario_str
        if not tipo or tipo not in TIPOS_AGENDAMENTO:
            messagebox.showwarning("Agenda", "Tipo de agendamento inválido.")
            return
        if not status or status not in STATUS_AGENDAMENTO:
            messagebox.showwarning("Agenda", "Status de agendamento inválido.")
            return

        user = self.get_current_user() if self.get_current_user else None
        user_id = None
        if user is not None:
            try:
                user_id = int(user.get("id"))
            except Exception:
                user_id = None

        if self.selected_id is None:
            db.execute(
                """
                INSERT INTO agendamentos
                    (id_aluno, data, horario, tipo, status,
                     id_usuario_criacao, id_usuario_atualizacao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (id_aluno, data, horario, tipo, status, user_id, user_id),
                commit=True,
            )
        else:
            db.execute(
                """
                UPDATE agendamentos
                SET id_aluno = ?, data = ?, horario = ?, tipo = ?, status = ?,
                    id_usuario_atualizacao = ?
                WHERE id = ?
                """,
                (id_aluno, data, horario, tipo, status, user_id, self.selected_id),
                commit=True,
            )

        self.load_agendamentos()
        messagebox.showinfo("Agenda", "Agendamento salvo com sucesso.")

    def on_excluir(self) -> None:
        if self.selected_id is None:
            show_toast(self, "Selecione um agendamento para excluir.", 3000)
            return
        
        if not messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja excluir este agendamento?"):
            return
            
        show_toast(self, "Excluindo agendamento...", 1500)
        self.after(500, self._confirm_excluir)

    def _confirm_excluir(self):
        db.execute(
            "DELETE FROM agendamentos WHERE id = ?",
            (self.selected_id,),
            commit=True,
        )
        self.selected_id = None
        self.on_novo()
        self.load_agendamentos()
        messagebox.showinfo("Agenda", "Agendamento excluído com sucesso.")

    def on_gerar_pdf(self) -> None:
        data_filtro = self.entry_data_filtro.get().strip()
        aluno_filtro = ""
        if hasattr(self, "entry_filtro_aluno"):
            aluno_filtro = self.entry_filtro_aluno.get().strip()

        if not data_filtro:
            messagebox.showwarning(
                "Agenda",
                "Informe uma data no filtro para gerar o PDF da agenda.",
            )
            return

        filtro_like = f"%{aluno_filtro}%" if aluno_filtro else None

        if filtro_like:
            rows = db.fetch_all(
                """
                SELECT a.id, a.data, a.horario, a.tipo, a.status, al.nome AS nome_aluno
                FROM agendamentos a
                JOIN alunos al ON al.id = a.id_aluno
                WHERE a.data = ?
                  AND al.nome LIKE ?
                ORDER BY a.horario
                """,
                (data_iso, filtro_like),
            )
        else:
            rows = db.fetch_all(
                """
                SELECT a.id, a.data, a.horario, a.tipo, a.status, al.nome AS nome_aluno
                FROM agendamentos a
                JOIN alunos al ON al.id = a.id_aluno
                WHERE a.data = ?
                ORDER BY a.horario
                """,
                (data_iso,),
            )

        initial_dir = str(Path.cwd())
        default_filename = f"agenda_{data_iso}.pdf"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialdir=initial_dir,
            initialfile=default_filename,
            title="Salvar agenda em PDF",
        )
        if not file_path:
            return

        gerar_pdf_agenda(
            data=data_filtro,
            agendamentos=rows,
            output_path=Path(file_path),
        )

        self.load_agendamentos()

    def on_excluir(self) -> None:
        if self.selected_id is None:
            return

        db.execute(
            "DELETE FROM agendamentos WHERE id = ?",
            (self.selected_id,),
            commit=True,
        )

        self.on_novo()
        self.load_agendamentos()

