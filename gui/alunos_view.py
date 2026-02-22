import datetime
from tkinter import messagebox

import re
import customtkinter as ctk
from .input_masks import bind_mask, is_valid_cpf, is_valid_cep, format_cpf_value, format_cep_value, only_digits
from .utils import setup_enter_navigation, create_tooltip, show_toast

from database import db


from .theme import _c, font_body, font_subtitle, font_small, create_view_header, create_styled_card, create_action_button, create_empty_state, create_section_title, bind_card_hover, bind_click_recursive
from utils.image_utils import create_circular_image

class AlunosView(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master)

        self.selected_id = None
        self.foto_perfil_path = None # Armazena caminho da foto selecionada

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        self.header = create_view_header(self, "👥", "Gestão de Alunos", "Cadastre e gerencie seus alunos")
        self.header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

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
        create_section_title(form_scroll, "Dados Pessoais").grid(row=row, column=0, columnspan=2, padx=16, pady=(18, 8), sticky="w")
        row += 1

        # Foto de Perfil
        foto_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        foto_frame.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        
        # Label para preview (circular simulado ou quadrado)
        self.lbl_foto_preview = ctk.CTkLabel(foto_frame, text="📷", width=100, height=100, fg_color="gray30", corner_radius=10)
        self.lbl_foto_preview.pack(side="left", padx=(50, 20)) # Indentado para alinhar visualmente
        
        btn_foto_frame = ctk.CTkFrame(foto_frame, fg_color="transparent")
        btn_foto_frame.pack(side="left")
        
        create_action_button(btn_foto_frame, "Selecionar Foto...", "btn_save", self.on_select_foto, width=140).pack(pady=5)
        create_action_button(btn_foto_frame, "Remover Foto", "btn_delete", self.on_remove_foto, width=140).pack(pady=5)
        
        row += 1
        
        ctk.CTkLabel(form_scroll, text="Nome:").grid(
            row=row, column=0, padx=10, pady=(10, 5), sticky="e"
        )
        self.entry_nome = ctk.CTkEntry(form_scroll)
        self.entry_nome.grid(row=row, column=1, padx=10, pady=(10, 5), sticky="ew")
        
        row += 1
        ctk.CTkLabel(form_scroll, text="Instagram:").grid(
            row=row, column=0, padx=10, pady=5, sticky="e"
        )
        self.entry_instagram = ctk.CTkEntry(form_scroll, placeholder_text="@usuario")
        self.entry_instagram.grid(row=row, column=1, padx=10, pady=5, sticky="ew")

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
        actions_frame.grid(row=1, column=0, padx=20, pady=20, sticky="ew")

        create_action_button(actions_frame, "+ Novo Aluno", "btn_new", self.on_novo).pack(side="left", padx=(0, 10))
        create_action_button(actions_frame, "💾 Salvar", "btn_save", self.on_salvar).pack(side="left", padx=(0, 10))
        create_action_button(actions_frame, "🗑️ Excluir", "btn_delete", self.on_excluir).pack(side="right")

        self.load_alunos()

    def load_alunos(self) -> None:
        # Limpa lista
        for widget in self.scroll_list.winfo_children():
            widget.destroy()

        filtro = self.entry_filtro_nome.get().strip()
        query = "SELECT id, nome, data_nascimento, telefone, cpf, foto_perfil, instagram FROM alunos"
        params = []
        
        if filtro:
            query += " WHERE nome LIKE ?"
            params.append(f"%{filtro}%")
        
        query += " ORDER BY nome"
        
        rows = db.fetch_all(query, tuple(params))

        if not rows:
            create_empty_state(self.scroll_list, "👤", "Nenhum aluno encontrado").pack(pady=40)
            return

        for row in rows:
            self._create_card(row)

    def _create_card(self, row: dict) -> None:
        bg = _c("list_card_bg")
        hover = _c("list_card_hover")
        
        card = ctk.CTkFrame(self.scroll_list, fg_color=bg, corner_radius=8, height=65)
        card.pack(fill="x", pady=2, padx=4)
        card.pack_propagate(False)

        # Accent bar lateral sutil
        accent = ctk.CTkFrame(card, width=3, fg_color=_c("list_card_accent"), corner_radius=1)
        accent.pack(side="left", fill="y", padx=(6, 0), pady=10)

        # Conteúdo
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        
        # Foto (Miniatura Circular)
        foto_path = row["foto_perfil"]
        lbl_foto = ctk.CTkLabel(content_frame, text="👤", width=40, height=40, font=ctk.CTkFont(size=18), fg_color="gray50", corner_radius=20)
        
        if foto_path:
            try:
                from pathlib import Path
                if Path(foto_path).exists():
                    pil_img = create_circular_image(foto_path, (80, 80))
                    if pil_img:
                        ctk_img = ctk.CTkImage(pil_img, size=(40, 40))
                        lbl_foto.configure(image=ctk_img, text="", fg_color="transparent")
            except Exception:
                pass
        
        lbl_foto.pack(side="left", padx=(0, 10))

        # Info Frame
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        # Info
        tel = row["telefone"] or ""
        insta = row["instagram"] or ""
        
        # Header: Nome
        lbl_nome = ctk.CTkLabel(info_frame, text=row["nome"], font=ctk.CTkFont(size=13, weight="bold"), anchor="w", justify="left")
        lbl_nome.pack(fill="x")
        
        # Detalhes
        details = []
        if tel: details.append(tel)
        if insta: details.append(insta)
        
        lbl_details = ctk.CTkLabel(
            info_frame, 
            text=" | ".join(details) if details else "Nenhum contato", 
            font=font_small(), 
            text_color=_c("view_header_subtitle"),
            anchor="w",
            justify="left"
        )
        lbl_details.pack(fill="x")

        # Bind events
        for w in (card, content_frame, lbl_foto, info_frame, lbl_nome, lbl_details):
            w.bind("<Button-1>", lambda e, aid=row["id"]: self.load_aluno_details(aid))
            
        bind_card_hover(card, bg, hover)


    def load_aluno_details(self, aluno_id: int) -> None:
        self.selected_id = aluno_id
        row = db.fetch_one(
            """
            SELECT id, nome, data_nascimento, telefone, email, objetivo, observacoes_medicas, cpf, cep, foto_perfil, instagram
            FROM alunos
            WHERE id = ?
            """,
            (self.selected_id,),
        )
        if row is None:
            return

        # Foto
        self.foto_perfil_path = row["foto_perfil"]
        self._update_foto_preview(self.foto_perfil_path)

        self.entry_nome.delete(0, "end")
        self.entry_nome.insert(0, row["nome"] or "")
        
        self.entry_instagram.delete(0, "end")
        self.entry_instagram.insert(0, row["instagram"] or "")

        self.entry_data_nascimento.delete(0, "end")
        try:
            if row["data_nascimento"]:
                d = datetime.date.fromisoformat(row["data_nascimento"])
                self.entry_data_nascimento.insert(0, d.strftime("%d/%m/%Y"))
        except Exception:
            self.entry_data_nascimento.insert(0, row["data_nascimento"] or "")
        
        # ... continuação
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
        
        self.foto_perfil_path = None
        self._update_foto_preview(None)

        self.entry_nome.delete(0, "end")
        self.entry_instagram.delete(0, "end")
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

    def on_select_foto(self):
        from customtkinter import filedialog
        path = filedialog.askopenfilename(
            title="Selecionar Foto de Perfil",
            filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if path:
            self.foto_perfil_path = path
            self._update_foto_preview(path)

    def on_remove_foto(self):
        self.foto_perfil_path = None
        self._update_foto_preview(None)

    def _update_foto_preview(self, path):
        if path:
            try:
                from pathlib import Path
                if Path(path).exists():
                    pil_img = create_circular_image(path, (200, 200)) # Qualidade maior
                    if pil_img:
                        ctk_img = ctk.CTkImage(pil_img, size=(100, 100))
                        self.lbl_foto_preview.configure(image=ctk_img, text="", fg_color="transparent")
                        self.lbl_foto_preview._image_ref = ctk_img
                else:
                    self._clear_foto_preview("Arquivo\nnão encontrado")
            except Exception:
                self._clear_foto_preview("Erro")
        else:
            self._clear_foto_preview("📷")

    def _clear_foto_preview(self, text):
        try:
            from PIL import Image
            empty_img = ctk.CTkImage(Image.new("RGBA", (1, 1), (0, 0, 0, 0)), size=(1, 1))
            self.lbl_foto_preview.configure(image=empty_img, text=text, fg_color="gray30")
            self.lbl_foto_preview._image_ref = empty_img
        except Exception:
            self.lbl_foto_preview.configure(image=None, text=text, fg_color="gray30")

    def on_salvar(self) -> None:
        nome = self.entry_nome.get().strip()
        instagram = self.entry_instagram.get().strip() or None
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

        if self.selected_id is None:
            db.execute(
                """
                INSERT INTO alunos
                    (nome, data_nascimento, telefone, email, objetivo, observacoes_medicas, cpf, cep, foto_perfil, instagram)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    self.foto_perfil_path,
                    instagram
                ),
                commit=True,
            )
        else:
            db.execute(
                """
                UPDATE alunos
                SET nome = ?, data_nascimento = ?, telefone = ?, email = ?,
                    objetivo = ?, observacoes_medicas = ?, cpf = ?, cep = ?,
                    foto_perfil = ?, instagram = ?
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
                    self.foto_perfil_path,
                    instagram,
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
