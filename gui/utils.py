import customtkinter as ctk
import tkinter as tk

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
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

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
                       background="#ffffe0", relief='solid', borderwidth=1,
                       wraplength = self.wraplength, font=("tahoma", "8", "normal"))
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
        frame = ctk.CTkFrame(toast, fg_color="#333333", corner_radius=20)
        frame.pack(fill="both", expand=True)
        
        label = ctk.CTkLabel(frame, text=message, text_color="white", font=("Arial", 12))
        label.pack(expand=True, fill="both")
        
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
        
        def focus_next(event, w=next_widget):
            try:
                w.focus_set()
            except Exception:
                pass
            return "break"
            
        # Bind no widget interno do CTk (entry)
        # CTkEntry e ComboBox expõem bind, mas o foco real está nos componentes internos
        widget.bind("<Return>", focus_next)
