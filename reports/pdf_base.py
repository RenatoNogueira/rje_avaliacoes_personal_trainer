"""
Base comum dos relatórios PDF.

* ``SafeFPDF``: evita que um caractere fora do conjunto das fontes padrão
  (ex.: emoji, aspas especiais coladas de outro programa) derrube a geração
  inteira do PDF — o caractere é substituído por um equivalente seguro.
* ``load_branding()``: lê marca/logo/contatos das configurações a partir da
  pasta de dados correta (antes os relatórios procuravam em ``_internal/data``).
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

from fpdf import FPDF

import app_paths

_REPLACEMENTS = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", "•": "-",
    " ": " ", "→": "->", "←": "<-", "≥": ">=", "≤": "<=",
}


class SafeFPDF(FPDF):
    def normalize_text(self, text: str) -> str:  # type: ignore[override]
        if not self.is_ttf_font and self.core_fonts_encoding:
            enc = self.core_fonts_encoding
            try:
                return text.encode(enc).decode("latin-1")
            except UnicodeEncodeError:
                out = []
                for ch in text:
                    try:
                        ch.encode(enc)
                        out.append(ch)
                        continue
                    except UnicodeEncodeError:
                        pass
                    rep = _REPLACEMENTS.get(ch)
                    if rep is None:
                        # tenta remover acentos compostos; senão descarta (ex.: emoji)
                        rep = unicodedata.normalize("NFKD", ch).encode(enc, "ignore").decode(enc, "ignore")
                    out.append(rep)
                return "".join(out).encode(enc, "replace").decode("latin-1")
        return super().normalize_text(text)


def load_branding() -> dict:
    """Retorna logo_path (absoluto, se existir), marca_nome e contato_linha."""
    info = {"logo_path": None, "marca_nome": "", "contato_linha": ""}
    try:
        settings_path = app_paths.SETTINGS_PATH
        if settings_path.exists():
            data = json.loads(settings_path.read_text(encoding="utf-8"))
            logo = app_paths.resolve_data_path(data.get("logo_path")) if data.get("logo_path") else None
            if logo and Path(logo).exists():
                info["logo_path"] = str(logo)
            info["marca_nome"] = (data.get("marca_nome") or "").strip()
            email = (data.get("contato_email") or "").strip()
            tel = (data.get("contato_telefone") or "").strip()
            info["contato_linha"] = " | ".join(p for p in (email, tel) if p)
    except Exception:
        pass
    return info
