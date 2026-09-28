import re
import tkinter as tk


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def _apply(entry: tk.Entry, text: str) -> None:
    entry.delete(0, "end")
    entry.insert(0, text)
    try:
        entry.icursor(len(text))
    except Exception:
        pass


def format_cpf_value(raw: str) -> str:
    d = _digits(raw)[:11]
    parts = []
    if len(d) > 3:
        parts.append(d[:3])
        d = d[3:]
    else:
        return d
    if len(d) > 3:
        parts.append(d[:3])
        d = d[3:]
    else:
        return ".".join(parts + [d])
    if len(d) > 2:
        parts.append(d[:3])
        rest = d[3:]
        if rest:
            return ".".join(parts) + "-" + rest
        return ".".join(parts)
    return ".".join(parts + [d])


def format_cep_value(raw: str) -> str:
    d = _digits(raw)[:8]
    if len(d) <= 5:
        return d
    return d[:5] + "-" + d[5:]


def format_tel_value(raw: str) -> str:
    d = _digits(raw)[:11]
    if not d:
        return ""
    if len(d) <= 2:
        return f"({d}"
    if len(d) <= 7:
        return f"({d[:2]}) {d[2:]}"
    if len(d) <= 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return f"({d[:2]}) {d[2:7]}-{d[7:]}"


def format_date_br_value(raw: str) -> str:
    d = _digits(raw)[:8]
    if len(d) <= 2:
        return d
    if len(d) <= 4:
        return d[:2] + "/" + d[2:]
    return d[:2] + "/" + d[2:4] + "/" + d[4:]


def format_time_value(raw: str) -> str:
    d = _digits(raw)[:4]
    if len(d) <= 2:
        return d
    return d[:2] + ":" + d[2:]


def format_altura_value(raw: str) -> str:
    d = _digits(raw)[:3]
    if len(d) <= 2:
        return d
    return d[0] + "." + d[1:]


def format_int3_value(raw: str) -> str:
    return _digits(raw)[:3]


def add_calendar_to_entry(entry: tk.Entry) -> None:
    """
    Seletor de data: duplo clique, F4 ou Alt+↓ abrem o calendário.
    (Antes abria a cada clique, atrapalhando quem só queria digitar/corrigir a data.)
    """
    from .calendar_dialog import CalendarDialog

    def open_cal(_e=None):
        if getattr(entry, "_cal_open", False):
            return "break"

        def on_select(date_str):
            entry.delete(0, "end")
            entry.insert(0, date_str)
            entry._cal_open = False
            entry.event_generate("<KeyRelease>")
            try:
                entry.focus_set()
            except Exception:
                pass

        entry._cal_open = True
        top = entry.winfo_toplevel()
        cal = CalendarDialog(top, current_date_str=entry.get(), callback=on_select, anchor_widget=entry)

        def on_close():
            entry._cal_open = False
            cal.destroy()

        cal.protocol("WM_DELETE_WINDOW", on_close)
        cal.bind("<Destroy>", lambda e: setattr(entry, "_cal_open", False), add="+")
        return "break"

    entry.bind("<Double-Button-1>", open_cal, add="+")
    entry.bind("<F4>", open_cal, add="+")
    entry.bind("<Alt-Down>", open_cal, add="+")
    try:
        from .utils import create_tooltip
        create_tooltip(entry, "Digite a data (DD/MM/AAAA) ou dê duplo clique / F4 para abrir o calendário")
    except Exception:
        pass


_FORMATTERS = {
    "cpf": lambda v: format_cpf_value(v),
    "cep": lambda v: format_cep_value(v),
    "tel": lambda v: format_tel_value(v),
    "date": lambda v: format_date_br_value(v),
    "time": lambda v: format_time_value(v),
    "altura": lambda v: format_altura_value(v),
    "int3": lambda v: format_int3_value(v),
}

_IGNORED_KEYS = {
    "Left", "Right", "Up", "Down", "Home", "End", "Tab", "ISO_Left_Tab",
    "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
    "Caps_Lock", "Escape", "Return", "KP_Enter", "Prior", "Next", "F4",
}


def bind_mask(entry: tk.Entry, kind: str) -> None:
    formatter = _FORMATTERS.get(kind, lambda v: v)

    def on_key_release(event):
        # Não reformatar em teclas de navegação (mantém o cursor onde o usuário deixou)
        if getattr(event, "keysym", "") in _IGNORED_KEYS:
            return
        val = entry.get()
        masked = formatter(val)
        if masked == val:
            return
        try:
            cursor = entry.index("insert")
        except Exception:
            cursor = len(val)
        # posição proporcional em dígitos para não jogar o cursor para o fim
        digits_before = len(_digits(val[:cursor]))
        _apply(entry, masked)
        pos = 0
        count = 0
        for i, ch in enumerate(masked):
            if count >= digits_before:
                break
            if ch.isdigit():
                count += 1
            pos = i + 1
        try:
            entry.icursor(pos if cursor < len(val) else len(masked))
        except Exception:
            pass

    entry.bind("<KeyRelease>", on_key_release, add="+")

    if kind == "date":
        add_calendar_to_entry(entry)


def is_valid_cpf(raw: str) -> bool:
    d = _digits(raw)
    if len(d) != 11:
        return False
    if d == d[0] * 11:
        return False
    try:
        nums = [int(x) for x in d]
    except Exception:
        return False
    s1 = sum(nums[i] * (10 - i) for i in range(9))
    r1 = s1 % 11
    dv1 = 0 if r1 < 2 else 11 - r1
    if nums[9] != dv1:
        return False
    s2 = sum(nums[i] * (11 - i) for i in range(10))
    r2 = s2 % 11
    dv2 = 0 if r2 < 2 else 11 - r2
    return nums[10] == dv2


def is_valid_cep(raw: str) -> bool:
    d = _digits(raw)
    return len(d) == 8


def only_digits(raw: str | None) -> str:
    return _digits(raw or "")
