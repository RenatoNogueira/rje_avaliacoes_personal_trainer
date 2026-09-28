"""
Infraestrutura de suporte do aplicativo desktop:

* log em arquivo (rotativo) — no executável sem console, é a única forma de
  diagnosticar erros;
* tratamento global de exceções (Python e callbacks do Tkinter) com mensagem
  amigável ao usuário em vez de falhas silenciosas;
* trava de instância única (evita dois processos gravando o mesmo banco);
* backup automático diário do banco de dados, mantendo os mais recentes;
* utilitário para abrir arquivos/pastas com o programa padrão do sistema.
"""

from __future__ import annotations

import datetime
import logging
import os
import subprocess
import sys
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path

import app_paths

log = logging.getLogger("rje")


def setup_logging() -> None:
    if log.handlers:
        return
    log.setLevel(logging.INFO)
    try:
        handler = RotatingFileHandler(
            app_paths.LOG_DIR / "rje_avaliacoes.log",
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        log.addHandler(handler)
    except Exception:
        pass
    if not app_paths.IS_FROZEN:
        log.addHandler(logging.StreamHandler(sys.stderr))


def _friendly_error(exc_type, exc_value, exc_tb) -> None:
    detail = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    log.error("Erro não tratado:\n%s", detail)
    try:
        from tkinter import messagebox

        messagebox.showerror(
            "Ops! Algo deu errado",
            "Ocorreu um erro inesperado, mas seus dados estão seguros.\n\n"
            f"Detalhe: {exc_value}\n\n"
            f"Um registro técnico foi salvo em:\n{app_paths.LOG_DIR}",
        )
    except Exception:
        pass


def install_exception_hooks(tk_root=None) -> None:
    """Registra tratamento global de exceções (sys.excepthook e Tk)."""

    def _hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        # Corridas inofensivas do Tk (callback agendado para uma janela já fechada):
        # apenas registra no log, sem incomodar o usuário.
        msg = str(exc_value)
        if exc_type.__name__ == "TclError" and (
            "bad window path name" in msg or "invalid command name" in msg
        ):
            log.info("TclError ignorado: %s", msg)
            return
        _friendly_error(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook
    if tk_root is not None:
        tk_root.report_callback_exception = _hook


# ────────────────────────── Instância única ─────────────────────────────────
_mutex_handle = None


def acquire_single_instance() -> bool:
    """
    Retorna False se já existir outra instância aberta (somente Windows).
    Em outros sistemas sempre retorna True.
    """
    global _mutex_handle
    if os.name != "nt":
        return True
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        _mutex_handle = kernel32.CreateMutexW(None, False, "Global\\RJE_Avaliacoes_SingleInstance")
        ERROR_ALREADY_EXISTS = 183
        return kernel32.GetLastError() != ERROR_ALREADY_EXISTS
    except Exception:
        return True


# ─────────────────────────── Backup automático ──────────────────────────────

def auto_backup(db, keep: int = 10) -> Path | None:
    """
    Cria no máximo um backup por dia em DATA_ROOT/backups/auto e mantém
    apenas os ``keep`` mais recentes.
    """
    try:
        auto_dir = app_paths.BACKUP_DIR / "auto"
        auto_dir.mkdir(parents=True, exist_ok=True)
        today = datetime.date.today().isoformat()
        target = auto_dir / f"rje_avaliacoes_{today}.db"
        if not target.exists() and Path(db.db_path).exists():
            db.backup_to(target)
            log.info("Backup automático criado: %s", target)
        backups = sorted(auto_dir.glob("rje_avaliacoes_*.db"), reverse=True)
        for old in backups[keep:]:
            try:
                old.unlink()
            except Exception:
                pass
        return target
    except Exception as exc:
        log.warning("Falha no backup automático: %s", exc)
        return None


# ───────────────────────────── Abrir arquivos ───────────────────────────────

def open_path(path: str | Path) -> bool:
    """Abre um arquivo ou pasta com o aplicativo padrão do sistema."""
    try:
        p = str(path)
        if os.name == "nt":
            os.startfile(p)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", p])
        else:
            subprocess.Popen(["xdg-open", p])
        return True
    except Exception as exc:
        log.warning("Não foi possível abrir %s: %s", path, exc)
        return False


def safe_filename(text: str, max_len: int = 60) -> str:
    """Remove caracteres inválidos em nomes de arquivo do Windows."""
    import re
    import unicodedata

    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9._ -]+", "", text).strip().replace(" ", "_")
    return (text or "arquivo")[:max_len]
