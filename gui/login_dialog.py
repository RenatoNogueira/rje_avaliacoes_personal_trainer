import customtkinter as ctk
from PIL import Image
from pathlib import Path
from database import db

class LoginDialog(ctk.CTkToplevel):
    def __init__(self, master, on_login_success, on_cancel):
        super().__init__(master)
        
        self.on_login_success = on_login_success
        self.on_cancel = on_cancel
        
        self.title("RJE Avaliações - Login")
        self.geometry("700x450")
        self.resizable(False, False)
        
        # Centralizar na tela
        # self.eval('tk::PlaceWindow . center') # Alternativa simples, mas vamos fazer cálculo manual se precisar
        
        # Configuração da Janela Modal
        self.transient(master)
        self.grab_set()
        self.focus_force()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Layout Principal (2 Colunas)
        self.grid_columnconfigure(0, weight=1) # Lado Esquerdo (Branding)
        self.grid_columnconfigure(1, weight=1) # Lado Direito (Form)
        self.grid_rowconfigure(0, weight=1)

        # --- Lado Esquerdo: Branding ---
        self.left_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray90", "#1a1a1a"))
        self.left_frame.grid(row=0, column=0, sticky="nsew")
        self.left_frame.grid_columnconfigure(0, weight=1)
        self.left_frame.grid_rowconfigure((0, 4), weight=1) # Espaçadores verticais

        # Logo / Imagem
        # Tenta pegar logo das configurações se existir
        logo_path = getattr(master, "logo_path", None)
        logo_image = None
        
        if logo_path and Path(logo_path).exists():
            try:
                pil_img = Image.open(logo_path)
                logo_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(150, 150))
                
                # Define ícone da janela também
                if logo_path.lower().endswith(".ico"):
                    self.iconbitmap(logo_path)
                else:
                    from PIL import ImageTk
                    icon_photo = ImageTk.PhotoImage(pil_img)
                    self.wm_iconphoto(False, icon_photo)
                    self._icon_ref = icon_photo # Manter referência
            except:
                pass
        
        # Se não tiver logo personalizada, poderíamos usar uma padrão ou ícone
        
        if logo_image:
            ctk.CTkLabel(self.left_frame, text="", image=logo_image).grid(row=1, column=0, pady=(0, 20))
        else:
            # Placeholder se não tiver imagem
            ctk.CTkLabel(self.left_frame, text="🏋️", font=ctk.CTkFont(size=80)).grid(row=1, column=0, pady=(0, 20))

        ctk.CTkLabel(
            self.left_frame, 
            text="RJE Avaliações", 
            font=ctk.CTkFont(family="Helvetica", size=26, weight="bold")
        ).grid(row=2, column=0, padx=20)
        
        ctk.CTkLabel(
            self.left_frame, 
            text="Sistema de Gestão para Personal Trainers", 
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).grid(row=3, column=0, padx=20, pady=(5, 0))


        # --- Lado Direito: Login Form ---
        self.right_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=("white", "#2b2b2b"))
        self.right_frame.grid(row=0, column=1, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure((0, 6), weight=1) # Centralizar verticalmente

        # Título Form
        ctk.CTkLabel(
            self.right_frame, 
            text="Bem-vindo!", 
            font=ctk.CTkFont(size=24, weight="bold")
        ).grid(row=1, column=0, padx=40, pady=(0, 5), sticky="w")
        
        ctk.CTkLabel(
            self.right_frame, 
            text="Faça login para continuar", 
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).grid(row=2, column=0, padx=40, pady=(0, 30), sticky="w")

        # Inputs
        self.entry_user = ctk.CTkEntry(
            self.right_frame, 
            placeholder_text="Usuário",
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.entry_user.grid(row=3, column=0, padx=40, pady=(0, 15), sticky="ew")
        
        self.entry_pass = ctk.CTkEntry(
            self.right_frame, 
            placeholder_text="Senha", 
            show="*",
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.entry_pass.grid(row=4, column=0, padx=40, pady=(0, 10), sticky="ew")

        # Error Label
        self.lbl_error = ctk.CTkLabel(
            self.right_frame, 
            text="", 
            text_color="#e74c3c", 
            font=ctk.CTkFont(size=12)
        )
        self.lbl_error.grid(row=5, column=0, padx=40, pady=(0, 10), sticky="w")

        # Botão Entrar
        self.btn_login = ctk.CTkButton(
            self.right_frame,
            text="ENTRAR",
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._attempt_login,
            fg_color="#2ecc71",
            hover_color="#27ae60"
        )
        self.btn_login.grid(row=6, column=0, padx=40, pady=(10, 40), sticky="ew")

        # Bind Enter key
        self.entry_user.bind("<Return>", lambda e: self.entry_pass.focus())
        self.entry_pass.bind("<Return>", lambda e: self.btn_login.invoke())
        
        # Focus inicial
        self.entry_user.focus_set()

    def _attempt_login(self):
        usuario = self.entry_user.get().strip()
        senha = self.entry_pass.get()
        
        if not usuario or not senha:
            self._show_error("Por favor, preencha todos os campos.")
            return

        row = db.fetch_one(
            """
            SELECT id, username, senha_hash, nome, is_admin, ativo, is_trial, data_criacao, foto_perfil, telefone
            FROM usuarios
            WHERE lower(username) = lower(?)
            """,
            (usuario,),
        )
        
        if row is None or not row["ativo"]:
            self._show_error("Usuário não encontrado ou inativo.")
            return
            
        senha_hash = db.hash_password(senha)
        if senha_hash != row["senha_hash"]:
            self._show_error("Senha incorreta.")
            return

        # Verificação de Trial (30 dias)
        if row["is_trial"]:
            try:
                from datetime import datetime
                criacao_str = row["data_criacao"]
                # Tenta formatos comuns
                dt_format = "%Y-%m-%d %H:%M:%S" if " " in criacao_str else "%Y-%m-%d"
                criacao_dt = datetime.strptime(criacao_str, dt_format)
                
                delta = datetime.now() - criacao_dt
                if delta.days > 30:
                    self._show_error("Período de teste (30 dias) expirado.\nContate o administrador.")
                    return
            except Exception:
                pass # Se der erro na data, permite login (fallback)
            
        # Sucesso
        user_data = {
            "id": row["id"],
            "username": row["username"],
            "nome": row["nome"],
            "is_admin": bool(row["is_admin"]),
            "foto_perfil": row["foto_perfil"],
            "telefone": row["telefone"],
        }
        try:
            self.on_login_success(user_data)
        except Exception as e:
            print(f"Erro no callback de login: {e}")
            pass
        self.destroy()

    def _show_error(self, msg):
        self.lbl_error.configure(text=msg)
        # Animação de "shake" simples ou apenas cor (opcional, por enquanto só texto)

    def _on_close(self):
        try:
            self.on_cancel()
        except Exception:
            pass
            
        try:
            self.destroy()
        except Exception:
            pass
