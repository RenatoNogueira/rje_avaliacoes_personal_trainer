import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from .input_masks import bind_mask, format_cpf_value, only_digits
from .utils import setup_enter_navigation, create_tooltip, show_toast

from .theme import _c, font_body, font_subtitle, font_small, create_view_header, create_action_button, create_empty_state, create_section_title, create_status_pill, bind_card_hover
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
        self.header = create_view_header(self, "📅", "Agenda", "Gerencie seus horários e compromissos")
        self.header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

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

        btn_filtrar = create_action_button(filter_frame, "Aplicar Filtros", "btn_save", self.load_agendamentos)
        btn_filtrar.grid(row=2, column=0, columnspan=3, padx=0, pady=(10, 0), sticky="ew")

        # Lista (Scrollable)
        self.scroll_list = ctk.CTkScrollableFrame(left_panel, fg_color=_c("panel_bg"), corner_radius=0)
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
        create_section_title(form_scroll, "Detalhes do Agendamento").grid(row=row, column=0, columnspan=2, padx=16, pady=(18, 8), sticky="w")
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
        create_section_title(form_scroll, "Histórico").grid(row=row, column=0, columnspan=2, padx=16, pady=(18, 8), sticky="w")
        row += 1
        
        # Metadados
        meta_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        meta_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=(5, 20), sticky="ew")
        meta_frame.grid_columnconfigure(0, weight=1)
        meta_frame.grid_columnconfigure(1, weight=1)

        self.label_criado_por = ctk.CTkLabel(meta_frame, text="Criado por: -", font=font_small(), text_color="gray")
        self.label_criado_por.grid(row=0, column=0, sticky="w")
        self.label_atualizado_por = ctk.CTkLabel(meta_frame, text="Última atualização: -", font=font_small(), text_color="gray")
        self.label_atualizado_por.grid(row=0, column=1, sticky="e")

        setup_enter_navigation(form_scroll)

        # Botões de Ação (Footer)
        actions_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        actions_frame.grid(row=1, column=0, padx=20, pady=20, sticky="ew")

        create_action_button(actions_frame, "+ Novo", "btn_new", self.on_novo, width=90).pack(side="left", padx=(0, 10))
        create_action_button(actions_frame, "💾 Salvar", "btn_save", self.on_salvar, width=90).pack(side="left", padx=(0, 10))
        create_action_button(actions_frame, "📄 PDF", "btn_pdf", self.on_gerar_pdf, width=90).pack(side="left", padx=(0, 10))
        create_action_button(actions_frame, "🗑️ Excluir", "btn_delete", self.on_excluir, width=90).pack(side="right")

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
            create_empty_state(self.scroll_list, "📅", "Nenhum agendamento encontrado").pack(pady=40)
            return

        for row in rows:
            self._create_card(row)

    def _create_card(self, row: dict) -> None:
        bg = _c("ag_card_bg")
        hover = _c("ag_card_hover")
        is_today = row["data"] == datetime.date.today().isoformat()
        
        if is_today:
            bg = _c("ag_today_bg")
            hover = _c("ag_today_hover")

        card = ctk.CTkFrame(self.scroll_list, fg_color=bg, corner_radius=8, height=65)
        card.pack(fill="x", pady=2, padx=4)
        card.pack_propagate(False)

        # Accent bar lateral se for hoje
        if is_today:
            accent = ctk.CTkFrame(card, width=3, fg_color=_c("card_agenda_accent"), corner_radius=1)
            accent.pack(side="left", fill="y", padx=(6, 0), pady=10)

        data_br = row["data"]
        try:
            if row["data"]:
                data_br = datetime.date.fromisoformat(row["data"]).strftime("%d/%m")
        except Exception:
            pass
        
        # Conteúdo
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        
        # Header do card: Hora e Status
        header = ctk.CTkFrame(content_frame, fg_color="transparent")
        header.pack(fill="x")
        
        lbl_hora = ctk.CTkLabel(header, text=f"🕒 {row['horario']}", font=ctk.CTkFont(size=14, weight="bold"))
        lbl_hora.pack(side="left")
        
        create_status_pill(header, row["status"])

        # Aluno e Tipo
        lbl_aluno = ctk.CTkLabel(content_frame, text=row["nome_aluno"], font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        lbl_aluno.pack(fill="x", pady=(2, 0))

        details_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        details_frame.pack(fill="x")
        
        tipo_data = f"📂 {row['tipo']} | 📅 {data_br}" if not is_today else f"📂 {row['tipo']} | Hoje"
        lbl_tipo = ctk.CTkLabel(details_frame, text=tipo_data, font=font_small(), text_color=_c("view_header_subtitle"))
        lbl_tipo.pack(side="left")

        # Bind events
        for w in (card, content_frame, header, lbl_hora, lbl_aluno, details_frame, lbl_tipo):
            w.bind("<Button-1>", lambda e, aid=row["id"]: self.load_agendamento_details(aid))
            
        bind_card_hover(card, bg, hover)

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

        try:
            # Converte DD/MM/YYYY -> YYYY-MM-DD
            d, m, y = data_filtro.split("/")
            data_iso = f"{y}-{m}-{d}"
        except Exception:
            messagebox.showerror("Erro", "Formato de data inválido no filtro. Use DD/MM/YYYY")
            return

        filtro_like = f"%{aluno_filtro}%" if aluno_filtro else None

        if filtro_like:
            rows = db.fetch_all(
                """
                SELECT a.id, a.data, a.horario, a.tipo, a.status, al.nome AS nome_aluno, al.cpf,
                       v.psist, v.pdiast
                FROM agendamentos a
                JOIN alunos al ON al.id = a.id_aluno
                LEFT JOIN (
                    SELECT id_aluno, pressao_sistolica as psist, pressao_diastolica as pdiast,
                           ROW_NUMBER() OVER (PARTITION BY id_aluno ORDER BY data DESC, id DESC) as rn
                    FROM avaliacoes_fisicas
                ) v ON v.id_aluno = a.id_aluno AND v.rn = 1
                WHERE a.data = ?
                  AND al.nome LIKE ?
                ORDER BY a.horario
                """,
                (data_iso, filtro_like),
            )
        else:
            rows = db.fetch_all(
                """
                SELECT a.id, a.data, a.horario, a.tipo, a.status, al.nome AS nome_aluno, al.cpf,
                       v.psist, v.pdiast
                FROM agendamentos a
                JOIN alunos al ON al.id = a.id_aluno
                LEFT JOIN (
                    SELECT id_aluno, pressao_sistolica as psist, pressao_diastolica as pdiast,
                           ROW_NUMBER() OVER (PARTITION BY id_aluno ORDER BY data DESC, id DESC) as rn
                    FROM avaliacoes_fisicas
                ) v ON v.id_aluno = a.id_aluno AND v.rn = 1
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

        # Tenta obter CREF do usuário logado ou das configurações
        professor_cref = ""
        user = self.get_current_user() if self.get_current_user else None
        if user:
             professor_cref = user.get("cref") or ""
        
        if not professor_cref:
            # Fallback para settings.json se houver
            try:
                import json
                base_dir = Path(__file__).resolve().parent.parent
                settings_path = base_dir / "data" / "settings.json"
                if settings_path.exists():
                    data = json.loads(settings_path.read_text(encoding="utf-8"))
                    professor_cref = data.get("contato_cref") or ""
            except Exception:
                pass

        gerar_pdf_agenda(
            data=data_filtro,
            agendamentos=rows,
            professor_cref=professor_cref,
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

