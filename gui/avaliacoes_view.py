import datetime
import os
from pathlib import Path
from tkinter import filedialog, messagebox
import shutil

import customtkinter as ctk
from .input_masks import bind_mask, format_cpf_value, only_digits
from .utils import setup_enter_navigation, create_tooltip, show_toast

try:
    from PIL import Image  # type: ignore[import]
except Exception:  # Pillow opcional; sem ela, não há miniaturas
    Image = None  # type: ignore[assignment]

from database import db
from reports.avaliacao_pdf import gerar_pdf_avaliacao


class AvaliacoesView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        professor_var: ctk.StringVar | None = None,
        get_current_user=None,
    ) -> None:
        super().__init__(master)

        self.selected_id = None
        self.professor_nome_var = professor_var or ctk.StringVar()
        self.get_current_user = get_current_user or (lambda: None)
        
        # Se não foi passado professor_var externo, tenta preencher com o usuário logado
        if self.get_current_user:
            user = self.get_current_user()
            if user:
                nome_user = user.get("nome") or user.get("username") or ""
                self.professor_nome_var.set(nome_user)

        # Layout Principal: 2 colunas (Lista e Detalhes)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        title = ctk.CTkLabel(
            header_frame,
            text="Avaliações Físicas",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(side="left")

        # Container Principal
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        content.grid_columnconfigure(0, weight=1, minsize=300) # Lista (30%)
        content.grid_columnconfigure(1, weight=2, minsize=450) # Detalhes (70%)
        content.grid_rowconfigure(0, weight=1)

        # --- Coluna da Esquerda: Filtros e Lista ---
        left_panel = ctk.CTkFrame(content)
        left_panel.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        left_panel.grid_rowconfigure(2, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        # 1. Filtros Básicos
        filter_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        filter_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        filter_frame.grid_columnconfigure(0, weight=1)

        self.entry_filtro_aluno = ctk.CTkEntry(filter_frame, placeholder_text="🔍 Buscar aluno...")
        self.entry_filtro_aluno.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="ew")
        
        self.combo_filtro_usuario = ctk.CTkComboBox(filter_frame, values=["Todos os profissionais"])
        self.combo_filtro_usuario.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="ew")

        # 2. Filtros Avançados (Expander)
        self.adv_filters_frame = ctk.CTkFrame(left_panel)
        self.adv_filters_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        # Grid para filtros numéricos (2 linhas, 4 colunas)
        for i in range(4): self.adv_filters_frame.grid_columnconfigure(i, weight=1)
        
        # Linha 1
        self.entry_filtro_peso = self._create_mini_filter(self.adv_filters_frame, "Peso ≥", 0, 0)
        self.entry_filtro_altura = self._create_mini_filter(self.adv_filters_frame, "Alt ≥", 0, 1)
        self.entry_filtro_gordura = self._create_mini_filter(self.adv_filters_frame, "%G ≥", 0, 2)
        self.entry_filtro_massa_magra = self._create_mini_filter(self.adv_filters_frame, "M.M ≥", 0, 3)
        
        # Linha 2
        self.entry_filtro_massa_gorda = self._create_mini_filter(self.adv_filters_frame, "M.G ≥", 1, 0)
        self.entry_filtro_ldl = self._create_mini_filter(self.adv_filters_frame, "LDL ≥", 1, 1)
        self.entry_filtro_hdl = self._create_mini_filter(self.adv_filters_frame, "HDL ≥", 1, 2)
        
        btn_filtrar = ctk.CTkButton(self.adv_filters_frame, text="Filtrar", height=24, command=self.load_avaliacoes)
        btn_filtrar.grid(row=1, column=3, padx=2, pady=2, sticky="ew")

        # 3. Lista de Cards (Scrollable)
        self.scroll_list = ctk.CTkScrollableFrame(left_panel)
        self.scroll_list.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # --- Coluna da Direita: Formulário ---
        right_panel = ctk.CTkFrame(content)
        right_panel.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(0, weight=1)

        # Tabs
        tabs = ctk.CTkTabview(right_panel)
        tabs.grid(row=0, column=0, padx=15, pady=(10, 0), sticky="nsew")
        
        tab_id = tabs.add("Identificação")
        tab_ant = tabs.add("Antropometria")
        tab_ana = tabs.add("Anamnese")
        tab_pos = tabs.add("Postural")
        tab_fun = tabs.add("Funcional")
        tab_cf = tabs.add("Cardio/Força")
        
        for t in (tab_id, tab_ant, tab_ana, tab_pos, tab_fun, tab_cf):
            t.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(tab_id, text="Professor:").grid(
            row=0, column=0, padx=10, pady=(10, 5), sticky="e"
        )
        self.entry_professor = ctk.CTkEntry(tab_id, textvariable=self.professor_nome_var, state="readonly")
        self.entry_professor.grid(row=0, column=1, padx=10, pady=(10, 5), sticky="ew")

        ctk.CTkLabel(tab_id, text="Aluno:").grid(
            row=1, column=0, padx=10, pady=5, sticky="e"
        )
        self.combo_aluno = ctk.CTkComboBox(tab_id, values=[])
        self.combo_aluno.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        self.label_criado_por = ctk.CTkLabel(tab_id, text="Criado por: -")
        self.label_criado_por.grid(row=2, column=0, padx=10, pady=(5, 0), sticky="w")
        self.label_atualizado_por = ctk.CTkLabel(tab_id, text="Última atualização: -")
        self.label_atualizado_por.grid(row=2, column=1, padx=10, pady=(5, 0), sticky="e")

        ctk.CTkLabel(tab_id, text="Data:").grid(
            row=3, column=0, padx=10, pady=5, sticky="e"
        )
        self.entry_data = ctk.CTkEntry(tab_id)
        self.entry_data.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        bind_mask(self.entry_data, "date")

        # Cria um container scrollable dentro da tab Antropometria
        self.scroll_ant = ctk.CTkScrollableFrame(tab_ant)
        self.scroll_ant.pack(fill="both", expand=True, padx=0, pady=0)
        self.scroll_ant.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.scroll_ant, text="Peso (kg):").grid(
            row=0, column=0, padx=10, pady=5, sticky="e"
        )
        self.entry_peso = ctk.CTkEntry(self.scroll_ant)
        self.entry_peso.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.scroll_ant, text="Altura (m):").grid(
            row=1, column=0, padx=10, pady=5, sticky="e"
        )
        self.entry_altura = ctk.CTkEntry(self.scroll_ant)
        self.entry_altura.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        imc_frame = ctk.CTkFrame(self.scroll_ant)
        imc_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        imc_frame.grid_columnconfigure(3, weight=1)
        ctk.CTkLabel(imc_frame, text="% Gordura:").grid(
            row=0, column=0, padx=(5, 5), pady=5, sticky="e"
        )
        self.entry_percentual_gordura = ctk.CTkEntry(imc_frame, width=80)
        self.entry_percentual_gordura.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="w")
        self.label_imc = ctk.CTkLabel(
            imc_frame, text="IMC: -", font=ctk.CTkFont(size=12, weight="bold")
        )
        self.label_imc.grid(row=0, column=2, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(imc_frame, text="LDL (mg/dL):").grid(
            row=1, column=0, padx=(5, 5), pady=5, sticky="e"
        )
        self.entry_ldl = ctk.CTkEntry(imc_frame, width=80)
        self.entry_ldl.grid(row=1, column=1, padx=(0, 5), pady=5, sticky="w")
        ctk.CTkLabel(imc_frame, text="HDL (mg/dL):").grid(
            row=1, column=2, padx=(5, 5), pady=5, sticky="e"
        )
        self.entry_hdl = ctk.CTkEntry(imc_frame, width=80)
        self.entry_hdl.grid(row=1, column=3, padx=(0, 5), pady=5, sticky="w")
        self.label_ant_alertas = ctk.CTkLabel(
            imc_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray",
            fg_color="transparent",
            corner_radius=6,
            padx=10,
            pady=6,
        )
        self.label_ant_alertas.grid(
            row=2,
            column=0,
            columnspan=4,
            padx=5,
            pady=(0, 5),
            sticky="ew",
        )

        ctk.CTkLabel(self.scroll_ant, text="Massa magra (kg):").grid(
            row=3, column=0, padx=10, pady=5, sticky="e"
        )
        self.entry_massa_magra = ctk.CTkEntry(self.scroll_ant)
        self.entry_massa_magra.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.scroll_ant, text="Massa gorda (kg):").grid(
            row=4, column=0, padx=10, pady=5, sticky="e"
        )
        self.entry_massa_gorda = ctk.CTkEntry(self.scroll_ant)
        self.entry_massa_gorda.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        fotos_frame = ctk.CTkFrame(self.scroll_ant)
        fotos_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=8, sticky="ew")
        fotos_frame.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(fotos_frame, text="Fotos:").grid(
            row=0, column=0, padx=10, pady=(6, 4), sticky="w"
        )
        self.label_foto_frente = ctk.CTkLabel(
            fotos_frame, text="Nenhum arquivo selecionado", text_color="gray"
        )
        self.label_foto_costas = ctk.CTkLabel(
            fotos_frame, text="Nenhum arquivo selecionado", text_color="gray"
        )
        self.label_foto_lateral_dir = ctk.CTkLabel(
            fotos_frame, text="Nenhum arquivo selecionado", text_color="gray"
        )
        self.label_foto_lateral_esq = ctk.CTkLabel(
            fotos_frame, text="Nenhum arquivo selecionado", text_color="gray"
        )
        ctk.CTkLabel(fotos_frame, text="Vista Anterior (Frente):").grid(
            row=1, column=0, padx=10, pady=4, sticky="e"
        )
        ctk.CTkButton(
            fotos_frame,
            text="Selecionar...",
            width=130,
            command=self.on_select_foto_frente,
        ).grid(row=1, column=1, padx=(0, 4), pady=4, sticky="w")
        self.label_foto_frente.grid(row=1, column=2, padx=4, pady=4, sticky="w")
        ctk.CTkButton(
            fotos_frame,
            text="Limpar",
            width=80,
            command=self.on_clear_foto_frente,
        ).grid(row=1, column=3, padx=4, pady=4, sticky="w")
        ctk.CTkLabel(fotos_frame, text="Vista Posterior (Costas):").grid(
            row=2, column=0, padx=10, pady=4, sticky="e"
        )
        ctk.CTkButton(
            fotos_frame,
            text="Selecionar...",
            width=130,
            command=self.on_select_foto_costas,
        ).grid(row=2, column=1, padx=(0, 4), pady=4, sticky="w")
        self.label_foto_costas.grid(row=2, column=2, padx=4, pady=4, sticky="w")
        ctk.CTkButton(
            fotos_frame,
            text="Limpar",
            width=80,
            command=self.on_clear_foto_costas,
        ).grid(row=2, column=3, padx=4, pady=4, sticky="w")
        ctk.CTkLabel(fotos_frame, text="Vista Lateral Direita:").grid(
            row=3, column=0, padx=10, pady=4, sticky="e"
        )
        ctk.CTkButton(
            fotos_frame,
            text="Selecionar...",
            width=130,
            command=self.on_select_foto_lateral_dir,
        ).grid(row=3, column=1, padx=(0, 4), pady=4, sticky="w")
        self.label_foto_lateral_dir.grid(row=3, column=2, padx=4, pady=4, sticky="w")
        ctk.CTkButton(
            fotos_frame,
            text="Limpar",
            width=80,
            command=self.on_clear_foto_lateral_dir,
        ).grid(row=3, column=3, padx=4, pady=4, sticky="w")
        ctk.CTkLabel(fotos_frame, text="Vista Lateral Esquerda:").grid(
            row=4, column=0, padx=10, pady=4, sticky="e"
        )
        ctk.CTkButton(
            fotos_frame,
            text="Selecionar...",
            width=130,
            command=self.on_select_foto_lateral_esq,
        ).grid(row=4, column=1, padx=(0, 4), pady=4, sticky="w")
        self.label_foto_lateral_esq.grid(row=4, column=2, padx=4, pady=4, sticky="w")
        ctk.CTkButton(
            fotos_frame,
            text="Limpar",
            width=80,
            command=self.on_clear_foto_lateral_esq,
        ).grid(row=4, column=3, padx=4, pady=4, sticky="w")

        btn_ver_fotos = ctk.CTkButton(
            fotos_frame,
            text="Ver fotos",
            width=110,
            command=self.on_ver_fotos,
        )
        btn_ver_fotos.grid(row=0, column=3, padx=4, pady=(6, 4), sticky="e")

        ctk.CTkLabel(self.scroll_ant, text="Dobras cutâneas:").grid(
            row=6, column=0, padx=10, pady=5, sticky="ne"
        )
        self.text_dobras = ctk.CTkTextbox(self.scroll_ant, height=100)
        self.text_dobras.grid(row=6, column=1, padx=10, pady=5, sticky="nsew")

        ctk.CTkLabel(self.scroll_ant, text="Perímetros:").grid(
            row=7, column=0, padx=10, pady=5, sticky="ne"
        )
        self.text_perimetros = ctk.CTkTextbox(self.scroll_ant, height=100)
        self.text_perimetros.grid(row=7, column=1, padx=10, pady=5, sticky="nsew")

        # paths state
        self.foto_frente_src: str | None = None
        self.foto_costas_src: str | None = None
        self.foto_lateral_dir_src: str | None = None
        self.foto_lateral_esq_src: str | None = None
        self.foto_frente_db: str | None = None
        self.foto_costas_db: str | None = None
        self.foto_lateral_dir_db: str | None = None
        self.foto_lateral_esq_db: str | None = None

        ctk.CTkLabel(tab_ana, text="Anamnese:").grid(
            row=0, column=0, padx=10, pady=5, sticky="ne"
        )
        self.text_anamnese = ctk.CTkTextbox(tab_ana, height=80)
        self.text_anamnese.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
        ctk.CTkLabel(
            tab_ana,
            text="Ex.: queixas, histórico familiar, sintomas atuais.",
            font=ctk.CTkFont(size=10),
        ).grid(row=1, column=1, padx=10, pady=(0, 6), sticky="w")

        ctk.CTkLabel(tab_ana, text="Histórico de saúde:").grid(
            row=2, column=0, padx=10, pady=5, sticky="ne"
        )
        self.text_historico_saude = ctk.CTkTextbox(tab_ana, height=60)
        self.text_historico_saude.grid(row=2, column=1, padx=10, pady=5, sticky="nsew")
        hist_checks = ctk.CTkFrame(tab_ana)
        hist_checks.grid(row=3, column=1, padx=10, pady=(0, 6), sticky="ew")
        self.chk_diabetes = ctk.CTkCheckBox(hist_checks, text="Diabetes")
        self.chk_diabetes.grid(row=0, column=0, padx=(0, 8), pady=2, sticky="w")
        self.chk_hipertensao = ctk.CTkCheckBox(hist_checks, text="Hipertensão")
        self.chk_hipertensao.grid(row=0, column=1, padx=(0, 8), pady=2, sticky="w")
        self.chk_lesoes = ctk.CTkCheckBox(hist_checks, text="Lesões")
        self.chk_lesoes.grid(row=0, column=2, padx=(0, 8), pady=2, sticky="w")
        self.chk_cirurgias = ctk.CTkCheckBox(hist_checks, text="Cirurgias")
        self.chk_cirurgias.grid(row=0, column=3, padx=(0, 8), pady=2, sticky="w")

        ctk.CTkLabel(tab_ana, text="Estilo de vida:").grid(
            row=4, column=0, padx=10, pady=5, sticky="ne"
        )
        self.text_estilo_vida = ctk.CTkTextbox(tab_ana, height=60)
        self.text_estilo_vida.grid(row=4, column=1, padx=10, pady=5, sticky="nsew")
        ctk.CTkLabel(
            tab_ana,
            text="Ex.: atividade física, tabagismo, alimentação, sono.",
            font=ctk.CTkFont(size=10),
        ).grid(row=5, column=1, padx=10, pady=(0, 6), sticky="w")

        ctk.CTkLabel(tab_ana, text="Metas do aluno:").grid(
            row=6, column=0, padx=10, pady=5, sticky="ne"
        )
        self.text_metas = ctk.CTkTextbox(tab_ana, height=60)
        self.text_metas.grid(row=6, column=1, padx=10, pady=5, sticky="nsew")
        ctk.CTkLabel(
            tab_ana,
            text="Ex.: hipertrofia, emagrecimento, condicionamento, reabilitação.",
            font=ctk.CTkFont(size=10),
        ).grid(row=7, column=1, padx=10, pady=(0, 6), sticky="w")

        ctk.CTkLabel(tab_pos, text="Avaliação postural:").grid(
            row=0, column=0, padx=10, pady=5, sticky="ne"
        )
        self.text_postura = ctk.CTkTextbox(tab_pos, height=100)
        self.text_postura.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
        ctk.CTkLabel(
            tab_pos,
            text="Ex.: desvios, assimetrias, pontos de tensão.",
            font=ctk.CTkFont(size=10),
        ).grid(row=1, column=1, padx=10, pady=(0, 6), sticky="w")

        ctk.CTkLabel(tab_fun, text="Funcional e mobilidade:").grid(
            row=0, column=0, padx=10, pady=5, sticky="ne"
        )
        self.text_funcional = ctk.CTkTextbox(tab_fun, height=100)
        self.text_funcional.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
        ctk.CTkLabel(
            tab_fun,
            text="Ex.: agachamento, passadas, core, tornozelo/quadril/ombro.",
            font=ctk.CTkFont(size=10),
        ).grid(row=1, column=1, padx=10, pady=(0, 6), sticky="w")

        ctk.CTkLabel(tab_cf, text="Teste cardiorrespiratório:").grid(
            row=0, column=0, padx=10, pady=5, sticky="ne"
        )
        self.text_cardio = ctk.CTkTextbox(tab_cf, height=60)
        self.text_cardio.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
        ctk.CTkLabel(
            tab_cf,
            text="Ex.: esteira/bike, FC, percepção de esforço.",
            font=ctk.CTkFont(size=10),
        ).grid(row=1, column=1, padx=10, pady=(0, 6), sticky="w")

        ctk.CTkLabel(tab_cf, text="Força/Resistência:").grid(
            row=2, column=0, padx=10, pady=5, sticky="ne"
        )
        self.text_forca = ctk.CTkTextbox(tab_cf, height=60)
        self.text_forca.grid(row=2, column=1, padx=10, pady=5, sticky="nsew")
        ctk.CTkLabel(
            tab_cf,
            text="Ex.: 1RM estimada, flexões, abdominais, repetições.",
            font=ctk.CTkFont(size=10),
        ).grid(row=3, column=1, padx=10, pady=(0, 6), sticky="w")
        
        setup_enter_navigation(tabs)
        
        # Botões de Ação (Footer do Right Panel)
        actions_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        actions_frame.grid(row=1, column=0, padx=15, pady=15, sticky="ew")
        actions_frame.grid_columnconfigure(0, weight=1)

        btn_novo = ctk.CTkButton(actions_frame, text="+ Nova Avaliação", command=self.on_novo, fg_color="#2ecc71", hover_color="#27ae60")
        btn_novo.pack(side="left", padx=(0, 10))
        create_tooltip(btn_novo, "Limpar formulário para nova avaliação")

        btn_salvar = ctk.CTkButton(actions_frame, text="💾 Salvar", command=self.on_salvar)
        btn_salvar.pack(side="left", padx=(0, 10))
        create_tooltip(btn_salvar, "Gravar avaliação no banco de dados")

        btn_pdf = ctk.CTkButton(actions_frame, text="📄 PDF", command=self.on_gerar_pdf, fg_color="#3498db", hover_color="#2980b9")
        btn_pdf.pack(side="left", padx=(0, 10))
        create_tooltip(btn_pdf, "Gerar relatório detalhado em PDF")
        
        btn_excluir = ctk.CTkButton(actions_frame, text="🗑️ Excluir", command=self.on_excluir, fg_color="#e74c3c", hover_color="#c0392b")
        btn_excluir.pack(side="right")
        create_tooltip(btn_excluir, "Excluir avaliação selecionada")

        self.entry_peso.bind("<KeyRelease>", self.on_imc_change)
        self.entry_altura.bind("<KeyRelease>", self.on_imc_change)
        self.entry_percentual_gordura.bind("<KeyRelease>", self.on_imc_change)
        self.entry_massa_magra.bind("<KeyRelease>", self.on_imc_change)
        self.entry_ldl.bind("<KeyRelease>", self.on_imc_change)
        self.entry_hdl.bind("<KeyRelease>", self.on_imc_change)

        self.load_alunos()
        self._load_usuarios_filtro()
        self.on_novo()
        self.load_avaliacoes()

    def _create_mini_filter(self, parent, text, row, col):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, padx=2, pady=2, sticky="ew")
        
        lbl = ctk.CTkLabel(frame, text=text, font=ctk.CTkFont(size=10))
        lbl.pack(side="left", padx=(0, 2))
        
        entry = ctk.CTkEntry(frame, width=50, height=24, font=ctk.CTkFont(size=11))
        entry.pack(side="left", fill="x", expand=True)
        return entry

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

    def _set_foto_label(self, lbl: ctk.CTkLabel, path: str | None) -> None:
        if path:
            try:
                name = Path(path).name
            except Exception:
                name = str(path)
            lbl.configure(text=name, text_color="white")
        else:
            lbl.configure(text="Nenhum arquivo selecionado", text_color="gray")

    def on_select_foto_frente(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecionar foto (Vista Anterior)",
            filetypes=[("Imagens", "*.jpg;*.jpeg;*.png;*.webp;*.bmp")],
        )
        if path:
            self.foto_frente_src = path
            self._set_foto_label(self.label_foto_frente, path)

    def on_select_foto_costas(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecionar foto (Vista Posterior)",
            filetypes=[("Imagens", "*.jpg;*.jpeg;*.png;*.webp;*.bmp")],
        )
        if path:
            self.foto_costas_src = path
            self._set_foto_label(self.label_foto_costas, path)

    def on_select_foto_lateral_dir(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecionar foto (Vista Lateral Direita)",
            filetypes=[("Imagens", "*.jpg;*.jpeg;*.png;*.webp;*.bmp")],
        )
        if path:
            self.foto_lateral_dir_src = path
            self._set_foto_label(self.label_foto_lateral_dir, path)

    def on_select_foto_lateral_esq(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecionar foto (Vista Lateral Esquerda)",
            filetypes=[("Imagens", "*.jpg;*.jpeg;*.png;*.webp;*.bmp")],
        )
        if path:
            self.foto_lateral_esq_src = path
            self._set_foto_label(self.label_foto_lateral_esq, path)

    def on_clear_foto_frente(self) -> None:
        self.foto_frente_src = None
        self.foto_frente_db = None
        self._set_foto_label(self.label_foto_frente, None)

    def on_clear_foto_costas(self) -> None:
        self.foto_costas_src = None
        self.foto_costas_db = None
        self._set_foto_label(self.label_foto_costas, None)

    def on_clear_foto_lateral_dir(self) -> None:
        self.foto_lateral_dir_src = None
        self.foto_lateral_dir_db = None
        self._set_foto_label(self.label_foto_lateral_dir, None)

    def on_clear_foto_lateral_esq(self) -> None:
        self.foto_lateral_esq_src = None
        self.foto_lateral_esq_db = None
        self._set_foto_label(self.label_foto_lateral_esq, None)

    def _resolve_path(self, path_str: str | None) -> Path | None:
        if not path_str:
            return None
        p = Path(path_str)
        if p.is_absolute():
            return p
        # relativo à raiz do projeto
        base_dir = Path(__file__).resolve().parent.parent
        return base_dir / p

    def on_ver_fotos(self) -> None:
        fotos = [
            ("Vista Anterior (Frente)", self.foto_frente_src or self.foto_frente_db),
            ("Vista Posterior (Costas)", self.foto_costas_src or self.foto_costas_db),
            ("Vista Lateral Direita", self.foto_lateral_dir_src or self.foto_lateral_dir_db),
            ("Vista Lateral Esquerda", self.foto_lateral_esq_src or self.foto_lateral_esq_db),
        ]

        window = ctk.CTkToplevel(self)
        window.title("Fotos da avaliação")
        window.geometry("900x500")
        window.grab_set()
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(0, weight=1)

        container = ctk.CTkScrollableFrame(window)
        container.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        container.grid_columnconfigure(1, weight=1)

        if not hasattr(self, "_foto_thumbs"):
            self._foto_thumbs = []
        else:
            self._foto_thumbs.clear()

        for i, (titulo, caminho) in enumerate(fotos):
            ctk.CTkLabel(container, text=titulo).grid(
                row=i, column=0, padx=(0, 10), pady=5, sticky="ne"
            )
            
            path_obj = self._resolve_path(caminho)

            if not path_obj or not path_obj.exists():
                ctk.CTkLabel(
                    container,
                    text="Sem foto",
                    text_color="gray",
                ).grid(row=i, column=1, columnspan=2, padx=(0, 0), pady=5, sticky="w")
                continue

            if Image is None:
                ctk.CTkLabel(
                    container,
                    text=path_obj.name,
                ).grid(row=i, column=1, padx=(0, 10), pady=5, sticky="w")
            else:
                try:
                    img = Image.open(path_obj)
                    thumb = img.copy()
                    thumb.thumbnail((220, 260))
                    ctk_img = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=thumb.size)
                    self._foto_thumbs.append(ctk_img)
                    preview = ctk.CTkLabel(container, image=ctk_img, text="")
                    preview.grid(row=i, column=1, padx=(0, 10), pady=5, sticky="w")
                except Exception:
                    ctk.CTkLabel(
                        container,
                        text=path_obj.name,
                    ).grid(row=i, column=1, padx=(0, 10), pady=5, sticky="w")

            btn = ctk.CTkButton(
                container,
                text="Abrir foto",
                width=110,
                command=lambda p=caminho: self._abrir_foto(p),
            )
            btn.grid(row=i, column=2, padx=(0, 0), pady=5, sticky="w")

    def _abrir_foto(self, caminho: str) -> None:
        path_obj = self._resolve_path(caminho)
        if not path_obj:
            return
        try:
            if not path_obj.exists():
                messagebox.showwarning(
                    "Avaliações", "Arquivo de foto não encontrado."
                )
                return
            try:
                os.startfile(path_obj)
            except Exception:
                messagebox.showwarning(
                    "Avaliações", "Não foi possível abrir a foto neste sistema."
                )
        except Exception:
            messagebox.showwarning(
                "Avaliações", "Não foi possível abrir a foto selecionada."
            )

    def _copy_foto(self, src: str | None, id_aluno: int, tipo: str) -> str | None:
        if not src:
            return None
        try:
            base_dir = Path(__file__).resolve().parent.parent
            media_dir = base_dir / "media" / "avaliacoes" / str(id_aluno)
            media_dir.mkdir(parents=True, exist_ok=True)
            ext = "".join(Path(src).suffixes) or ".jpg"
            ts = int(datetime.datetime.now().timestamp())
            dest = media_dir / f"{ts}_{tipo}{ext}"
            shutil.copyfile(src, dest)
            try:
                rel = dest.relative_to(base_dir)
                return str(rel)
            except ValueError:
                return str(dest)
        except Exception:
            messagebox.showwarning(
                "Avaliações",
                "Não foi possível copiar a foto selecionada. Verifique o arquivo.",
            )
            return None

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

    def load_avaliacoes(self) -> None:
        # Limpa lista atual
        for widget in self.scroll_list.winfo_children():
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

        def parse_filter(value: str) -> float | None:
            value = value.strip()
            if not value:
                return None
            try:
                return float(value.replace(",", "."))
            except Exception:
                return None

        peso_min = parse_filter(self.entry_filtro_peso.get())
        altura_min = parse_filter(self.entry_filtro_altura.get())
        gordura_min = parse_filter(self.entry_filtro_gordura.get())
        ldl_min = parse_filter(self.entry_filtro_ldl.get())
        hdl_min = parse_filter(self.entry_filtro_hdl.get())
        massa_magra_min = parse_filter(self.entry_filtro_massa_magra.get())
        massa_gorda_min = parse_filter(self.entry_filtro_massa_gorda.get())

        user = self.get_current_user() if self.get_current_user else None
        is_admin = bool(user and user.get("is_admin"))
        user_id = user.get("id") if user else None

        query = """
            SELECT af.id, af.data, af.peso, af.altura,
                   af.percentual_gordura, af.massa_magra, af.massa_gorda,
                   af.ldl, af.hdl,
                   al.nome AS nome_aluno, al.cpf AS cpf,
                   uc.username AS username_criacao, uc.nome AS nome_criacao
            FROM avaliacoes_fisicas af
            JOIN alunos al ON al.id = af.id_aluno
            LEFT JOIN usuarios uc ON uc.id = af.id_usuario_criacao
            WHERE 1=1
        """
        params: list[float | str | int] = []

        # Se NÃO for admin, filtra apenas avaliações criadas pelo usuário
        if not is_admin and user_id:
            query += " AND af.id_usuario_criacao = ?"
            params.append(user_id)

        if filtro:
            query += " AND al.nome LIKE ?"
            params.append(f"%{filtro}%")
        # Se um filtro específico de usuário foi selecionado (e o usuário atual for admin, ou filtro redundante)
        if usuario_id is not None:
             # Se não for admin, o filtro acima já restringiu. Se for admin, aplica filtro da UI.
             if is_admin:
                query += " AND af.id_usuario_criacao = ?"
                params.append(usuario_id)

        if peso_min is not None:
            query += " AND af.peso >= ?"
            params.append(peso_min)
        if altura_min is not None:
            query += " AND af.altura >= ?"
            params.append(altura_min)
        if gordura_min is not None:
            query += " AND af.percentual_gordura >= ?"
            params.append(gordura_min)
        if ldl_min is not None:
            query += " AND af.ldl >= ?"
            params.append(ldl_min)
        if hdl_min is not None:
            query += " AND af.hdl >= ?"
            params.append(hdl_min)
        if massa_magra_min is not None:
            query += " AND af.massa_magra >= ?"
            params.append(massa_magra_min)
        if massa_gorda_min is not None:
            query += " AND af.massa_gorda >= ?"
            params.append(massa_gorda_min)

        query += " ORDER BY af.data DESC"

        rows = db.fetch_all(query, tuple(params))

        if not rows:
            ctk.CTkLabel(self.scroll_list, text="Nenhuma avaliação encontrada.", text_color="gray").pack(pady=20)
            return

        for row in rows:
            self._create_card(row)

    def _create_card(self, row: dict) -> None:
        card = ctk.CTkFrame(self.scroll_list, fg_color=("gray90", "gray20"), corner_radius=8)
        card.pack(fill="x", pady=4, padx=2)

        # Dados principais
        data_br = row["data"]
        try:
            if row["data"]:
                data_br = datetime.date.fromisoformat(row["data"]).strftime("%d/%m/%Y")
        except Exception:
            pass

        peso = row["peso"]
        altura = row["altura"]
        imc = "-"
        if peso and altura:
            try:
                imc_val = float(peso) / (float(altura) ** 2)
                imc = f"{imc_val:.1f}"
            except Exception:
                pass

        prof_nome = row["nome_criacao"] or row["username_criacao"] or "N/A"

        # Linha 1: Nome e Data
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 0))
        
        lbl_nome = ctk.CTkLabel(header, text=row["nome_aluno"], font=ctk.CTkFont(size=14, weight="bold"))
        lbl_nome.pack(side="left")
        
        lbl_data = ctk.CTkLabel(header, text=data_br, font=ctk.CTkFont(size=12), text_color="gray")
        lbl_data.pack(side="right")

        # Linha 2: Métricas Resumidas
        metrics = []
        if peso: metrics.append(f"{peso}kg")
        if imc != "-": metrics.append(f"IMC {imc}")
        if row["percentual_gordura"]: metrics.append(f"{row['percentual_gordura']}% G")
        
        lbl_metrics = ctk.CTkLabel(card, text=" | ".join(metrics), font=ctk.CTkFont(size=12))
        lbl_metrics.pack(fill="x", padx=10, pady=(2, 0), anchor="w")

        # Linha 3: Profissional
        lbl_prof = ctk.CTkLabel(card, text=f"Prof: {prof_nome}", font=ctk.CTkFont(size=11), text_color="gray")
        lbl_prof.pack(fill="x", padx=10, pady=(2, 8), anchor="w")

        # Bind click events
        for widget in (card, header, lbl_nome, lbl_data, lbl_metrics, lbl_prof):
            widget.bind("<Button-1>", lambda e, aid=row["id"]: self.load_avaliacao_details(aid))
            widget.bind("<Enter>", lambda e, c=card: c.configure(border_width=1, border_color="gray50"))
            widget.bind("<Leave>", lambda e, c=card: c.configure(border_width=0))

    def load_avaliacao_details(self, avaliacao_id: int) -> None:
        self.selected_id = avaliacao_id
        row = db.fetch_one(
            """
            SELECT af.id, af.id_aluno, af.data, af.peso, af.altura,
                   af.percentual_gordura, af.massa_magra, af.massa_gorda,
                   af.dobras_cutaneas, af.perimetros, af.anamnese,
                   af.historico_saude, af.estilo_vida, af.metas,
                   af.postura, af.funcional_mobilidade, af.cardio, af.forca_resistencia,
                   af.ldl, af.hdl,
                   af.foto_frente, af.foto_costas, af.foto_lateral_dir, af.foto_lateral_esq,
                   uc.username AS username_criacao, uc.nome AS nome_criacao,
                   uu.username AS username_atualizacao, uu.nome AS nome_atualizacao
            FROM avaliacoes_fisicas af
            LEFT JOIN usuarios uc ON uc.id = af.id_usuario_criacao
            LEFT JOIN usuarios uu ON uu.id = af.id_usuario_atualizacao
            WHERE af.id = ?
            """,
            (self.selected_id,),
        )
        if row is None:
            return

        aluno_row = db.fetch_one(
            "SELECT id, nome FROM alunos WHERE id = ?", (row["id_aluno"],)
        )
        if aluno_row is not None:
            aluno_str = f"{aluno_row['id']:04d} - {aluno_row['nome']}"
            self.combo_aluno.set(aluno_str)

        self.entry_data.delete(0, "end")
        try:
            if row["data"]:
                d = datetime.date.fromisoformat(row["data"])
                self.entry_data.insert(0, d.strftime("%d/%m/%Y"))
        except Exception:
            self.entry_data.insert(0, row["data"] or "")

        self.entry_peso.delete(0, "end")
        self.entry_peso.insert(0, str(row["peso"] or ""))

        self.entry_altura.delete(0, "end")
        self.entry_altura.insert(0, str(row["altura"] or ""))

        self.entry_percentual_gordura.delete(0, "end")
        if row["percentual_gordura"] is not None:
            self.entry_percentual_gordura.insert(
                0, str(row["percentual_gordura"])
            )

        self.entry_massa_magra.delete(0, "end")
        if row["massa_magra"] is not None:
            self.entry_massa_magra.insert(0, str(row["massa_magra"]))

        self.entry_massa_gorda.delete(0, "end")
        if "massa_gorda" in row.keys() and row["massa_gorda"] is not None:
            self.entry_massa_gorda.insert(0, str(row["massa_gorda"]))

        self.entry_ldl.delete(0, "end")
        if "ldl" in row.keys() and row["ldl"] is not None:
            self.entry_ldl.insert(0, str(row["ldl"]))

        self.entry_hdl.delete(0, "end")
        if "hdl" in row.keys() and row["hdl"] is not None:
            self.entry_hdl.insert(0, str(row["hdl"]))

        self.text_dobras.configure(state="normal")
        self.text_dobras.delete("1.0", "end")
        if row["dobras_cutaneas"]:
            self.text_dobras.insert("end", row["dobras_cutaneas"])
        self.text_dobras.configure(state="normal")

        self.text_perimetros.configure(state="normal")
        self.text_perimetros.delete("1.0", "end")
        if row["perimetros"]:
            self.text_perimetros.insert("end", row["perimetros"])
        self.text_perimetros.configure(state="normal")

        self.text_anamnese.configure(state="normal")
        self.text_anamnese.delete("1.0", "end")
        if row["anamnese"]:
            self.text_anamnese.insert("end", row["anamnese"])
        self.text_anamnese.configure(state="normal")

        criado = row["nome_criacao"] or row["username_criacao"] or "-"
        atualizado = row["nome_atualizacao"] or row["username_atualizacao"] or "-"
        self.label_criado_por.configure(text=f"Criado por: {criado}")
        self.label_atualizado_por.configure(text=f"Última atualização: {atualizado}")

        self.text_historico_saude.configure(state="normal")
        self.text_historico_saude.delete("1.0", "end")
        if row["historico_saude"]:
            self.text_historico_saude.insert("end", row["historico_saude"])
        self.text_historico_saude.configure(state="normal")

        self.text_estilo_vida.configure(state="normal")
        self.text_estilo_vida.delete("1.0", "end")
        if row["estilo_vida"]:
            self.text_estilo_vida.insert("end", row["estilo_vida"])
        self.text_estilo_vida.configure(state="normal")

        self.text_metas.configure(state="normal")
        self.text_metas.delete("1.0", "end")
        if row["metas"]:
            self.text_metas.insert("end", row["metas"])
        self.text_metas.configure(state="normal")

        self.text_postura.configure(state="normal")
        self.text_postura.delete("1.0", "end")
        if row["postura"]:
            self.text_postura.insert("end", row["postura"])
        self.text_postura.configure(state="normal")

        self.text_funcional.configure(state="normal")
        self.text_funcional.delete("1.0", "end")
        if row["funcional_mobilidade"]:
            self.text_funcional.insert("end", row["funcional_mobilidade"])
        self.text_funcional.configure(state="normal")

        self.text_cardio.configure(state="normal")
        self.text_cardio.delete("1.0", "end")
        if row["cardio"]:
            self.text_cardio.insert("end", row["cardio"])
        self.text_cardio.configure(state="normal")

        self.text_forca.configure(state="normal")
        self.text_forca.delete("1.0", "end")
        if row["forca_resistencia"]:
            self.text_forca.insert("end", row["forca_resistencia"])
        self.text_forca.configure(state="normal")

        # fotos
        try:
            self.foto_frente_db = row["foto_frente"]
            self.foto_costas_db = row["foto_costas"]
            self.foto_lateral_dir_db = row["foto_lateral_dir"]
            self.foto_lateral_esq_db = row["foto_lateral_esq"]
        except Exception:
            self.foto_frente_db = None
            self.foto_costas_db = None
            self.foto_lateral_dir_db = None
            self.foto_lateral_esq_db = None
        self.foto_frente_src = None
        self.foto_costas_src = None
        self.foto_lateral_dir_src = None
        self.foto_lateral_esq_src = None
        self._set_foto_label(self.label_foto_frente, self.foto_frente_db)
        self._set_foto_label(self.label_foto_costas, self.foto_costas_db)
        self._set_foto_label(self.label_foto_lateral_dir, self.foto_lateral_dir_db)
        self._set_foto_label(self.label_foto_lateral_esq, self.foto_lateral_esq_db)

        self.update_imc_label()

    def on_novo(self) -> None:
        self.selected_id = None
        self.combo_aluno.set("")
        self.entry_data.delete(0, "end")

        self.entry_peso.delete(0, "end")
        self.entry_altura.delete(0, "end")
        self.entry_percentual_gordura.delete(0, "end")
        self.entry_massa_magra.delete(0, "end")
        self.entry_massa_gorda.delete(0, "end")
        self.entry_ldl.delete(0, "end")
        self.entry_hdl.delete(0, "end")
        self.label_ant_alertas.configure(
            text="",
            text_color="gray",
            fg_color="transparent",
        )

        self.text_dobras.configure(state="normal")
        self.text_dobras.delete("1.0", "end")
        self.text_dobras.configure(state="normal")

        self.text_perimetros.configure(state="normal")
        self.text_perimetros.delete("1.0", "end")
        self.text_perimetros.configure(state="normal")

        self.text_anamnese.configure(state="normal")
        self.text_anamnese.delete("1.0", "end")
        self.text_anamnese.configure(state="normal")
        try:
            self.chk_diabetes.deselect()
            self.chk_hipertensao.deselect()
            self.chk_lesoes.deselect()
            self.chk_cirurgias.deselect()
        except Exception:
            pass

        self.text_historico_saude.configure(state="normal")
        self.text_historico_saude.delete("1.0", "end")
        self.text_historico_saude.configure(state="normal")

        self.text_estilo_vida.configure(state="normal")
        self.text_estilo_vida.delete("1.0", "end")
        self.text_estilo_vida.configure(state="normal")

        self.text_metas.configure(state="normal")
        self.text_metas.delete("1.0", "end")
        self.text_metas.configure(state="normal")

        self.text_postura.configure(state="normal")
        self.text_postura.delete("1.0", "end")
        self.text_postura.configure(state="normal")

        self.text_funcional.configure(state="normal")
        self.text_funcional.delete("1.0", "end")
        self.text_funcional.configure(state="normal")

        self.text_cardio.configure(state="normal")
        self.text_cardio.delete("1.0", "end")
        self.text_cardio.configure(state="normal")

        self.text_forca.configure(state="normal")
        self.text_forca.delete("1.0", "end")
        self.text_forca.configure(state="normal")

        self.update_imc_label()

        self.foto_frente_src = None
        self.foto_costas_src = None
        self.foto_lateral_dir_src = None
        self.foto_lateral_esq_src = None
        self.foto_frente_db = None
        self.foto_costas_db = None
        self.foto_lateral_dir_db = None
        self.foto_lateral_esq_db = None
        self._set_foto_label(self.label_foto_frente, None)
        self._set_foto_label(self.label_foto_costas, None)
        self._set_foto_label(self.label_foto_lateral_dir, None)
        self._set_foto_label(self.label_foto_lateral_esq, None)

        if hasattr(self, "label_criado_por"):
            self.label_criado_por.configure(text="Criado por: -")
        if hasattr(self, "label_atualizado_por"):
            self.label_atualizado_por.configure(text="Última atualização: -")

    def on_imc_change(self, event) -> None:
        self.update_imc_label()

    def update_imc_label(self) -> None:
        def to_float(value: str) -> float | None:
            value = value.strip()
            if not value:
                return None
            try:
                return float(value.replace(",", "."))
            except Exception:
                return None

        peso_str = self.entry_peso.get().strip()
        altura_str = self.entry_altura.get().strip()
        perc_str = self.entry_percentual_gordura.get().strip()
        massa_magra_str = self.entry_massa_magra.get().strip()
        ldl_str = self.entry_ldl.get().strip()
        hdl_str = self.entry_hdl.get().strip()

        peso = to_float(peso_str) if peso_str else None
        altura = to_float(altura_str) if altura_str else None
        percentual = to_float(perc_str) if perc_str else None
        massa_magra_val = to_float(massa_magra_str) if massa_magra_str else None
        ldl_val = to_float(ldl_str) if ldl_str else None
        hdl_val = to_float(hdl_str) if hdl_str else None

        if not peso or not altura or altura <= 0:
            self.label_imc.configure(text="IMC: -")
        else:
            try:
                imc = peso / (altura**2)
                self.label_imc.configure(text=f"IMC: {imc:.2f}")
            except Exception:
                self.label_imc.configure(text="IMC: -")

        massa_gorda_est = None
        if peso and percentual is not None:
            try:
                massa_gorda_est = peso * (percentual / 100.0)
            except Exception:
                massa_gorda_est = None
        elif peso and massa_magra_val is not None:
            try:
                massa_gorda_est = peso - massa_magra_val
            except Exception:
                massa_gorda_est = None

        alertas = []
        if percentual is not None and percentual >= 30:
            alertas.append("Gordura corporal elevada")
        if ldl_val is not None:
            if ldl_val >= 160:
                alertas.append("LDL alto")
            elif ldl_val >= 130:
                alertas.append("LDL limítrofe")
        if hdl_val is not None and hdl_val < 40:
            alertas.append("HDL baixo")

        partes = []
        if massa_magra_val is not None:
            partes.append(f"Massa magra: {massa_magra_val:.1f} kg")
        if massa_gorda_est is not None:
            partes.append(f"Massa gorda (estimada): {massa_gorda_est:.1f} kg")

        texto_alertas = ""
        if partes:
            texto_alertas = " | ".join(partes)
        if alertas:
            if texto_alertas:
                texto_alertas += "  –  "
            texto_alertas += "; ".join(alertas)

        if texto_alertas:
            self.label_ant_alertas.configure(
                text=texto_alertas,
                text_color="#ffecec",
                fg_color="#b00020",
            )
        else:
            self.label_ant_alertas.configure(
                text="",
                text_color="gray",
                fg_color="transparent",
            )

    def on_salvar(self) -> None:
        id_aluno = self._get_selected_aluno_id()
        if id_aluno is None:
            messagebox.showwarning("Avaliações", "Selecione um aluno.")
            return

        data_str = self.entry_data.get().strip()
        if not data_str:
            data = datetime.date.today().isoformat()
        else:
            try:
                d = datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
                data = d.isoformat()
            except ValueError:
                messagebox.showwarning(
                    "Avaliações", "Data inválida. Use o formato DD/MM/AAAA."
                )
                return

        def parse_float(value: str) -> float | None:
            value = value.strip()
            if not value:
                return None
            try:
                return float(value.replace(",", "."))
            except Exception:
                return None

        peso_str = self.entry_peso.get()
        altura_str = self.entry_altura.get()
        peso = parse_float(peso_str)
        altura = parse_float(altura_str)
        percentual_gordura = parse_float(self.entry_percentual_gordura.get())
        massa_magra = parse_float(self.entry_massa_magra.get())
        massa_gorda = parse_float(self.entry_massa_gorda.get())
        ldl = parse_float(self.entry_ldl.get())
        hdl = parse_float(self.entry_hdl.get())

        if peso_str.strip() and peso is None:
            messagebox.showwarning("Avaliações", "Peso inválido.")
            return
        if altura_str.strip() and altura is None:
            messagebox.showwarning("Avaliações", "Altura inválida.")
            return

        if peso is not None and percentual_gordura is not None:
            try:
                massa_gorda_calc = peso * (percentual_gordura / 100.0)
                if massa_gorda is None:
                    massa_gorda = massa_gorda_calc
                if massa_magra is None:
                    massa_magra = peso - massa_gorda_calc
            except Exception:
                pass

        dobras = self.text_dobras.get("1.0", "end").strip() or None
        perimetros = self.text_perimetros.get("1.0", "end").strip() or None
        anamnese = self.text_anamnese.get("1.0", "end").strip() or None
        historico_saude = self.text_historico_saude.get("1.0", "end").strip() or None
        # incorpora checklist selecionado ao texto
        checks = []
        if getattr(self, "chk_diabetes").get():
            checks.append("Diabetes")
        if getattr(self, "chk_hipertensao").get():
            checks.append("Hipertensão")
        if getattr(self, "chk_lesoes").get():
            checks.append("Lesões")
        if getattr(self, "chk_cirurgias").get():
            checks.append("Cirurgias")
        if checks:
            prefixo = "Condições: " + ", ".join(checks)
            if historico_saude:
                historico_saude = prefixo + "; " + historico_saude
            else:
                historico_saude = prefixo
        estilo_vida = self.text_estilo_vida.get("1.0", "end").strip() or None
        metas = self.text_metas.get("1.0", "end").strip() or None
        postura = self.text_postura.get("1.0", "end").strip() or None
        funcional = self.text_funcional.get("1.0", "end").strip() or None
        cardio = self.text_cardio.get("1.0", "end").strip() or None
        forca = self.text_forca.get("1.0", "end").strip() or None

        # prepara caminhos das fotos (cópia para pasta gerenciada)
        foto_frente = self._copy_foto(self.foto_frente_src, id_aluno, "frente") or self.foto_frente_db
        foto_costas = self._copy_foto(self.foto_costas_src, id_aluno, "costas") or self.foto_costas_db
        foto_lateral_dir = self._copy_foto(self.foto_lateral_dir_src, id_aluno, "lateral_dir") or self.foto_lateral_dir_db
        foto_lateral_esq = self._copy_foto(self.foto_lateral_esq_src, id_aluno, "lateral_esq") or self.foto_lateral_esq_db

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
                INSERT INTO avaliacoes_fisicas
                    (id_aluno, data, peso, altura,
                     percentual_gordura, massa_magra, massa_gorda,
                     dobras_cutaneas, perimetros, anamnese,
                     historico_saude, estilo_vida, metas,
                     postura, funcional_mobilidade, cardio, forca_resistencia,
                     ldl, hdl,
                     foto_frente, foto_costas, foto_lateral_dir, foto_lateral_esq,
                     id_usuario_criacao, id_usuario_atualizacao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    id_aluno,
                    data,
                    peso,
                    altura,
                    percentual_gordura,
                    massa_magra,
                    massa_gorda,
                    dobras,
                    perimetros,
                    anamnese,
                    historico_saude,
                    estilo_vida,
                    metas,
                    postura,
                    funcional,
                    cardio,
                    forca,
                    ldl,
                    hdl,
                    foto_frente,
                    foto_costas,
                    foto_lateral_dir,
                    foto_lateral_esq,
                    user_id,
                    user_id,
                ),
                commit=True,
            )
        else:
            db.execute(
                """
                UPDATE avaliacoes_fisicas
                SET id_aluno = ?, data = ?, peso = ?, altura = ?,
                    percentual_gordura = ?, massa_magra = ?, massa_gorda = ?,
                    dobras_cutaneas = ?, perimetros = ?, anamnese = ?,
                    historico_saude = ?, estilo_vida = ?, metas = ?,
                    postura = ?, funcional_mobilidade = ?, cardio = ?, forca_resistencia = ?,
                    ldl = ?, hdl = ?,
                    foto_frente = ?, foto_costas = ?, foto_lateral_dir = ?, foto_lateral_esq = ?,
                    id_usuario_atualizacao = ?
                WHERE id = ?
                """,
                (
                    id_aluno,
                    data,
                    peso,
                    altura,
                    percentual_gordura,
                    massa_magra,
                    massa_gorda,
                    dobras,
                    perimetros,
                    anamnese,
                    historico_saude,
                    estilo_vida,
                    metas,
                    postura,
                    funcional,
                    cardio,
                    forca,
                    ldl,
                    hdl,
                    foto_frente,
                    foto_costas,
                    foto_lateral_dir,
                    foto_lateral_esq,
                    user_id,
                    self.selected_id,
                ),
                commit=True,
            )

        self.load_avaliacoes()
        messagebox.showinfo("Avaliações", "Avaliação salva com sucesso.")

    def on_excluir(self) -> None:
        if self.selected_id is None:
            show_toast(self, "Selecione uma avaliação para excluir.", 3000)
            return

        if not messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja excluir esta avaliação?"):
            return

        show_toast(self, "Excluindo avaliação...", 1500)
        self.after(500, self._confirm_excluir)

    def _confirm_excluir(self):
        db.execute(
            "DELETE FROM avaliacoes_fisicas WHERE id = ?",
            (self.selected_id,),
            commit=True,
        )

        self.on_novo()
        self.load_avaliacoes()
        messagebox.showinfo("Avaliações", "Avaliação excluída com sucesso.")

    def on_gerar_pdf(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning(
                "Avaliações",
                "Selecione uma avaliação na lista para gerar o PDF.",
            )
            return

        avaliacao = db.fetch_one(
            """
            SELECT id, id_aluno, data, peso, altura,
                   percentual_gordura, massa_magra, massa_gorda,
                   dobras_cutaneas, perimetros, anamnese,
                   historico_saude, estilo_vida, metas,
                   postura, funcional_mobilidade, cardio, forca_resistencia,
                   ldl, hdl,
                   foto_frente, foto_costas, foto_lateral_dir, foto_lateral_esq
            FROM avaliacoes_fisicas
            WHERE id = ?
            """,
            (self.selected_id,),
        )
        if avaliacao is None:
            return

        aluno = db.fetch_one(
            "SELECT id, nome, data_nascimento, cpf, cep FROM alunos WHERE id = ?",
            (avaliacao["id_aluno"],),
        )
        if aluno is None:
            return

        initial_dir = str(Path.cwd())
        aluno_nome = str(aluno["nome"]).replace(" ", "_")
        default_filename = f"avaliacao_{self.selected_id}_{aluno_nome}.pdf"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialdir=initial_dir,
            initialfile=default_filename,
            title="Salvar avaliação em PDF",
        )
        if not file_path:
            return

        dados_avaliacao = dict(avaliacao)
        dados_aluno = dict(aluno)
        professor_nome = self.professor_nome_var.get().strip()

        gerar_pdf_avaliacao(
            dados_avaliacao=dados_avaliacao,
            dados_aluno=dados_aluno,
            professor_nome=professor_nome,
            output_path=Path(file_path),
        )

