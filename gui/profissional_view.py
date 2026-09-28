from pathlib import Path
from tkinter import filedialog, messagebox
from PIL import Image

import customtkinter as ctk
from .theme import _c, font_body, font_subtitle, font_small, create_view_header, create_action_button, create_section_title, create_info_badge
from .utils import setup_enter_navigation, create_tooltip
from .input_masks import bind_mask
from utils.image_utils import create_circular_image
from .utils import show_toast
import app_paths


def _fit_size(pil_img, box: int) -> tuple[int, int]:
    """Tamanho que cabe em box×box mantendo a proporção da imagem."""
    w, h = pil_img.size
    scale = box / max(w, h) if max(w, h) else 1
    return max(1, int(w * scale)), max(1, int(h * scale))


class ProfissionalView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        professor_var: ctk.StringVar,
        marca_var: ctk.StringVar,
        email_var: ctk.StringVar,
        telefone_var: ctk.StringVar,
        cref_var: ctk.StringVar,
        get_logo_path,
        set_branding,
        current_user=None,
        on_update_profile=None,
        cidade_var=None,
        accent_color_var=None
    ) -> None:
        super().__init__(master)
        self.professor_var = professor_var
        self.marca_var = marca_var
        self.email_var = email_var
        self.telefone_var = telefone_var
        self.cref_var = cref_var
        self.get_logo_path = get_logo_path
        self.set_branding = set_branding
        # Converter Row para dict para permitir .get() e evitar erros
        self.current_user = dict(current_user) if current_user else None
        self.on_update_profile = on_update_profile
        self.cidade_var = cidade_var
        self.accent_color_var = accent_color_var
        self.selected_logo_path: str | None = None
        _foto = self.current_user.get("foto_perfil") if self.current_user else None
        _foto_res = app_paths.resolve_data_path(_foto) if _foto else None
        self.foto_perfil_path: str | None = str(_foto_res) if _foto_res else None

        # Layout: Left (Preview Card), Right (Form)
        self.grid_columnconfigure(0, weight=1)  # Left panel (smaller)
        self.grid_columnconfigure(1, weight=2)  # Right panel (larger)
        self.grid_rowconfigure(0, weight=1)

        # --- Left Panel: Preview / "Cartão de Visita" ---
        self.left_panel = ctk.CTkFrame(self, corner_radius=15)
        self.left_panel.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")
        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(4, weight=1) # Push content up

        ctk.CTkLabel(
            self.left_panel,
            text="Visualização",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=_c("view_header_subtitle")
        ).grid(row=0, column=0, padx=20, pady=(20, 10))

        # Card Container
        self.card_frame = ctk.CTkFrame(self.left_panel, fg_color=_c("card_bg"), corner_radius=15, border_width=1, border_color=_c("card_border"))
        self.card_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.card_frame.grid_columnconfigure(0, weight=1)

        # Logo Preview
        self.logo_preview = ctk.CTkLabel(self.card_frame, text="[Sem Logo]", width=100, height=100)
        self.logo_preview.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        # Brand Preview
        self.lbl_marca_preview = ctk.CTkLabel(
            self.card_frame, 
            textvariable=self.marca_var,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.lbl_marca_preview.grid(row=1, column=0, padx=10, pady=(0, 5))

        # Foto Perfil Preview (Miniatura circular)
        self.lbl_foto_perfil_preview = ctk.CTkLabel(
            self.card_frame, 
            text="👤", 
            width=80, 
            height=80, 
            fg_color="gray50", 
            corner_radius=40 # Circular se suportado pelo tema/renderizador
        )
        self.lbl_foto_perfil_preview.grid(row=2, column=0, pady=(10, 5))

        # Professor Name Preview
        self.lbl_prof_preview = ctk.CTkLabel(
            self.card_frame,
            textvariable=self.professor_var,
            font=ctk.CTkFont(size=14)
        )
        self.lbl_prof_preview.grid(row=3, column=0, padx=10, pady=(0, 20))

        # Contact Info Preview
        self.contact_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.contact_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.contact_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.contact_frame, text="📧").grid(row=0, column=0, padx=(0, 5), sticky="e")
        ctk.CTkLabel(self.contact_frame, textvariable=self.email_var, anchor="w").grid(row=0, column=1, sticky="ew")
        
        ctk.CTkLabel(self.contact_frame, text="📞").grid(row=1, column=0, padx=(0, 5), sticky="e")
        ctk.CTkLabel(self.contact_frame, textvariable=self.telefone_var, anchor="w").grid(row=1, column=1, sticky="ew")

        ctk.CTkLabel(self.contact_frame, text="🆔").grid(row=2, column=0, padx=(0, 5), sticky="e")
        ctk.CTkLabel(self.contact_frame, textvariable=self.cref_var, anchor="w").grid(row=2, column=1, sticky="ew")

        # Reload Preview Button
        create_action_button(
            self.left_panel,
            "Atualizar Visualização",
            "btn_pdf", # Using primary color
            self._update_preview,
            width=200
        ).grid(row=3, column=0, padx=20, pady=20)


        # --- Right Panel: Edit Form ---
        self.right_panel = ctk.CTkFrame(self, corner_radius=15)
        self.right_panel.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1) # Scrollable area expands

        # Header
        self.header = create_view_header(self.right_panel, "👤", "Identidade Visual", "Personalize a aparência dos seus relatórios")
        self.header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Scrollable Form Area
        self.scroll_form = ctk.CTkScrollableFrame(self.right_panel, fg_color="transparent")
        self.scroll_form.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.scroll_form.grid_columnconfigure(0, weight=1)

        # Form Container (dentro do scroll)
        self.form_container = ctk.CTkFrame(self.scroll_form, fg_color="transparent")
        self.form_container.grid(row=0, column=0, padx=10, sticky="ew")
        self.form_container.grid_columnconfigure(1, weight=1)

        row = 0
        create_section_title(self.form_container, "Perfil do Profissional").grid(row=row, column=0, columnspan=2, padx=16, pady=(18, 8), sticky="w")

        row += 1
        
        # Foto de Perfil
        ctk.CTkLabel(self.form_container, text="Foto de Perfil:", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, padx=10, pady=10, sticky="e"
        )
        frame_foto = ctk.CTkFrame(self.form_container, fg_color="transparent")
        frame_foto.grid(row=row, column=1, padx=10, pady=10, sticky="w")
        create_action_button(frame_foto, "📸 Selecionar", "btn_new", self.on_select_foto_perfil, width=120).pack(side="left", padx=(0, 10))
        create_action_button(frame_foto, "🗑️ Remover", "btn_delete", self.on_remove_foto_perfil, width=120).pack(side="left")
        
        row += 1
        self._add_form_row(row, "Nome do Profissional:", self.professor_var)
        row += 1
        self._add_form_row(row, "Nome da Marca/Empresa:", self.marca_var)
        row += 1
        self._add_form_row(row, "E-mail de Contato:", self.email_var)
        row += 1
        
        # Telefone com máscara
        ctk.CTkLabel(self.form_container, text="Telefone:", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, padx=10, pady=10, sticky="e"
        )
        self.entry_telefone = ctk.CTkEntry(self.form_container, textvariable=self.telefone_var)
        self.entry_telefone.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        bind_mask(self.entry_telefone, "tel")
        
        row += 1
        self._add_form_row(row, "CREF:", self.cref_var)
        
        row += 1
        create_section_title(self.form_container, "Identidade da Marca").grid(row=row, column=0, columnspan=2, padx=16, pady=(18, 8), sticky="w")
        
        logo_controls = ctk.CTkFrame(self.form_container, fg_color="transparent")
        logo_controls.grid(row=row, column=1, padx=10, pady=(10, 5), sticky="ew")
        logo_controls.grid_columnconfigure(0, weight=1)

        self.entry_logo = ctk.CTkEntry(logo_controls, placeholder_text="Caminho do arquivo...")
        self.entry_logo.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        current_logo = self.get_logo_path()
        if current_logo:
            self.entry_logo.insert(0, current_logo)

        create_action_button(
            logo_controls, 
            "📁 Escolher", 
            "btn_save",
            self.on_escolher_logo,
            width=100
        ).grid(row=0, column=1)

        # Save Button Area (Footer fixo no right_panel)
        self.btn_salvar = create_action_button(
            self.right_panel,
            "💾 Salvar Alterações",
            "btn_save",
            self.on_salvar,
            height=45,
            width=None # Fill
        )
        self.btn_salvar.grid(row=2, column=0, padx=20, pady=20, sticky="ew")

        # Initial Preview Load
        self._update_preview()
        
        setup_enter_navigation(self.form_container)

    def _add_form_row(self, row, label_text, variable):
        ctk.CTkLabel(self.form_container, text=label_text, font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, padx=10, pady=10, sticky="e"
        )
        ctk.CTkEntry(self.form_container, textvariable=variable).grid(
            row=row, column=1, padx=10, pady=10, sticky="ew"
        )

    def _update_preview(self):
        # Update Logo Image
        logo_path = self.selected_logo_path or self.get_logo_path()
        if logo_path and Path(logo_path).exists():
            try:
                pil_img = Image.open(logo_path)
                # Preview mantendo a proporção (antes a logo era esticada para 100x100)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=_fit_size(pil_img, 100))
                self.logo_preview.configure(image=ctk_img, text="")
                self.logo_preview._image_ref = ctk_img
            except Exception:
                self.logo_preview.configure(image=None, text="[Erro Imagem]")
        else:
            self.logo_preview.configure(image=None, text="[Sem Logo]")

        # Update Foto Perfil
        if self.foto_perfil_path and Path(self.foto_perfil_path).exists():
            try:
                pil_img = create_circular_image(self.foto_perfil_path, (160, 160))
                if pil_img:
                    ctk_img = ctk.CTkImage(pil_img, size=(80, 80))
                    self.lbl_foto_perfil_preview.configure(image=ctk_img, text="", fg_color="transparent")
                    self.lbl_foto_perfil_preview._image_ref = ctk_img
            except Exception:
                self.lbl_foto_perfil_preview.configure(image=None, text="Erro", fg_color="gray50")
        else:
            self.lbl_foto_perfil_preview.configure(image=None, text="👤", fg_color="gray50")

    def on_select_foto_perfil(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp *.bmp")],
            title="Selecionar foto de perfil",
        )
        if file_path:
            self.foto_perfil_path = file_path
            self._update_preview()

    def on_remove_foto_perfil(self):
        self.foto_perfil_path = None
        self._update_preview()

    def on_escolher_logo(self) -> None:
        file_path = filedialog.askopenfilename(
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp"), ("Todos os arquivos", "*.*")],
            title="Selecionar arquivo de logo",
        )
        if not file_path:
            return
        self.selected_logo_path = file_path
        self.entry_logo.delete(0, "end")
        self.entry_logo.insert(0, file_path)
        self._update_preview()

    def on_salvar(self) -> None:
        marca = self.marca_var.get().strip()
        logo_input = self.entry_logo.get().strip()
        logo_target = ""
        
        if logo_input:
            # Check if it's already the target path to avoid copy error
            try:
                branding_dir = app_paths.DATA_DIR / "branding"
                branding_dir.mkdir(parents=True, exist_ok=True)
                logo_target_path = branding_dir / "logo.png"
                src = app_paths.resolve_data_path(logo_input) or Path(logo_input)
                if not Path(src).exists():
                    messagebox.showwarning("Profissional e Logo", "Arquivo de logo não encontrado. Escolha novamente.")
                    return
                
                # Copia (convertendo para PNG real) somente se a origem for diferente
                if Path(src).resolve() != logo_target_path.resolve():
                    try:
                        Image.open(src).save(logo_target_path, format="PNG")
                    except Exception:
                        from shutil import copyfile
                        copyfile(src, logo_target_path)
                
                logo_target = str(logo_target_path)
            except Exception as exc:
                messagebox.showerror("Profissional e Logo", f"Erro ao salvar logo: {exc}")
                return

        if not logo_target:
            # If input is empty but we have a previous one
            logo_target = self.get_logo_path() or ""
            # If user cleared the input manually to remove logo?
            if not logo_input: 
                logo_target = "" # Clear logo if field is empty

        email = self.email_var.get().strip()
        telefone = self.telefone_var.get().strip()
        cref = self.cref_var.get().strip()
        
        self.set_branding(logo_target, marca, email, telefone, cref)

        # Atualiza foto de perfil e telefone do usuário logado
        if self.on_update_profile and self.current_user:
            try:
                user_id = int(self.current_user["id"])
                
                # Copiar foto para pasta gerenciada se for nova
                final_foto_path = self.foto_perfil_path
                if self.foto_perfil_path and Path(self.foto_perfil_path).exists():
                    # Verifica se já não está na pasta de media
                    media_dir = app_paths.MEDIA_DIR / "usuarios"
                    media_dir.mkdir(parents=True, exist_ok=True)
                    
                    p_src = Path(self.foto_perfil_path)
                    # Se não estiver dentro de media/usuarios, copia
                    if media_dir.resolve() not in p_src.resolve().parents:
                        import shutil
                        import time
                        # Timestamp para evitar cache ou conflito
                        ts = int(time.time())
                        ext = p_src.suffix or ".png"
                        new_name = f"user_{user_id}_{ts}{ext}"
                        dest_path = media_dir / new_name
                        shutil.copyfile(p_src, dest_path)
                        final_foto_path = str(dest_path)
                        # Atualiza a referência local (caminho absoluto para preview)
                        self.foto_perfil_path = final_foto_path
                    # No banco o caminho fica relativo à pasta de dados (portável)
                    final_foto_path = app_paths.to_storage_path(final_foto_path)

                self.on_update_profile(
                    user_id, 
                    final_foto_path,
                    telefone,
                    cref
                )
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao atualizar perfil do usuário: {e}")
                print(f"Erro ao atualizar perfil do usuário: {e}")

        self.selected_logo_path = None
        self._update_preview()
        show_toast(self, "Identidade visual e perfil salvos", 2500, kind="success")
