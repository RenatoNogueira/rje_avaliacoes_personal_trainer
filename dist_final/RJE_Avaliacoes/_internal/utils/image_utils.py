from PIL import Image, ImageOps, ImageDraw

def create_circular_image(image_path: str, size: tuple[int, int]) -> Image.Image:
    """
    Carrega uma imagem, redimensiona (preenchendo o tamanho via crop central)
    e aplica uma máscara circular.
    """
    try:
        img = Image.open(image_path).convert("RGBA")
        
        # 1. Resize e Crop para preencher o quadrado (aspect fill)
        img = ImageOps.fit(img, size, centering=(0.5, 0.5))
        
        # 2. Criar máscara circular
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        
        # 3. Aplicar máscara
        output = Image.new("RGBA", size, (0, 0, 0, 0))
        output.paste(img, (0, 0), mask=mask)
        
        return output
    except Exception as e:
        print(f"Erro ao criar imagem circular: {e}")
        return None
