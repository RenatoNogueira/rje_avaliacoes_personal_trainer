import sys

try:
    import customtkinter  # noqa: F401
except ImportError:
    print(
        "A biblioteca 'customtkinter' não está instalada.\n"
        "Instale com: pip install -r requirements.txt"
    )
    sys.exit(1)

from utils.app_support import (
    acquire_single_instance,
    install_exception_hooks,
    log,
    setup_logging,
)


def main() -> None:
    setup_logging()
    install_exception_hooks()

    # Impede duas janelas do sistema abertas ao mesmo tempo (evita conflitos no banco)
    if not acquire_single_instance():
        from tkinter import Tk, messagebox

        r = Tk()
        r.withdraw()
        messagebox.showinfo(
            "RJE Avaliações",
            "O RJE Avaliações já está aberto.\nVerifique a barra de tarefas.",
        )
        r.destroy()
        return

    from utils.self_installer import SelfInstaller

    # Gerencia auto-instalação (somente quando executado fora de uma instalação)
    SelfInstaller.run()

    import app_paths
    from version import __version__

    # Versões antigas distribuíam um .env com token do GitHub: removido por segurança
    if app_paths.IS_FROZEN:
        try:
            (app_paths.APP_DIR / ".env").unlink(missing_ok=True)
        except Exception:
            pass

    log.info("Iniciando RJE Avaliações v%s | dados em %s", __version__, app_paths.DATA_ROOT)

    from database import db  # noqa: F401  (inicializa/migra o banco)
    from gui import Application

    app = Application()
    app.mainloop()


if __name__ == "__main__":
    main()
