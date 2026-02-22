from pathlib import Path
from typing import Iterable, Mapping
import json

from fpdf import FPDF


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
    titulo = "Agenda do Dia"
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
    text_data = f"Data: {data or '-'}"
    if professor_cref:
        text_data += f" | CREF: {professor_cref}"
    pdf.cell(0, 8, text_data, ln=True)
    pdf.ln(4)

    col_horario = 25
    col_aluno = 60
    col_cpf = 35
    col_tipo = 35
    col_status = 35

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_horario, 8, "Horário", border=1)
    pdf.cell(col_aluno, 8, "Aluno", border=1)
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

        pdf.cell(col_horario, 8, horario[:10], border=1)
        pdf.cell(col_aluno, 8, aluno[:34], border=1)
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
