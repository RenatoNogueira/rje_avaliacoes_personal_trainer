from pathlib import Path
from typing import Any, Iterable
import json
import datetime

from fpdf import FPDF
from fpdf.fonts import FontFace
from fpdf.enums import TableCellFillMode


class TreinoPDF(FPDF):
    def __init__(self, brand_info: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.brand_info = brand_info
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        # Logo
        logo_path = self.brand_info.get("logo_path")
        if logo_path and Path(logo_path).exists():
            try:
                # Logo à esquerda, 25mm largura
                self.image(logo_path, x=10, y=8, w=25)
            except Exception:
                pass

        # Marca e Título (alinhados à direita ou centro se não tiver logo?)
        # Vamos padronizar: Logo na esquerda, Textos centralizados/direita
        self.set_y(10)
        
        # Nome da Marca
        marca = self.brand_info.get("marca_nome", "").strip()
        if marca:
            self.set_font("Helvetica", "B", 16)
            self.cell(0, 8, marca, align="R", ln=True)

        # Subtítulo fixo
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "FICHA DE TREINO", align="R", ln=True)
        self.set_text_color(0, 0, 0)

        # Contato
        contato = self.brand_info.get("contato_linha", "").strip()
        if contato:
            self.set_font("Helvetica", "", 9)
            self.set_text_color(128, 128, 128)
            self.cell(0, 5, contato, align="R", ln=True)
            self.set_text_color(0, 0, 0)

        self.ln(5)
        # Linha separadora
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")


