from pathlib import Path
from typing import Any
import json

from fpdf import FPDF


def gerar_pdf_avaliacao(
    dados_avaliacao: dict[str, Any],
    dados_aluno: dict[str, Any],
    professor_nome: str,
    professor_cref: str,
    output_path: Path,
) -> None:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    try:
        base_dir = Path(__file__).resolve().parent.parent
        settings_path = base_dir / "data" / "settings.json"
        logo_path = None
        marca_nome = ""
        contato_linha = ""
        if settings_path.exists():
            data = json.loads(settings_path.read_text(encoding="utf-8"))
            logo_path = data.get("logo_path") or None
            marca_nome = (data.get("marca_nome") or "").strip()
            email = (data.get("contato_email") or "").strip()
            tel = (data.get("contato_telefone") or "").strip()
            parts = [p for p in [email, tel] if p]
            contato_linha = " | ".join(parts)
        if logo_path:
            p = Path(logo_path)
            if p.exists():
                pdf.image(str(p), x=10, y=8, w=24)
                pdf.ln(18)
    except Exception:
        pass

    pdf.set_font("Helvetica", "B", 16)
    titulo = "Avaliação Física"
    if marca_nome:
        titulo = f"{marca_nome} - {titulo}"
    pdf.cell(0, 10, titulo, ln=True)
    if contato_linha:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, contato_linha, ln=True)
    pdf.set_draw_color(180, 180, 180)
    pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    prof_text = f"Professor(a): {professor_nome}" if professor_nome.strip() else "Professor(a): ____________________"
    if professor_cref:
        prof_text += f" (CREF: {professor_cref})"
    pdf.cell(0, 8, prof_text, ln=True)

    nome_aluno = dados_aluno.get("nome", "")
    pdf.cell(0, 8, f"Aluno(a): {nome_aluno}", ln=True)
    cpf_txt = (dados_aluno.get("cpf") or "").strip()
    cep_txt = (dados_aluno.get("cep") or "").strip()
    if cpf_txt or cep_txt:
        linha = " | ".join([p for p in [f"CPF: {cpf_txt}" if cpf_txt else "", f"CEP: {cep_txt}" if cep_txt else ""] if p])
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, linha, ln=True)
        pdf.set_font("Helvetica", "", 11)

    data_iso = dados_avaliacao.get("data", "")
    data_br = data_iso
    try:
        if data_iso:
            from datetime import date
            y, m, d = map(int, data_iso.split("-"))
            data_br = f"{d:02d}/{m:02d}/{y:04d}"
    except Exception:
        pass
    pdf.cell(0, 8, f"Data: {data_br}", ln=True)
    pdf.ln(4)

    def fmt_val(v, decimals=1):
        if v is None or str(v).strip() == "": return "-"
        try:
            val = float(v)
            if val.is_integer():
                return f"{int(val)}"
            return f"{val:.{decimals}f}".replace(".", ",")
        except Exception:
            return str(v)

    peso_fmt = fmt_val(dados_avaliacao.get("peso"))
    altura_fmt = fmt_val(dados_avaliacao.get("altura"), decimals=2)
    percent_fmt = fmt_val(dados_avaliacao.get("percentual_gordura"))
    massa_magra_fmt = fmt_val(dados_avaliacao.get("massa_magra"))
    massa_gorda_fmt = fmt_val(dados_avaliacao.get("massa_gorda"))
    ldl_fmt = fmt_val(dados_avaliacao.get("ldl"), decimals=0)
    hdl_fmt = fmt_val(dados_avaliacao.get("hdl"), decimals=0)
    psist = dados_avaliacao.get("pressao_sistolica")
    pdiast = dados_avaliacao.get("pressao_diastolica")

    imc = None
    if dados_avaliacao.get("peso") and dados_avaliacao.get("altura"):
        try:
            imc = float(dados_avaliacao["peso"]) / (float(dados_avaliacao["altura"]) ** 2)
        except Exception:
            imc = None

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Dados antropométricos", ln=True)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Helvetica", "", 11)

    pdf.cell(0, 7, f"Peso: {peso_fmt} kg", ln=True)
    pdf.cell(0, 7, f"Altura: {altura_fmt} m", ln=True)
    if imc is not None:
        pdf.cell(0, 7, f"IMC: {imc:.2f}".replace(".", ","), ln=True)
    else:
        pdf.cell(0, 7, "IMC: -", ln=True)

    pdf.cell(0, 7, f"% Gordura: {percent_fmt}", ln=True)
    pdf.cell(0, 7, f"Massa magra: {massa_magra_fmt} kg", ln=True)
    pdf.cell(0, 7, f"Massa gorda: {massa_gorda_fmt} kg", ln=True)
    
    if ldl_fmt != "-" or hdl_fmt != "-":
        pdf.cell(0, 7, "Perfil lipídico:", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"LDL: {ldl_fmt} mg/dL | HDL: {hdl_fmt} mg/dL", ln=True)
        pdf.set_font("Helvetica", "", 11)

    if psist is not None or pdiast is not None:
        ps = float(psist) if psist is not None else 0
        pd = float(pdiast) if pdiast is not None else 0
        pa_texto = f"{fmt_val(psist, decimals=0)}/{fmt_val(pdiast, decimals=0)} mmHg"
        
        # O Brasil costuma falar algo como "12 por 8", vamos mostrar também
        if ps >= 10 and pd >= 10:
            pa_texto += f" ({fmt_val(ps/10, decimals=0)} por {fmt_val(pd/10, decimals=0)})"

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
        pdf.cell(0, 7, "Pressão Arterial:", ln=True)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, f"PA: {pa_texto} - {alerta_pa}", ln=True)
        if dica_pa:
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 5, dica_pa)
        pdf.set_font("Helvetica", "", 11)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Dobras cutâneas", ln=True)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Helvetica", "", 11)
    dobras = dados_avaliacao.get("dobras_cutaneas") or "-"
    pdf.multi_cell(0, 6, str(dobras))

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Perímetros", ln=True)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Helvetica", "", 11)
    perimetros = dados_avaliacao.get("perimetros") or "-"
    pdf.multi_cell(0, 6, str(perimetros))

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Anamnese", ln=True)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Helvetica", "", 11)
    anamnese = dados_avaliacao.get("anamnese") or "-"
    pdf.multi_cell(0, 6, str(anamnese))

    historico = dados_avaliacao.get("historico_saude")
    estilo = dados_avaliacao.get("estilo_vida")
    metas = dados_avaliacao.get("metas")
    if historico or estilo or metas:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Entrevista inicial", ln=True)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.set_font("Helvetica", "", 11)
        if historico:
            pdf.multi_cell(0, 6, f"Histórico de saúde: {historico}")
        if estilo:
            pdf.multi_cell(0, 6, f"Estilo de vida: {estilo}")
        if metas:
            pdf.multi_cell(0, 6, f"Metas: {metas}")

    postura = dados_avaliacao.get("postura")
    if postura:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Avaliação postural", ln=True)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, str(postura))

    funcional = dados_avaliacao.get("funcional_mobilidade")
    if funcional:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Funcional e mobilidade", ln=True)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, str(funcional))

    cardio = dados_avaliacao.get("cardio")
    forca = dados_avaliacao.get("forca_resistencia")
    if cardio or forca:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Cardiorrespiratório e força", ln=True)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.set_font("Helvetica", "", 11)
        if cardio:
            pdf.multi_cell(0, 6, f"Cardiorrespiratório: {cardio}")
        if forca:
            pdf.multi_cell(0, 6, f"Força/Resistência: {forca}")

    # Fotos
    fotos = [
        ("Vista Anterior (Frente)", dados_avaliacao.get("foto_frente")),
        ("Vista Posterior (Costas)", dados_avaliacao.get("foto_costas")),
        ("Vista Lateral Direita", dados_avaliacao.get("foto_lateral_dir")),
        ("Vista Lateral Esquerda", dados_avaliacao.get("foto_lateral_esq")),
    ]
    existentes = []
    for titulo, caminho in fotos:
        try:
            if caminho and Path(caminho).exists():
                existentes.append((titulo, Path(caminho)))
        except Exception:
            continue
    if existentes:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Fotos", ln=True)
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)
        pdf.set_font("Helvetica", "", 9)
        # duas por linha
        col_w = 90
        x_left = 10
        x_right = 110
        y = pdf.get_y()
        i = 0
        for titulo, caminho in existentes:
            x = x_left if (i % 2) == 0 else x_right
            pdf.set_xy(x, y)
            try:
                pdf.cell(col_w, 5, titulo, ln=False)
                pdf.set_xy(x, pdf.get_y() + 3)
                pdf.image(str(caminho), x=x, y=pdf.get_y(), w=col_w, h=0)
                # avançar y para próxima célula
                img_h = 60  # altura aproximada
                y_next_candidate = pdf.get_y() + img_h + 6
            except Exception:
                y_next_candidate = pdf.get_y() + 10
            if (i % 2) == 1:
                y = max(y_next_candidate, y)
                pdf.set_y(y)
            else:
                # deixar y como está, outra coluna na mesma linha
                pass
            i += 1
        pdf.ln(4)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
