"""
Resolução centralizada de caminhos do RJE Avaliações.

Separa três conceitos que antes estavam misturados (tudo era resolvido a partir
de ``Path(__file__).parent``, que no executável aponta para ``_internal``):

* ``APP_DIR``       – pasta onde está o executável (ou a raiz do projeto em dev).
* ``RESOURCE_DIR``  – recursos somente leitura empacotados (ícones, JSON, fontes).
* ``DATA_ROOT``     – dados do usuário (banco, configurações, fotos, backups, logs).

No executável Windows os dados ficam em ``%PROGRAMDATA%\\RJE Avaliacoes`` (compartilhado
entre as contas do computador e preservado em atualizações/reinstalações). Se essa
pasta não puder ser gravada, usa ``%LOCALAPPDATA%``. Em desenvolvimento, a raiz do
projeto continua sendo usada, como antes.

Na primeira execução, dados de versões anteriores (``_internal/data`` e
``_internal/media``) são copiados automaticamente — nada é apagado da origem.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path

APP_NAME = "RJE Avaliacoes"
IS_FROZEN = bool(getattr(sys, "frozen", False))

if IS_FROZEN:
    APP_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
else:
    APP_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = APP_DIR


def _is_writable(folder: Path) -> bool:
    try:
        folder.mkdir(parents=True, exist_ok=True)
        probe = folder / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except Exception:
        return False


def _choose_data_root() -> Path:
    override = os.environ.get("RJE_DATA_DIR")
    if override:
        return Path(override)

    if not IS_FROZEN:
        return APP_DIR

    candidates = []
    if os.name == "nt":
        for env in ("PROGRAMDATA", "LOCALAPPDATA", "APPDATA"):
            base = os.environ.get(env)
            if base:
                candidates.append(Path(base) / APP_NAME)
    candidates.append(Path.home() / f".{APP_NAME.replace(' ', '_').lower()}")
    candidates.append(APP_DIR / "userdata")

    for c in candidates:
        if _is_writable(c):
            return c
    return APP_DIR


DATA_ROOT: Path = _choose_data_root()
DATA_DIR: Path = DATA_ROOT / "data"
MEDIA_DIR: Path = DATA_ROOT / "media"
BACKUP_DIR: Path = DATA_ROOT / "backups"
LOG_DIR: Path = DATA_ROOT / "logs"
DB_PATH: Path = DATA_DIR / "rje_avaliacoes.db"
SETTINGS_PATH: Path = DATA_DIR / "settings.json"

for _d in (DATA_DIR, MEDIA_DIR, BACKUP_DIR, LOG_DIR):
    try:
        _d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


# ───────────────────────────── Recursos ─────────────────────────────────────

def resource_path(*parts: str) -> Path:
    """Caminho de um recurso empacotado (somente leitura)."""
    p = RESOURCE_DIR.joinpath(*parts)
    if p.exists():
        return p
    # fallback: ao lado do executável
    return APP_DIR.joinpath(*parts)


def default_logo_path() -> str:
    return str(resource_path("assets", "logo_rje.png"))


def documents_dir() -> Path:
    """Pasta padrão para salvar PDFs gerados pelo usuário."""
    home = Path.home()
    docs = home / "Documents"
    if not docs.exists():
        docs = home / "Documentos" if (home / "Documentos").exists() else home
    target = docs / "RJE Avaliacoes"
    try:
        target.mkdir(parents=True, exist_ok=True)
        return target
    except Exception:
        return docs


# ─────────────────────── Caminhos de dados do usuário ───────────────────────

_MARKERS = ("media", "data")


def to_storage_path(path: str | Path | None) -> str | None:
    """
    Converte um caminho para o formato a ser gravado no banco:
    relativo a DATA_ROOT quando o arquivo está dentro dele (portável).
    """
    if not path:
        return None
    p = Path(path)
    try:
        return p.resolve().relative_to(DATA_ROOT.resolve()).as_posix()
    except Exception:
        return str(p)


def resolve_data_path(path: str | Path | None) -> Path | None:
    """
    Resolve um caminho gravado no banco/configurações.

    * relativo  → DATA_ROOT / caminho
    * absoluto existente → ele mesmo
    * absoluto de versão antiga (ex.: ...\\_internal\\media\\...) → remapeado
      para DATA_ROOT a partir do segmento "media"/"data".
    """
    if not path:
        return None
    p = Path(str(path).replace("\\", "/")) if os.name != "nt" else Path(path)
    if not p.is_absolute():
        return DATA_ROOT / p
    if p.exists():
        return p
    parts = list(p.parts)
    for i, part in enumerate(parts):
        if part.lower() in _MARKERS:
            candidate = DATA_ROOT.joinpath(*parts[i:])
            if candidate.exists():
                return candidate
    return p


# ───────────────────────────── Migração ─────────────────────────────────────

def _legacy_roots() -> list[Path]:
    roots = [APP_DIR / "_internal", APP_DIR]
    if IS_FROZEN:
        roots.insert(0, RESOURCE_DIR)
    seen, out = set(), []
    for r in roots:
        key = str(r.resolve()) if r.exists() else str(r)
        if key not in seen and r.resolve() != DATA_ROOT.resolve():
            seen.add(key)
            out.append(r)
    return out


def _copy_tree(src: Path, dst: Path) -> None:
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item, target)


def _rewrite_legacy_paths(legacy_root: Path) -> None:
    """Após copiar, converte caminhos absolutos antigos para relativos."""
    legacy_prefixes = {str(legacy_root.resolve()), str(legacy_root)}

    def convert(value):
        if not value or not isinstance(value, str):
            return value
        for pref in legacy_prefixes:
            if value.startswith(pref):
                rel = value[len(pref):].lstrip("\\/")
                if (DATA_ROOT / rel).exists():
                    return Path(rel).as_posix()
        return value

    # settings.json
    try:
        if SETTINGS_PATH.exists():
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            if "logo_path" in data:
                data["logo_path"] = convert(data["logo_path"])
            SETTINGS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    # Banco
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        targets = {
            "usuarios": ["foto_perfil"],
            "alunos": ["foto_perfil"],
            "avaliacoes_fisicas": ["foto_frente", "foto_costas", "foto_lateral_dir", "foto_lateral_esq"],
        }
        for table, cols in targets.items():
            existing = {r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()}
            for col in cols:
                if col not in existing:
                    continue
                rows = cur.execute(f"SELECT id, {col} FROM {table} WHERE {col} IS NOT NULL").fetchall()
                for rid, val in rows:
                    new = convert(val)
                    if new != val:
                        cur.execute(f"UPDATE {table} SET {col} = ? WHERE id = ?", (new, rid))
        conn.commit()
        conn.close()
    except Exception:
        pass


def migrate_legacy_data() -> str | None:
    """
    Copia dados de versões anteriores para DATA_ROOT, uma única vez.
    Retorna a origem migrada (para log) ou None.
    """
    if DB_PATH.exists():
        return None
    for root in _legacy_roots():
        legacy_db = root / "data" / "rje_avaliacoes.db"
        if legacy_db.exists():
            try:
                _copy_tree(root / "data", DATA_DIR)
                if (root / "media").exists():
                    _copy_tree(root / "media", MEDIA_DIR)
                _rewrite_legacy_paths(root)
                (DATA_DIR / "MIGRADO_DE.txt").write_text(str(root), encoding="utf-8")
                return str(root)
            except Exception:
                continue
    return None
