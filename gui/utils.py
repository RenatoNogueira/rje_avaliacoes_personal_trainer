import customtkinter as ctk
import tkinter as tk
from .theme import _c

def set_window_icon(window, logo_path=None):
    """
    Define o ícone de uma janela de forma centralizada com caminhos robustos.
    Prioridade: logo_path informado > icon.ico na raiz > ícone padrão.
    """
    import sys
    import os
    from pathlib import Path
    from PIL import Image, ImageTk
    
    # Determina a raiz do projeto de forma robusta
    if getattr(sys, 'frozen', False):
        # Se estiver rodando como executável PyInstaller
        base_dir = Path(sys._MEIPASS)
    else:
        # Se estiver rodando como script (.py)
        # gui/utils.py -> gui -> raiz
        base_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
    
    candidates = []
    
    # 1. Se foi passado um logo específico (ex: das configurações)
    if logo_path:
        from app_paths import resolve_data_path
        lp = resolve_data_path(logo_path) or Path(logo_path)
        if lp.exists():
            candidates.append(str(lp))
        elif (base_dir / lp).exists():
            candidates.append(str(base_dir / lp))
        
    # 2. Busca icon.ico na raiz do projeto (caminho absoluto)
    root_icon = base_dir / "icon.ico"
    if root_icon.exists():
        candidates.append(str(root_icon))
    
    # 3. Busca em assets/icon.ico (caminho absoluto)
    assets_icon = base_dir / "assets" / "icon.ico"
    if assets_icon.exists():
        candidates.append(str(assets_icon))

    for icon in candidates:
        icon_path = str(Path(icon).absolute())
        try:
            # Tenta múltiplos métodos para garantir exibição no Windows
            if icon_path.lower().endswith(".ico"):
                try:
                    window.iconbitmap(icon_path)
                except:
                    # Alternativa para iconbitmap no Windows
                    window.attributes("-iconbitmap", icon_path)
                
                # Mesmo com .ico, às vezes o iconphoto ajuda na barra de tarefas
                try:
                    img = Image.open(icon_path)
                    photo = ImageTk.PhotoImage(img)
                    window.wm_iconphoto(True, photo) # True para aplicar em todos
                    window._icon_photo_ref = photo
                except:
                    pass
                return True
            else:
                img = Image.open(icon_path)
                photo = ImageTk.PhotoImage(img)
                # wm_iconphoto(True, ...) aplica recursivamente a novas janelas se master
                window.wm_iconphoto(True, photo)
                window._icon_photo_ref = photo
                return True
        except Exception as e:
            print(f"Erro ao definir ícone ({icon_path}): {e}")
            continue
    return False

class ToolTip(object):
    """
    Cria uma tooltip para um widget específico.
    """
    def __init__(self, widget, text="widget info"):
        self.waittime = 500     # milisegundos
        self.wraplength = 180   # pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None
        self.enabled = True

    def enter(self, event=None):
        if not self.enabled or not self.text:
            return
        try:
            self.schedule()
        except Exception:
            pass

    def leave(self, event=None):
        try:
            self.unschedule()
            self.hidetip()
        except Exception:
            pass

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        try:
            if not self.widget.winfo_exists():
                return
            x = self.widget.winfo_rootx() + 25
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4

            # Cria janela de tooltip
            self.hidetip()
            self.tw = tk.Toplevel(self.widget)
            self.tw.wm_overrideredirect(True)
            self.tw.wm_geometry("+%d+%d" % (x, y))
            try:
                self.tw.attributes("-topmost", True)
            except Exception:
                pass

            dark = ctk.get_appearance_mode() == "Dark"
            label = tk.Label(self.tw, text=self.text, justify='left',
                           background=_c("card_bg")[1 if dark else 0],
                           foreground=_c("view_header_title")[1 if dark else 0],
                           relief='solid', borderwidth=1,
                           wraplength=self.wraplength, font=("Segoe UI", 9), padx=6, pady=3)
            label.pack(ipadx=1)
        except Exception:
            self.tw = None

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()

