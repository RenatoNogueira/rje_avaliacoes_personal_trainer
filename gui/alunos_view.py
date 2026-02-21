import datetime
from tkinter import messagebox

import re
import customtkinter as ctk
from .input_masks import bind_mask, is_valid_cpf, is_valid_cep, format_cpf_value, format_cep_value, only_digits
from .utils import setup_enter_navigation, create_tooltip, show_toast

from database import db


class AlunosView(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master)

        self.selected_id = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        title = ctk.CTkLabel(
            header_frame,
            text="Gestão de Alunos",
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

        self.entry_filtro_nome = ctk.CTkEntry(filter_frame, placeholder_text="🔍 Buscar por nome...")
        self.entry_filtro_nome.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="ew")
        self.entry_filtro_nome.bind("<Return>", lambda e: self.load_alunos())

        btn_filtrar = ctk.CTkButton(filter_frame, text="Filtrar", width=80, command=self.load_alunos)
        btn_filtrar.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="e")

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
        ctk.CTkLabel(form_scroll, text="Dados Pessoais", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=row, column=0, columnspan=2, padx=10, pady=(20, 10), sticky="w"
        )
        row += 1

        ctk.CTkLabel(form_scroll, text="Nome:").grid(
            row=row, column=0, padx=10, pady=(10, 5), sticky="e"
        )
        self.entry_nome = ctk.CTkEntry(form_scroll)
        self.entry_nome.grid(row=row, column=1, padx=10, pady=(10, 5), sticky="ew")

        row += 1
        ctk.CTkLabel(form_scroll, text="Data de nascimento:").grid(
            row=row, column=0, padx=10, pady=5, sticky="e"
        )
        self.entry_data_nascimento = ctk.CTkEntry(form_scroll, placeholder_text="DD/MM/AAAA")
        self.entry_data_nascimento.grid(
            row=row, column=1, padx=10, pady=5, sticky="ew"
        )
        bind_mask(self.entry_data_nascimento, "date")

        row += 1
        ctk.CTkLabel(form_scroll, text="CPF:").grid(
            row=row, column=0, padx=10, pady=5, sticky="e"
        )
        self.entry_cpf = ctk.CTkEntry(form_scroll)
        self.entry_cpf.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        bind_mask(self.entry_cpf, "cpf")

        row += 1
        ctk.CTkLabel(form_scroll, text="Telefone:").grid(
            row=row, column=0, padx=10, pady=5, sticky="e"
        )
        self.entry_telefone = ctk.CTkEntry(form_scroll)
        self.entry_telefone.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        bind_mask(self.entry_telefone, "tel")

        row += 1
        ctk.CTkLabel(form_scroll, text="E-mail:").grid(
            row=row, column=0, padx=10, pady=5, sticky="e"
        )
        self.entry_email = ctk.CTkEntry(form_scroll)
        self.entry_email.grid(row=row, column=1, padx=10, pady=5, sticky="ew")

        row += 1
        ctk.CTkLabel(form_scroll, text="CEP:").grid(
            row=row, column=0, padx=10, pady=5, sticky="e"
        )
        self.entry_cep = ctk.CTkEntry(form_scroll)
        self.entry_cep.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
        bind_mask(self.entry_cep, "cep")

        row += 1
        ctk.CTkLabel(form_scroll, text="Objetivo:").grid(
            row=row, column=0, padx=10, pady=5, sticky="e"
        )
        self.entry_objetivo = ctk.CTkEntry(form_scroll)
        self.entry_objetivo.grid(row=row, column=1, padx=10, pady=5, sticky="ew")

        row += 1
        ctk.CTkLabel(form_scroll, text="Observações médicas:").grid(
            row=row, column=0, padx=10, pady=(20, 5), sticky="ne"
        )
        self.text_obs_medicas = ctk.CTkTextbox(form_scroll, height=100)
        self.text_obs_medicas.grid(
            row=row, column=1, padx=10, pady=(20, 5), sticky="nsew"
        )

        setup_enter_navigation(form_scroll)

        # Botões de Ação (Footer)
        actions_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        actions_frame.grid(row=1, column=0, padx=15, pady=15, sticky="ew")
        actions_frame.grid_columnconfigure(0, weight=1)

        btn_novo = ctk.CTkButton(
            actions_frame,
            text="+ Novo Aluno",
            command=self.on_novo,
            fg_color="#2ecc71",
            hover_color="#27ae60"
        )
        btn_novo.pack(side="left", padx=(0, 10))
        create_tooltip(btn_novo, "Limpar formulário para cadastrar novo aluno")

        btn_salvar = ctk.CTkButton(
            actions_frame,
            text="💾 Salvar",
            command=self.on_salvar,
        )
        btn_salvar.pack(side="left", padx=(0, 10))
        create_tooltip(btn_salvar, "Gravar dados do aluno")

        btn_excluir = ctk.CTkButton(
            actions_frame,
            text="🗑️ Excluir",
            command=self.on_excluir,
            fg_color="#e74c3c",
            hover_color="#c0392b",
        )
        btn_excluir.pack(side="right")
        create_tooltip(btn_excluir, "Remover aluno selecionado")

        self.load_alunos()

    def load_alunos(self) -> None:
        # Limpa lista
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        filtro = self.entry_filtro_nome.get().strip()
        query = "SELECT id, nome, data_nascimento, telefone, cpf FROM alunos"
        params = []
        
        if filtro:
            query += " WHERE nome LIKE ?"
            params.append(f"%{filtro}%")
        
        query += " ORDER BY nome"
        
        rows = db.fetch_all(query, tuple(params))

        if not rows:
            ctk.CTkLabel(self.scroll_list, text="Nenhum aluno encontrado.", text_color="gray").pack(pady=20)
            return

        for row in rows:
            self._create_card(row)

    def _create_card(self, row: dict) -> None:
        card = ctk.CTkFrame(self.scroll_list, fg_color=("gray90", "gray20"), corner_radius=8)
        card.pack(fill="x", pady=4, padx=2)

        # Info
        tel = row["telefone"] or ""
        cpf_d = only_digits(row["cpf"])
        cpf_fmt = format_cpf_value(cpf_d) if cpf_d else ""
        
        # Header: Nome
        lbl_nome = ctk.CTkLabel(card, text=row["nome"], font=ctk.CTkFont(size=14, weight="bold"))
        lbl_nome.pack(fill="x", padx=10, pady=(8, 2), anchor="w")
        
        # Detalhes
        details = []
        if tel: details.append(tel)
        if cpf_fmt: details.append(f"CPF: {cpf_fmt}")
        
        lbl_details = ctk.CTkLabel(card, text=" | ".join(details), font=ctk.CTkFont(size=12), text_color="gray")
        lbl_details.pack(fill="x", padx=10, pady=(0, 8), anchor="w")

        # Bind events
        for w in (card, lbl_nome, lbl_details):
            w.bind("<Button-1>", lambda e, aid=row["id"]: self.load_aluno_details(aid))
            w.bind("<Enter>", lambda e, c=card: c.configure(border_width=1, border_color="gray50"))
            w.bind("<Leave>", lambda e, c=card: c.configure(border_width=0))

    def load_aluno_details(self, aluno_id: int) -> None:
        self.selected_id = aluno_id
        row = db.fetch_one(
            """
            SELECT id, nome, data_nascimento, telefone, email, objetivo, observacoes_medicas, cpf, cep
            FROM alunos
            WHERE id = ?
            """,
            (self.selected_id,),
        )
        if row is None:
            return

        self.entry_nome.delete(0, "end")
        self.entry_nome.insert(0, row["nome"] or "")

        self.entry_data_nascimento.delete(0, "end")
        try:
            if row["data_nascimento"]:
                d = datetime.date.fromisoformat(row["data_nascimento"])
                self.entry_data_nascimento.insert(0, d.strftime("%d/%m/%Y"))
        except Exception:
            self.entry_data_nascimento.insert(0, row["data_nascimento"] or "")

        self.entry_telefone.delete(0, "end")
        self.entry_telefone.insert(0, row["telefone"] or "")

        self.entry_cpf.delete(0, "end")
        if row["cpf"]:
            _cpf_d = only_digits(row["cpf"])
            self.entry_cpf.insert(0, format_cpf_value(_cpf_d) if _cpf_d else "")

        self.entry_cep.delete(0, "end")
        if row["cep"]:
            _cep_d = only_digits(row["cep"])
            self.entry_cep.insert(0, format_cep_value(_cep_d) if _cep_d else "")

        self.entry_email.delete(0, "end")
        self.entry_email.insert(0, row["email"] or "")

        self.entry_objetivo.delete(0, "end")
        self.entry_objetivo.insert(0, row["objetivo"] or "")

        self.text_obs_medicas.configure(state="normal")
        self.text_obs_medicas.delete("1.0", "end")
        if row["observacoes_medicas"]:
            self.text_obs_medicas.insert("end", row["observacoes_medicas"])
        self.text_obs_medicas.configure(state="normal")

    def on_novo(self) -> None:
        self.selected_id = None

        self.entry_nome.delete(0, "end")
        self.entry_data_nascimento.delete(0, "end")
        self.entry_telefone.delete(0, "end")
        try:
            self.entry_cpf.delete(0, "end")
            self.entry_cep.delete(0, "end")
        except Exception:
            pass
        self.entry_email.delete(0, "end")
        self.entry_objetivo.delete(0, "end")
        self.text_obs_medicas.configure(state="normal")
        self.text_obs_medicas.delete("1.0", "end")
        self.text_obs_medicas.configure(state="normal")

    def on_salvar(self) -> None:
        nome = self.entry_nome.get().strip()
        data_nascimento_str = self.entry_data_nascimento.get().strip()
        data_nascimento = None
        if data_nascimento_str:
            try:
                d = datetime.datetime.strptime(data_nascimento_str, "%d/%m/%Y").date()
                data_nascimento = d.isoformat()
            except ValueError:
                messagebox.showwarning(
                    "Alunos", "Data de nascimento inválida. Use o formato DD/MM/AAAA."
                )
                return
        telefone = self.entry_telefone.get().strip() or None
        cpf = None
        cep = None
        try:
            cpf = self.entry_cpf.get().strip() or None
        except Exception:
            pass
        try:
            cep = self.entry_cep.get().strip() or None
        except Exception:
            pass
        email = self.entry_email.get().strip() or None
        objetivo = self.entry_objetivo.get().strip() or None
        observacoes_medicas = self.text_obs_medicas.get("1.0", "end").strip() or None

        if not nome:
            messagebox.showwarning("Alunos", "O nome do aluno é obrigatório.")
            return

        # Telefone: se informado, validar DDD (não inicia com 0) e comprimento (10 ou 11 dígitos)
        if telefone:
            tel_digits = only_digits(telefone)
            if len(tel_digits) not in (10, 11) or tel_digits[0] == "0":
                messagebox.showwarning(
                    "Alunos",
                    "Telefone inválido. Informe DDD + número (10 ou 11 dígitos).",
                )
                return
        # E-mail: validação básica
        if email:
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                messagebox.showwarning(
                    "Alunos",
                    "E-mail inválido. Verifique o endereço informado.",
                )
                return

        # CPF: se informado, validar dígitos verificadores e comprimento
        if cpf:
            if not is_valid_cpf(cpf):
                messagebox.showwarning(
                    "Alunos",
                    "CPF inválido ou incompleto. Verifique os dígitos.",
                )
                return
        if cep:
            if not is_valid_cep(cep):
                messagebox.showwarning(
                    "Alunos",
                    "CEP inválido ou incompleto. Informe 8 dígitos.",
                )
                return

        # telefone já validado por máscara; permite vazio

        if self.selected_id is None:
            db.execute(
                """
                INSERT INTO alunos
                    (nome, data_nascimento, telefone, email, objetivo, observacoes_medicas, cpf, cep)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    nome,
                    data_nascimento,
                    telefone,
                    email,
                    objetivo,
                    observacoes_medicas,
                    only_digits(cpf) if cpf else None,
                    only_digits(cep) if cep else None,
                ),
                commit=True,
            )
        else:
            db.execute(
                """
                UPDATE alunos
                SET nome = ?, data_nascimento = ?, telefone = ?, email = ?,
                    objetivo = ?, observacoes_medicas = ?, cpf = ?, cep = ?
                WHERE id = ?
                """,
                (
                    nome,
                    data_nascimento,
                    telefone,
                    email,
                    objetivo,
                    observacoes_medicas,
                    only_digits(cpf) if cpf else None,
                    only_digits(cep) if cep else None,
                    self.selected_id,
                ),
                commit=True,
            )

        self.load_alunos()

        messagebox.showinfo("Alunos", "Dados do aluno salvos com sucesso.")

    def on_excluir(self) -> None:
        if self.selected_id is None:
            show_toast(self, "Selecione um aluno para excluir.", 3000)
            return

        if not messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja excluir este aluno e todos os seus dados?"):
            return

        show_toast(self, "Excluindo aluno...", 1500)
        self.after(500, self._confirm_excluir)

    def _confirm_excluir(self):
        db.execute(
            "DELETE FROM alunos WHERE id = ?",
            (self.selected_id,),
            commit=True,
        )

        self.on_novo()
        self.load_alunos()

        messagebox.showinfo("Alunos", "Aluno excluído com sucesso.")
