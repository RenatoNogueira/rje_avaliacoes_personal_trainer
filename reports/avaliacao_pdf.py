from pathlib import Path
from typing import Any
import json

from fpdf import FPDF


def gerar_pdf_avaliacao(
    dados_avaliacao: dict[str, Any],
    dados_aluno: dict[str, Any],
    professor_nome: str,
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
        titulo = f"{marca_nome} – {titulo}"
    pdf.cell(0, 10, titulo, ln=True)
    if contato_linha:
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, contato_linha, ln=True)
    pdf.set_draw_color(180, 180, 180)
    pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 11)
    if professor_nome.strip():
        pdf.cell(0, 8, f"Professor(a): {professor_nome}", ln=True)
    else:
        pdf.cell(0, 8, "Professor(a): ____________________", ln=True)

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

    peso = dados_avaliacao.get("peso")
    altura = dados_avaliacao.get("altura")
    percentual_gordura = dados_avaliacao.get("percentual_gordura")
    massa_magra = dados_avaliacao.get("massa_magra")
    massa_gorda = dados_avaliacao.get("massa_gorda")
    ldl = dados_avaliacao.get("ldl")
    hdl = dados_avaliacao.get("hdl")

    imc = None
    if peso and altura:
        try:
            imc = float(peso) / (float(altura) ** 2)
        except Exception:
            imc = None

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Dados antropométricos", ln=True)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Helvetica", "", 11)

    pdf.cell(0, 7, f"Peso: {peso or '-'} kg", ln=True)
    pdf.cell(0, 7, f"Altura: {altura or '-'} m", ln=True)
    if imc is not None:
        pdf.cell(0, 7, f"IMC: {imc:.2f}", ln=True)
    else:
        pdf.cell(0, 7, "IMC: -", ln=True)

    pdf.cell(
        0,
        7,
        f"% Gordura: {percentual_gordura if percentual_gordura is not None else '-'}",
        ln=True,
    )
    pdf.cell(
        0,
        7,
        f"Massa magra: {massa_magra if massa_magra is not None else '-'} kg",
        ln=True,
    )
    pdf.cell(
        0,
        7,
        f"Massa gorda: {massa_gorda if massa_gorda is not None else '-'} kg",
        ln=True,
    )
    if ldl is not None or hdl is not None:
        pdf.cell(0, 7, "Perfil lipídico:", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"LDL: {ldl if ldl is not None else '-'} mg/dL | HDL: {hdl if hdl is not None else '-'} mg/dL", ln=True)
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
