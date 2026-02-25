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
        lp = Path(logo_path)
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

    def enter(self, event=None):
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
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        
        # Cria janela de tooltip
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background=_c("card_bg")[1] if ctk.get_appearance_mode() == "Dark" else _c("card_bg")[0], 
                       foreground=_c("view_header_title")[1] if ctk.get_appearance_mode() == "Dark" else _c("view_header_title")[0],
                       relief='solid', borderwidth=1,
                       wraplength = self.wraplength, font=("Inter", "9"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()

def create_tooltip(widget, text):
    """Função auxiliar para criar tooltips de forma simples"""
    toolTip = ToolTip(widget, text)
    return toolTip

def show_toast(master, message, duration=2000):
    """
    Exibe uma mensagem temporária (Toast) na parte inferior da tela.
    """
    try:
        # Cria uma janela Toplevel sem bordas
        toast = ctk.CTkToplevel(master)
        toast.wm_overrideredirect(True)
        
        # Posiciona no centro inferior
        # Obtém geometria da janela principal
        master_x = master.winfo_rootx()
        master_y = master.winfo_rooty()
        master_w = master.winfo_width()
        master_h = master.winfo_height()
        
        # Tamanho do toast
        toast_w = 300
        toast_h = 40
        
        pos_x = master_x + (master_w - toast_w) // 2
        pos_y = master_y + master_h - 100
        
        toast.geometry(f"{toast_w}x{toast_h}+{pos_x}+{pos_y}")
        
        # Frame e Label
        frame = ctk.CTkFrame(toast, fg_color=_c("view_header_icon"), corner_radius=20)
        frame.pack(fill="both", expand=True)
        
        label = ctk.CTkLabel(frame, text=message, text_color="white", font=ctk.CTkFont(family="Inter", size=13, weight="bold"))
        label.pack(expand=True, fill="both", padx=20)
        
        # Fecha após duration ms
        toast.after(duration, toast.destroy)
        
        # Tenta colocar no topo
        toast.lift()
        
    except Exception:
        pass

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
