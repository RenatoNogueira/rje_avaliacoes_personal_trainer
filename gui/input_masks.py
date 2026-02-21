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


def bind_mask(entry: tk.Entry, kind: str) -> None:
    def on_key_release(_event):
        val = entry.get()
        if kind == "cpf":
            masked = format_cpf_value(val)
        elif kind == "cep":
            masked = format_cep_value(val)
        elif kind == "tel":
            masked = format_tel_value(val)
        elif kind == "date":
            masked = format_date_br_value(val)
        elif kind == "time":
            masked = format_time_value(val)
        else:
            masked = val
        _apply(entry, masked)

    entry.bind("<KeyRelease>", on_key_release, add="+")


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
