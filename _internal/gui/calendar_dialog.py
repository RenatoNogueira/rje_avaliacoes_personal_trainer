import calendar
import datetime
import customtkinter as ctk
from .theme import _c, font_subtitle, font_body
from .utils import set_window_icon

class CalendarDialog(ctk.CTkToplevel):
    def __init__(self, master, current_date_str=None, callback=None):
        super().__init__(master)
        
        self.title("Selecionar Data")
        self.geometry("380x420")
        self.resizable(False, False)
        set_window_icon(self, getattr(master, "logo_path", None))
        
        self.transient(master)
        self.grab_set()
        self.focus_force()
        self.after(10, self.lift) # Garante que fique no topo
        
        self.callback = callback
        
        # Tenta parsear a data atual ou usa hoje
        try:
            if current_date_str:
                self.selected_date = datetime.datetime.strptime(current_date_str, "%d/%m/%Y").date()
            else:
                self.selected_date = datetime.date.today()
        except Exception:
            self.selected_date = datetime.date.today()
            
        self.view_month = self.selected_date.month
        self.view_year = self.selected_date.year
        
        self.configure(fg_color=_c("panel_bg"))
        
        # Header: Mês e Ano + Navegação
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=15, pady=(15, 10))
        
        self.btn_prev = ctk.CTkButton(
            self.header, text="<", width=30, height=30, 
            fg_color="transparent", text_color=_c("view_header_title"),
            hover_color=_c("card_hover"), command=self.prev_month
        )
        self.btn_prev.pack(side="left")
        
        self.lbl_month_year = ctk.CTkLabel(
            self.header, text="", font=ctk.CTkFont(size=15, weight="bold"),
            text_color=_c("view_header_title")
        )
        self.lbl_month_year.pack(side="left", expand=True)
        
        self.btn_next = ctk.CTkButton(
            self.header, text=">", width=30, height=30, 
            fg_color="transparent", text_color=_c("view_header_title"),
            hover_color=_c("card_hover"), command=self.next_month
        )
        self.btn_next.pack(side="right")
        
        # Grid de Dias da Semana
        self.grid_days = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_days.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Configura colunas uniformes (0-6)
        for i in range(7):
            self.grid_days.grid_columnconfigure(i, weight=1, uniform="cal")

        dias_semana = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
        for i, dia in enumerate(dias_semana):
            lbl = ctk.CTkLabel(
                self.grid_days, text=dia, font=ctk.CTkFont(size=11, weight="bold"),
                text_color="gray"
            )
            lbl.grid(row=0, column=i, sticky="nsew", pady=(0, 5))
            
        self.days_buttons = []
        self.render_calendar()
        
        # Footer: Hoje e Fechar
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.pack(fill="x", padx=15, pady=(0, 15))
        
        self.btn_today = ctk.CTkButton(
            self.footer, text="Hoje", width=80, height=28,
            fg_color=_c("list_card_accent"), text_color="white",
            command=self.set_today
        )
        self.btn_today.pack(side="left")
        
        self.btn_cancel = ctk.CTkButton(
            self.footer, text="Cancelar", width=80, height=28,
            fg_color="transparent", border_width=1, border_color=_c("card_border"),
            text_color=_c("view_header_title"), command=self.destroy
        )
        self.btn_cancel.pack(side="right")

    def render_calendar(self):
        # Limpa botões antigos
        for btn in self.days_buttons:
            btn.destroy()
        self.days_buttons = []
        
        # Atualiza Label
        meses = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        self.lbl_month_year.configure(text=f"{meses[self.view_month]} {self.view_year}")
        
        # Lógica do Calendário
        cal = calendar.monthcalendar(self.view_year, self.view_month)
        today = datetime.date.today()
        
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day == 0:
                    continue
                
                # Formata cor se for o selecionado ou hoje
                is_selected = (day == self.selected_date.day and 
                               self.view_month == self.selected_date.month and 
                               self.view_year == self.selected_date.year)
                is_today = (day == today.day and 
                            self.view_month == today.month and 
                            self.view_year == today.year)
                
                fg_color = "transparent"
                border_width = 0
                text_color = _c("view_header_title")
                
                if is_selected:
                    fg_color = _c("list_card_accent")
                    text_color = "white"
                elif is_today:
                    border_width = 1
                    text_color = _c("list_card_accent")
                
                btn = ctk.CTkButton(
                    self.grid_days, text=str(day), width=34, height=34,
                    fg_color=fg_color, border_width=border_width, 
                    border_color=_c("list_card_accent"),
                    text_color=text_color, corner_radius=17,
                    hover_color=_c("card_hover"),
                    command=lambda d=day: self.select_day(d)
                )
                btn.grid(row=r+1, column=c, padx=1, pady=1)
                self.days_buttons.append(btn)

    def select_day(self, day):
        new_date = datetime.date(self.view_year, self.view_month, day)
        date_str = new_date.strftime("%d/%m/%Y")
        if self.callback:
            self.callback(date_str)
        self.destroy()

    def prev_month(self):
        self.view_month -= 1
        if self.view_month < 1:
            self.view_month = 12
            self.view_year -= 1
        self.render_calendar()

    def next_month(self):
        self.view_month += 1
        if self.view_month > 12:
            self.view_month = 1
            self.view_year += 1
        self.render_calendar()

    def set_today(self):
        today = datetime.date.today()
        if self.callback:
            self.callback(today.strftime("%d/%m/%Y"))
        self.destroy()
