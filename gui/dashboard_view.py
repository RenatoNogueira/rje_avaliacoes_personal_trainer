import datetime
import calendar
import customtkinter as ctk
from database import db

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, get_refresh_seconds=None) -> None:
        super().__init__(master)
        self.get_refresh_seconds = get_refresh_seconds or (lambda: 60)

        # Layout Principal
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=24, pady=(24, 12), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header, text="Dashboard", font=ctk.CTkFont(size=28, weight="bold")
        )
        title.grid(row=0, column=0, sticky="w")

        self.date_label = ctk.CTkLabel(
            header,
            text=datetime.date.today().strftime("%d/%m/%Y"),
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.date_label.grid(row=0, column=1, padx=15, sticky="e")

        btn_refresh = ctk.CTkButton(
            header, text="↻ Atualizar", width=100, command=self.refresh_data
        )
        btn_refresh.grid(row=0, column=2, padx=(0, 0))

        # 2. Cards de Resumo
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.grid(row=1, column=0, padx=24, pady=0, sticky="ew")
        self.cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.card_alunos = self._create_card(self.cards_frame, "Total de Alunos", "0", "👥")
        self.card_alunos.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")

        self.card_agendamentos = self._create_card(self.cards_frame, "Agendamentos Hoje", "0", "📅")
        self.card_agendamentos.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.card_avaliacoes = self._create_card(self.cards_frame, "Avaliações no Mês", "0", "⚖️")
        self.card_avaliacoes.grid(row=0, column=2, padx=(10, 0), pady=10, sticky="nsew")

        # 3. Área Principal (Grid 2 colunas)
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.grid(row=2, column=0, padx=24, pady=(12, 24), sticky="nsew")
        main_content.grid_columnconfigure(0, weight=2, minsize=500) # Tabela Principal
        main_content.grid_columnconfigure(1, weight=1, minsize=300) # Lateral
        main_content.grid_rowconfigure(0, weight=1)

        # Esquerda: Próximos Agendamentos (Usando ScrollableFrame e Cards)
        self.table_container = ctk.CTkScrollableFrame(main_content, label_text="Próximos Agendamentos")
        self.table_container.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        self.table_container.grid_columnconfigure(0, weight=1)

        # Direita: Aniversariantes e Extras
        side_container = ctk.CTkFrame(main_content, fg_color="transparent")
        side_container.grid(row=0, column=1, padx=(10, 0), pady=0, sticky="nsew")
        side_container.grid_rowconfigure(0, weight=1) # Aniversariantes ocupa mais espaço
        side_container.grid_rowconfigure(1, weight=0) # Extras
        side_container.grid_columnconfigure(0, weight=1)

        # Card Aniversariantes
        self.bday_card = ctk.CTkFrame(side_container)
        self.bday_card.grid(row=0, column=0, pady=(0, 15), sticky="nsew")
        self.bday_card.grid_rowconfigure(1, weight=1)
        self.bday_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.bday_card,
            text="🎂 Aniversariantes do Mês",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=15, pady=10, sticky="w")

        # Container scrollable para aniversariantes
        self.scroll_bday = ctk.CTkScrollableFrame(self.bday_card, fg_color="transparent")
        self.scroll_bday.grid(row=1, column=0, padx=5, pady=(0, 10), sticky="nsew")

        # Card Extra (Ex: Treinos)
        extra_card = ctk.CTkFrame(side_container)
        extra_card.grid(row=1, column=0, sticky="ew")
        extra_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            extra_card,
            text="📊 Estatísticas Rápidas",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.label_treinos_ativos = ctk.CTkLabel(extra_card, text="Treinos Cadastrados: 0", anchor="w")
        self.label_treinos_ativos.grid(row=1, column=0, padx=15, pady=(0, 5), sticky="ew")

        self.label_media_idade = ctk.CTkLabel(extra_card, text="Média de Idade: 0 anos", anchor="w")
        self.label_media_idade.grid(row=2, column=0, padx=15, pady=(0, 15), sticky="ew")

        # Inicializa
        self.refresh_data()
        self._start_timer()

    def _create_card(self, parent, title, value, icon):
        card = ctk.CTkFrame(parent)
        
        # Ícone
        icon_label = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=36))
        icon_label.pack(side="left", padx=(20, 15), pady=20)
        
        # Info Container
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="y", pady=15)
        
        # Valor
        lbl_value = ctk.CTkLabel(info_frame, text=value, font=ctk.CTkFont(size=26, weight="bold"))
        lbl_value.pack(anchor="w")
        
        # Título
        lbl_title = ctk.CTkLabel(info_frame, text=title, font=ctk.CTkFont(size=13), text_color="gray")
        lbl_title.pack(anchor="w")
        
        # Guarda referência para update
        if "Alunos" in title: self.lbl_alunos = lbl_value
        elif "Agendamentos" in title: self.lbl_agendamentos = lbl_value
        elif "Avaliações" in title: self.lbl_avaliacoes = lbl_value
        
        return card

    def _create_agendamento_card(self, row: dict, index: int) -> None:
        """Cria um card de agendamento com animação de entrada."""
        
        # Formata data
        data_obj = datetime.date.fromisoformat(row["data"])
        dia_semana = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"][data_obj.weekday()]
        data_fmt = data_obj.strftime("%d/%m")
        is_today = row["data"] == datetime.date.today().isoformat()
        
        card_color = ("gray90", "gray20")
        if is_today:
            card_color = ("#e8f5e9", "#1e3a23") # Destaque verde suave para hoje

        card = ctk.CTkFrame(self.table_container, fg_color=card_color, corner_radius=10)
        
        # Animação simples: delay baseado no index
        card.pack(fill="x", pady=5, padx=5)
        
        # Layout interno:
        # [DATA BOX] [INFO] [STATUS]
        
        # 1. Data Box (Esquerda)
        date_box = ctk.CTkFrame(card, width=60, height=60, fg_color=("gray80", "gray30"), corner_radius=8)
        date_box.pack(side="left", padx=10, pady=10)
        date_box.pack_propagate(False)
        
        ctk.CTkLabel(date_box, text=dia_semana, font=ctk.CTkFont(size=10, weight="bold")).pack(pady=(8, 0))
        ctk.CTkLabel(date_box, text=data_fmt, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(0, 5))

        # 2. Info (Centro)
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(info_frame, text=row["nome_aluno"], font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w")
        
        details = f"{row['tipo']} • {row['horario']}h"
        ctk.CTkLabel(info_frame, text=details, font=ctk.CTkFont(size=12), text_color="gray").pack(anchor="w")

        # 3. Status (Direita)
        status_colors = {
            "Pendente": "orange",
            "Concluído": "green",
            "Cancelado": "red"
        }
        color = status_colors.get(row["status"], "gray")
        
        status_frame = ctk.CTkFrame(card, fg_color="transparent")
        status_frame.pack(side="right", padx=15)
        
        ctk.CTkLabel(status_frame, text=row["status"], text_color=color, font=ctk.CTkFont(size=12, weight="bold")).pack()

    def _create_bday_card(self, row: dict, index: int) -> None:
        """Cria um card animado para aniversariante."""
        try:
            dn = datetime.date.fromisoformat(row["data_nascimento"])
            dia = dn.day
            dia_str = f"{dia:02d}"
        except:
            dia_str = "??"

        card = ctk.CTkFrame(self.scroll_bday, fg_color=("gray95", "gray25"), corner_radius=8, height=40)
        card.pack(fill="x", pady=3, padx=2)
        
        # Ícone Bolo
        ctk.CTkLabel(card, text="🎂", font=ctk.CTkFont(size=16)).pack(side="left", padx=(10, 5), pady=5)
        
        # Data
        ctk.CTkLabel(
            card, 
            text=f"Dia {dia_str}", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray40", "gray80")
        ).pack(side="left", padx=5)
        
        # Nome
        ctk.CTkLabel(
            card,
            text=row["nome"],
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=5, fill="x", expand=True, anchor="w")

        # Animação simples (fade in simulado com delay na criação)
        # Como Tkinter não tem fade nativo fácil, apenas o fato de usar cards já melhora a UI.
        # Poderíamos adicionar um efeito de hover
        card.bind("<Enter>", lambda e: card.configure(fg_color=("white", "gray35")))
        card.bind("<Leave>", lambda e: card.configure(fg_color=("gray95", "gray25")))

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

    def refresh_data(self) -> None:
        today = datetime.date.today()
        today_iso = today.isoformat()
        current_month = today.strftime("%m")

        # 1. Alunos
        row = db.fetch_one("SELECT COUNT(*) AS total FROM alunos")
        total_alunos = row["total"] if row is not None else 0
        if hasattr(self, "lbl_alunos"):
            self.lbl_alunos.configure(text=str(total_alunos))

        # 2. Agendamentos Hoje e Próximos
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
        
        # Filtra apenas os de hoje para o contador
        ag_hoje = [r for r in ag_rows if r["data"] == today_iso]
        total_ag = len(ag_hoje)
        
        if hasattr(self, "lbl_agendamentos"):
            self.lbl_agendamentos.configure(text=str(total_ag))

        # Lista de Agendamentos (Cards Animados)
        for widget in self.table_container.winfo_children():
            widget.destroy()

        if not ag_rows:
            ctk.CTkLabel(self.table_container, text="Nenhum agendamento próximo.", text_color="gray").pack(pady=20)
        else:
            for i, ag in enumerate(ag_rows):
                self._create_agendamento_card(ag, i)

        # 3. Avaliações no Mês
        # SQLite: strftime('%m', data) retorna mês
        av_row = db.fetch_one(
            "SELECT COUNT(*) as total FROM avaliacoes_fisicas WHERE strftime('%m', data) = ?",
            (current_month,)
        )
        total_av = av_row["total"] if av_row else 0
        if hasattr(self, "lbl_avaliacoes"):
            self.lbl_avaliacoes.configure(text=str(total_av))

        # 4. Aniversariantes do Mês
        bday_rows = db.fetch_all(
            "SELECT nome, data_nascimento FROM alunos WHERE strftime('%m', data_nascimento) = ? ORDER BY strftime('%d', data_nascimento)",
            (current_month,)
        )
        
        # Limpa os cards antigos
        for widget in self.scroll_bday.winfo_children():
            widget.destroy()
        
        if not bday_rows:
            ctk.CTkLabel(self.scroll_bday, text="Nenhum aniversariante este mês.", text_color="gray").pack(pady=20)
        else:
            for i, bday in enumerate(bday_rows):
                self._create_bday_card(bday, i)

        # 5. Estatísticas Extras
        treinos_row = db.fetch_one("SELECT COUNT(*) as total FROM treinos")
        total_treinos = treinos_row["total"] if treinos_row else 0
        if hasattr(self, "label_treinos_ativos"):
            self.label_treinos_ativos.configure(text=f"Treinos Cadastrados: {total_treinos}")

        # Média de idade (aproximada)
        avg_age = 0
        if total_alunos > 0:
            # Pega ano nascimento
            age_rows = db.fetch_all("SELECT data_nascimento FROM alunos WHERE data_nascimento IS NOT NULL AND data_nascimento != ''")
            if age_rows:
                total_years = 0
                count = 0
                this_year = today.year
                for r in age_rows:
                    try:
                        y = int(r["data_nascimento"][:4])
                        total_years += (this_year - y)
                        count += 1
                    except:
                        pass
                if count > 0:
                    avg_age = int(total_years / count)
        
        if hasattr(self, "label_media_idade"):
            self.label_media_idade.configure(text=f"Média de Idade: {avg_age} anos")