def gerar_pdf_treino(
    dados_treino: dict[str, Any],
    dados_aluno: dict[str, Any],
    exercicios: Iterable[dict[str, Any]],
    professor_nome: str,
    professor_cref: str,
    output_path: Path,
) -> None:
    # 1. Carregar configurações de branding
    base_dir = Path(__file__).resolve().parent.parent
    settings_path = base_dir / "data" / "settings.json"
    brand_info = {
        "logo_path": None,
        "marca_nome": "",
        "contato_linha": ""
    }
    
    if settings_path.exists():
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
            brand_info["logo_path"] = data.get("logo_path")
            brand_info["marca_nome"] = data.get("marca_nome")
            
            email = (data.get("contato_email") or "").strip()
            tel = (data.get("contato_telefone") or "").strip()
            parts = [p for p in [email, tel] if p]
            brand_info["contato_linha"] = " | ".join(parts)
        except Exception:
            pass

    # 2. Instanciar PDF
    pdf = TreinoPDF(brand_info=brand_info, orientation="P", unit="mm", format="A4")
    pdf.add_page()

    # 3. Cabeçalho do Treino (Aluno, Professor, Datas)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 6, f"Treino: {dados_treino.get('nome_do_treino', 'Sem nome')}", ln=True)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.ln(2)
    
    # Grid de info (Aluno | Professor | Data)
    # Usando cell simples
    
    # Linha 1: Aluno e Professor
    y_start = pdf.get_y()
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(20, 6, "Aluno(a):", align="L")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(80, 6, dados_aluno.get("nome", "-"), align="L")
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(25, 6, "Professor(a):", align="L")
    pdf.set_font("Helvetica", "", 10)
    prof_text = professor_nome or "-"
    if professor_cref:
        prof_text += f" (CREF: {professor_cref})"
    pdf.cell(0, 6, prof_text, align="L", ln=True)
    
    # Linha 2: Objetivo e Data
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(20, 6, "Objetivo:", align="L")
    pdf.set_font("Helvetica", "", 10)
    objetivo = dados_treino.get("objetivo") or "-"
    pdf.cell(80, 6, objetivo, align="L")
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(25, 6, "Data:", align="L")
    pdf.set_font("Helvetica", "", 10)
    
    data_criacao = dados_treino.get("data_criacao") or datetime.date.today().strftime("%d/%m/%Y")
    
    # Normalização de data para PT-BR
    try:
        # Se for objeto datetime ou date
        if isinstance(data_criacao, (datetime.date, datetime.datetime)):
            data_criacao = data_criacao.strftime("%d/%m/%Y")
        
        # Se for string
        elif isinstance(data_criacao, str):
            # Tenta YYYY-MM-DD ou YYYY-MM-DD HH:MM:SS
            if "-" in data_criacao:
                iso_part = data_criacao.split(" ")[0]
                d = datetime.date.fromisoformat(iso_part)
                data_criacao = d.strftime("%d/%m/%Y")
            # Se vier com / mas invertido (ex: 2026/02/21)
            elif "/" in data_criacao:
                parts = data_criacao.split("/")
                if len(parts) == 3 and len(parts[0]) == 4: # YYYY/MM/DD
                    data_criacao = f"{parts[2]}/{parts[1]}/{parts[0]}"
    except Exception:
        # Mantém original se falhar conversão
        pass
        
    pdf.cell(0, 6, data_criacao, align="L", ln=True)
    
    # Adicionar Pressão Arterial
    psist = dados_treino.get("pressao_sistolica")
    pdiast = dados_treino.get("pressao_diastolica")

    if psist is not None or pdiast is not None:
        def fmt_val(v):
            if v is None or str(v).strip() == "": return "-"
            try:
                val = float(v)
                if val.is_integer():
                    return f"{int(val)}"
                return f"{val:.1f}".replace(".", ",")
            except Exception:
                return str(v)

        ps = float(psist) if psist is not None else 0
        pd = float(pdiast) if pdiast is not None else 0
        pa_texto = f"{fmt_val(psist)}/{fmt_val(pdiast)} mmHg"

        if ps >= 10 and pd >= 10:
            pa_texto += f" ({int(ps / 10)} por {int(pd / 10)})"

        alerta_pa = ""
        dica_pa = ""
        if (ps > 0 and ps < 90) or (pd > 0 and pd < 60):
            alerta_pa = "Hipotensão (Pressão Baixa)"
            dica_pa = "Dicas: Mantenha-se hidratado, evite levantar bruscamente e consuma porções menores e mais frequentes. Exercícios devem ser acompanhados com atenção à tontura."
        elif ps >= 180 or pd >= 120:
            alerta_pa = "Crise Hipertensiva"
            dica_pa = "DICA URGENTE: Valores criticamente altos. Procure atendimento médico imediato e suspenda os treinos até liberação médica."
        elif ps >= 160 or pd >= 100:
            alerta_pa = "Hipertensão Estágio 2"
            dica_pa = "Dicas: Acompanhamento médico rigoroso é indispensável. Treinos precisam de controle rigoroso de carga, intervalo e respiração."
        elif ps >= 140 or pd >= 90:
            alerta_pa = "Hipertensão Estágio 1"
            dica_pa = "Dicas: Monitore regularmente. Reduza o consumo de sódio e gerencie o estresse. Atividade física regular (aeróbica e força) ajuda no controle."
        elif ps > 120 or pd > 80:
            alerta_pa = "Elevada/Limítrofe"
            dica_pa = "Dicas: Atenção aos fatores de risco. Adote uma alimentação balanceada e mantenha a consistência nos treinos para prevenir a hipertensão."
        else:
            alerta_pa = "Normotensão (Normal)"
            dica_pa = "Dicas: Excelente! Continue com seus hábitos saudáveis e rotina de exercícios para manter o sistema cardiovascular protegido."

        pdf.ln(2)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, "Pressão Arterial:", ln=True)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, f"PA: {pa_texto} - {alerta_pa}", ln=True)
        if dica_pa:
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 5, dica_pa)

    pdf.ln(6)

    # 4. Tabela de Exercícios (Agrupada por Divisão)
    
    # Agrupar exercícios
    grupos = {"A": [], "B": [], "C": [], "D": []}
    for ex in exercicios:
        div = str(ex.get("divisao") or "A").upper()
        # Se a divisão não for A, B, C ou D, agrupa em "Outros" ou cria chave nova
        if div not in grupos:
            grupos[div] = []
        grupos[div].append(ex)

    headers = ["Exercício", "Séries", "Reps", "Carga", "Descanso", "Obs"]
    
    # Determinar ordem de exibição (A, B, C, D e depois extras)
    divisoes_ordenadas = ["A", "B", "C", "D"]
    extras = [k for k in grupos.keys() if k not in divisoes_ordenadas]
    divisoes_ordenadas.extend(sorted(extras))

    for div in divisoes_ordenadas:
        lista = grupos[div]
        if not lista:
            continue
            
        # Cabeçalho da Divisão
        pdf.ln(2)
        # Verificar se cabe na página, senão quebra
        if pdf.get_y() > 250:
            pdf.add_page()
            
        pdf.set_font("Helvetica", "B", 12)
        # Fundo azul claro para destacar a divisão
        pdf.set_fill_color(52, 152, 219)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, f"  Treino {div}", ln=True, fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

        # Dados da tabela
        table_data = []
        for ex in lista:
            nome = str(ex.get("nome_exercicio") or "")
            series = str(ex.get("series") or "")
            reps = str(ex.get("repeticoes") or "")
            carga = str(ex.get("carga") or "")
            descanso = str(ex.get("descanso") or "")
            obs = str(ex.get("observacoes") or "")
            table_data.append([nome, series, reps, carga, descanso, obs])

        pdf.set_font("Helvetica", "", 9)
        with pdf.table() as table:
            table.row(headers, style=FontFace(emphasis="BOLD", fill_color=(230, 230, 230), size_pt=10))
            for row in table_data:
                table.row(row)
        
        pdf.ln(4)

    # 5. Seções Informativas (Cardio, Ativações, Instruções)
    if pdf.get_y() > 220:
        pdf.add_page()
    else:
        pdf.ln(5)

    # Box de Cardio / Ativações
    pdf.set_draw_color(200, 200, 200)
    pdf.set_fill_color(250, 250, 250)
    
    # Título Cardio
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Cardio / Ativações", ln=True)
    
    pdf.set_font("Helvetica", "", 10)
    # Linhas pontilhadas ou sublinhadas para preenchimento ou indicação
    # Usando multi_cell para layout
    cardio_text = (
        "Aquecimento: ___________________________________________________________________\n\n"
        "Ativações: ______________________________________________________________________\n\n"
        "Cardio Final: ___________________________________________________________________"
    )
    pdf.multi_cell(0, 6, cardio_text, border=1, fill=True)
    pdf.ln(5)

    # Instruções Básicas
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Instruções Básicas de Movimento", ln=True)
    
    instrucoes = (
        "1. Controle a respiração: expire na fase de esforço e inspire na fase de retorno.\n"
        "2. Mantenha a coluna alinhada e o abdômen contraído (Bracing) durante os exercícios.\n"
        "3. Cadência: Execute o movimento de forma controlada, evitando impulsos.\n"
        "4. Ajuste as cargas para completar as repetições indicadas com boa técnica.\n"
        "5. Em caso de dor articular aguda, interrompa o exercício e consulte o professor."
    )
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, instrucoes, border=1, fill=False)

    # 6. Espaço para anotações manuais (Opcional - mantido reduzido)
    pdf.ln(5)
    if pdf.get_y() < 240:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Anotações / Feedback:", ln=True)
        pdf.set_draw_color(150, 150, 150)
        pdf.line(10, pdf.get_y() + 5, 200, pdf.get_y() + 5)
        pdf.line(10, pdf.get_y() + 12, 200, pdf.get_y() + 12)

    # Salvar
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))

