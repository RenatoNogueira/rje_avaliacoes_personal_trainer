from pathlib import Path
from tkinter import filedialog, messagebox
from PIL import Image

import customtkinter as ctk
from .utils import setup_enter_navigation
from .input_masks import bind_mask


class ProfissionalView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        professor_var: ctk.StringVar,
        marca_var: ctk.StringVar,
        email_var: ctk.StringVar,
        telefone_var: ctk.StringVar,
        get_logo_path,
        set_branding,
    ) -> None:
        super().__init__(master)
        self.professor_var = professor_var
        self.marca_var = marca_var
        self.email_var = email_var
        self.telefone_var = telefone_var
        self.get_logo_path = get_logo_path
        self.set_branding = set_branding
        self.selected_logo_path: str | None = None

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
            text_color="gray"
        ).grid(row=0, column=0, padx=20, pady=(20, 10))

        # Card Container
        self.card_frame = ctk.CTkFrame(self.left_panel, fg_color=("gray90", "gray20"), corner_radius=10)
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

        # Professor Name Preview
        self.lbl_prof_preview = ctk.CTkLabel(
            self.card_frame,
            textvariable=self.professor_var,
            font=ctk.CTkFont(size=14)
        )
        self.lbl_prof_preview.grid(row=2, column=0, padx=10, pady=(0, 20))

        # Contact Info Preview
        self.contact_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.contact_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.contact_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.contact_frame, text="📧").grid(row=0, column=0, padx=(0, 5), sticky="e")
        ctk.CTkLabel(self.contact_frame, textvariable=self.email_var, anchor="w").grid(row=0, column=1, sticky="ew")
        
        ctk.CTkLabel(self.contact_frame, text="📞").grid(row=1, column=0, padx=(0, 5), sticky="e")
        ctk.CTkLabel(self.contact_frame, textvariable=self.telefone_var, anchor="w").grid(row=1, column=1, sticky="ew")

        # Reload Preview Button
        ctk.CTkButton(
            self.left_panel,
            text="Atualizar Visualização",
            command=self._update_preview,
            fg_color="transparent",
            border_width=1
        ).grid(row=3, column=0, padx=20, pady=20)


        # --- Right Panel: Edit Form ---
        self.right_panel = ctk.CTkFrame(self, corner_radius=15)
        self.right_panel.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1) # Scrollable area expands

        title_lbl = ctk.CTkLabel(
            self.right_panel,
            text="Editar Informações",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_lbl.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Scrollable Form Area
        self.scroll_form = ctk.CTkScrollableFrame(self.right_panel, fg_color="transparent")
        self.scroll_form.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.scroll_form.grid_columnconfigure(0, weight=1)

        # Form Container (dentro do scroll)
        self.form_container = ctk.CTkFrame(self.scroll_form, fg_color="transparent")
        self.form_container.grid(row=0, column=0, padx=10, sticky="ew")
        self.form_container.grid_columnconfigure(1, weight=1)

        row = 0
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
        
        # Logo Selection
        row += 1
        ctk.CTkLabel(self.form_container, text="Logo (PNG):", font=ctk.CTkFont(weight="bold")).grid(
            row=row, column=0, padx=10, pady=(20, 5), sticky="nw"
        )
        
        logo_controls = ctk.CTkFrame(self.form_container, fg_color="transparent")
        logo_controls.grid(row=row, column=1, padx=10, pady=(20, 5), sticky="ew")
        logo_controls.grid_columnconfigure(0, weight=1)

        self.entry_logo = ctk.CTkEntry(logo_controls, placeholder_text="Caminho do arquivo...")
        self.entry_logo.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        current_logo = self.get_logo_path()
        if current_logo:
            self.entry_logo.insert(0, current_logo)

        ctk.CTkButton(
            logo_controls, 
            text="📁 Escolher", 
            width=80,
            command=self.on_escolher_logo
        ).grid(row=0, column=1)

        # Save Button Area (Footer fixo no right_panel)
        self.btn_salvar = ctk.CTkButton(
            self.right_panel,
            text="Salvar Alterações",
            command=self.on_salvar,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
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
                # Resize for preview (max 100x100)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(100, 100))
                self.logo_preview.configure(image=ctk_img, text="")
            except Exception:
                self.logo_preview.configure(image=None, text="[Erro Imagem]")
        else:
            self.logo_preview.configure(image=None, text="[Sem Logo]")

    def on_escolher_logo(self) -> None:
        file_path = filedialog.askopenfilename(
            filetypes=[("Imagens PNG", "*.png"), ("Todos os arquivos", "*.*")],
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
                base_dir = Path(__file__).resolve().parent.parent
                branding_dir = base_dir / "data" / "branding"
                branding_dir.mkdir(parents=True, exist_ok=True)
                logo_target_path = branding_dir / "logo.png"
                
                # Only copy if the source is different from destination
                if Path(logo_input).resolve() != logo_target_path.resolve():
                    from shutil import copyfile
                    copyfile(logo_input, logo_target_path)
                
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
        
        self.set_branding(logo_target, marca, email, telefone)
        messagebox.showinfo("Sucesso", "Identidade visual salva com sucesso.")
