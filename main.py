import sys

try:
    import customtkinter  # noqa: F401
except ImportError:
    print(
        "A biblioteca 'customtkinter' não está instalada.\n"
        "Instale com: pip install customtkinter"
    )
    sys.exit(1)

from database import db  # noqa: F401
from gui import Application
from utils.self_installer import SelfInstaller


def main() -> None:
    # Gerencia auto-instalação
    SelfInstaller.run()
    
    app = Application()
    app.mainloop()


if __name__ == "__main__":
    main()
