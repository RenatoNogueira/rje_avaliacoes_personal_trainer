from pathlib import Path
from typing import Iterable, Mapping
import json

from .pdf_base import SafeFPDF as FPDF, load_branding


def _digits(s: str) -> str:
    return "".join(ch for ch in str(s or "") if ch.isdigit())


def _format_cpf(d: str) -> str:
    d = _digits(d)[:11]
    if len(d) != 11:
        return d
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def gerar_pdf_agenda(
    data: str,
    agendamentos: Iterable[Mapping[str, object]],
    professor_cref: str,
    output_path: Path,
) -> None:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # (Antes a variável "data" — a data da agenda — era sobrescrita pelo JSON de
    #  configurações, e o PDF mostrava o dicionário no lugar da data.)
    brand = load_branding()
    logo_path = brand["logo_path"]
    marca_nome = brand["marca_nome"]
    contato_linha = brand["contato_linha"]
    if logo_path:
        try:
            pdf.image(logo_path, x=10, y=8, w=24)
            pdf.ln(18)
        except Exception:
            pass

    pdf.set_font("Helvetica", "B", 16)
    titulo = "Agenda do Dia"
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
    text_data = f"Data: {data or '-'}"
    if professor_cref:
        text_data += f" | CREF: {professor_cref}"
    pdf.cell(0, 8, text_data, ln=True)
    pdf.ln(4)

    col_horario = 22
    col_aluno = 55
    col_pa = 25
    col_cpf = 30
    col_tipo = 33
    col_status = 25

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_horario, 8, "Horário", border=1)
    pdf.cell(col_aluno, 8, "Aluno", border=1)
    pdf.cell(col_pa, 8, "P.A.", border=1)
    pdf.cell(col_cpf, 8, "CPF", border=1)
    pdf.cell(col_tipo, 8, "Tipo", border=1)
    pdf.cell(col_status, 8, "Status", border=1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    count = 0
    for ag in agendamentos:
        horario = str(ag.get("horario") or "")
        aluno = str(ag.get("nome_aluno") or "")
        cpf = _format_cpf(ag.get("cpf") or "")
        tipo = str(ag.get("tipo") or "")
        status = str(ag.get("status") or "")
        
        # Format Blood Pressure
        psist = ag.get("psist")
        pdiast = ag.get("pdiast")
        pa_val = "-"
        if psist is not None and str(psist).strip() != "" or pdiast is not None and str(pdiast).strip() != "":
            ps = float(psist) if psist and str(psist).strip() != "" else 0
            pd = float(pdiast) if pdiast and str(pdiast).strip() != "" else 0
            pa_val = f"{int(ps)}/{int(pd)}"
            if ps >= 10 and pd >= 10:
                pa_val += f" ({int(ps/10)}x{int(pd/10)})"

        pdf.cell(col_horario, 8, horario[:10], border=1)
        pdf.cell(col_aluno, 8, aluno[:30], border=1)
        pdf.cell(col_pa, 8, pa_val, border=1)
        pdf.cell(col_cpf, 8, cpf[:18], border=1)
        pdf.cell(col_tipo, 8, tipo[:18], border=1)
        pdf.cell(col_status, 8, status[:18], border=1)
        pdf.ln()
        count += 1

    if count == 0:
        pdf.ln(4)
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 8, "Nenhum agendamento encontrado.", ln=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