def create_tooltip(widget, text):
    """Função auxiliar para criar tooltips de forma simples"""
    toolTip = ToolTip(widget, text)
    return toolTip

_TOAST_COLORS = {
    "info": ("#334155", "#334155"),
    "success": ("#15803d", "#16a34a"),
    "error": ("#b91c1c", "#dc2626"),
    "warning": ("#b45309", "#d97706"),
}


def show_toast(master, message, duration=2000, kind="info"):
    """
    Exibe uma mensagem temporária (Toast) na parte inferior da janela,
    sem bloquear o usuário. ``kind``: info | success | error | warning.
    """
    import os
    try:
        root = master.winfo_toplevel()
        # Remove toast anterior para não empilhar janelas
        old = getattr(root, "_active_toast", None)
        if old is not None:
            try:
                old.destroy()
            except Exception:
                pass

        toast = ctk.CTkToplevel(root)
        toast.wm_overrideredirect(True)
        root._active_toast = toast

        trans_color = "#f0f0ff"
        if os.name == "nt":
            toast.configure(fg_color=trans_color)
            toast.attributes("-transparentcolor", trans_color)

        root.update_idletasks()
        m_x = root.winfo_rootx()
        m_y = root.winfo_rooty()
        m_w = root.winfo_width()
        m_h = root.winfo_height()

        toast_w = max(340, min(640, 12 * len(str(message)) + 60))
        toast_h = 44

        pos_x = m_x + (m_w - toast_w) // 2
        pos_y = m_y + m_h - 80

        toast.geometry(f"{toast_w}x{toast_h}+{pos_x}+{pos_y}")

        colors = _TOAST_COLORS.get(kind, _TOAST_COLORS["info"])
        mode_idx = 1 if ctk.get_appearance_mode() == "Dark" else 0
        bg_pill = colors[mode_idx]

        frame = ctk.CTkFrame(toast, fg_color=bg_pill, corner_radius=22)
        frame.pack(fill="both", expand=True, padx=2, pady=2)

        icon = {"success": "✔", "error": "✖", "warning": "⚠"}.get(kind, "ℹ")
        label = ctk.CTkLabel(
            frame,
            text=f"{icon}  {message}",
            text_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        label.pack(expand=True, fill="both", padx=20)

        def _close(_e=None):
            try:
                toast.destroy()
            except Exception:
                pass

        label.bind("<Button-1>", _close)
        frame.bind("<Button-1>", _close)
        toast.after(duration, _close)

        toast.lift()
        toast.attributes("-topmost", True)

    except Exception as e:
        print(f"Erro ao exibir toast: {e}")


def debounce(widget, callback, delay_ms: int = 300):
    """
    Retorna uma função que agenda ``callback`` após ``delay_ms`` sem novas chamadas.
    Útil para busca enquanto digita, evitando consultas a cada tecla.
    """
    state = {"job": None}

    def _trigger(*_args):
        if state["job"] is not None:
            try:
                widget.after_cancel(state["job"])
            except Exception:
                pass
        state["job"] = widget.after(delay_ms, _run)

    def _run():
        state["job"] = None
        try:
            if widget.winfo_exists():
                callback()
        except Exception:
            pass

    return _trigger


def bind_live_search(entry, callback, delay_ms: int = 300):
    """Busca enquanto digita (com debounce) + Enter imediato + Esc limpa."""
    trigger = debounce(entry, callback, delay_ms)
    _NAV = {"Up", "Down", "Left", "Right", "Home", "End", "Tab", "Shift_L", "Shift_R",
            "Control_L", "Control_R", "Alt_L", "Alt_R", "Return", "Escape"}

    def on_key(event):
        if event.keysym in _NAV:
            return
        trigger()

    def on_escape(_e):
        entry.delete(0, "end")
        callback()
        return "break"

    entry.bind("<KeyRelease>", on_key, add="+")
    entry.bind("<Return>", lambda e: callback(), add="+")
    entry.bind("<Escape>", on_escape, add="+")


def ask_save_pdf(parent, default_name: str, title: str):
    """Diálogo 'Salvar PDF' abrindo na pasta Documentos/RJE Avaliacoes."""
    from tkinter import filedialog
    import app_paths
    from utils.app_support import safe_filename

    base = default_name[:-4] if default_name.lower().endswith(".pdf") else default_name
    return filedialog.asksaveasfilename(
        parent=parent.winfo_toplevel(),
        defaultextension=".pdf",
        filetypes=[("PDF", "*.pdf")],
        initialdir=str(app_paths.documents_dir()),
        initialfile=safe_filename(base, 80) + ".pdf",
        title=title,
    )


def run_pdf_export(parent, generator, output_path) -> bool:
    """
    Executa a geração de PDF com cursor de espera, tratamento de erro e
    oferta para abrir o arquivo gerado.
    """
    from pathlib import Path
    from tkinter import messagebox
    from utils.app_support import open_path, log

    top = parent.winfo_toplevel()
    try:
        top.configure(cursor="watch")
        top.update_idletasks()
        generator()
    except PermissionError:
        messagebox.showerror(
            "PDF",
            "Não foi possível salvar o arquivo.\n\n"
            "Verifique se ele não está aberto em outro programa (ex.: leitor de PDF) e tente novamente.",
            parent=top,
        )
        return False
    except Exception as exc:
        log.exception("Falha ao gerar PDF")
        messagebox.showerror("PDF", f"Não foi possível gerar o PDF.\n\nDetalhe: {exc}", parent=top)
        return False
    finally:
        try:
            top.configure(cursor="")
        except Exception:
            pass

    if messagebox.askyesno("PDF gerado", f"PDF salvo em:\n{output_path}\n\nDeseja abrir o arquivo agora?", parent=top):
        open_path(Path(output_path))
    return True


def setup_enter_navigation(parent):
    """
    Configura a navegação com a tecla Enter entre os campos de entrada (Entry, ComboBox).
    Percorre os widgets na ordem de criação (winfo_children) e faz o bind do <Return>.
    """
    widgets = []

    def collect_widgets(widget):
        # Se for um container, explora os filhos
        if isinstance(widget, (ctk.CTkFrame, ctk.CTkScrollableFrame, ctk.CTkTabview)):
            # Se for Tabview, precisa iterar pelas abas
            if isinstance(widget, ctk.CTkTabview):
                for tab_name in widget._tab_dict:
                    collect_widgets(widget.tab(tab_name))
            else:
                for child in widget.winfo_children():
                    collect_widgets(child)
        
        # Se for um widget de entrada
        elif isinstance(widget, (ctk.CTkEntry, ctk.CTkComboBox)):
            # Ignora widgets desabilitados ou readonly se possível (mas state='normal' é o padrão)
            try:
                if widget.cget("state") != "disabled":
                    widgets.append(widget)
            except:
                widgets.append(widget)

    collect_widgets(parent)

    for i, widget in enumerate(widgets[:-1]):
        next_widget = widgets[i+1]
        
        def focus_next(event=None, w=next_widget):
            try:
                w.focus_set()
            except Exception:
                pass
            return "break"
            
        # Bind no widget interno do CTk (entry)
        # CTkEntry e ComboBox expõem bind, mas o foco real está nos componentes internos
        try:
            widget.bind("<Return>", focus_next)
        except Exception:
            pass

def delete_folder_recursive(path):
    """
    Remove uma pasta e todo o seu conteúdo recursivamente.
    """
    import shutil
    from pathlib import Path
    try:
        p = Path(path)
        if p.exists() and p.is_dir():
            shutil.rmtree(p)
            return True
    except Exception as e:
        print(f"Erro ao remover pasta {path}: {e}")
    return False

def delete_files_with_prefix(directory, prefix):
    """
    Remove todos os arquivos em um diretório que começam com um determinado prefixo.
    """
    from pathlib import Path
    try:
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            return False
        
        deleted_count = 0
        for item in dir_path.iterdir():
            if item.is_file() and item.name.startswith(prefix):
                item.unlink()
                deleted_count += 1
        return deleted_count > 0
    except Exception as e:
        print(f"Erro ao remover arquivos com prefixo {prefix} em {directory}: {e}")
    return False
