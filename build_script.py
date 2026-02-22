import subprocess
import sys

def build_executable():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=RJE_Avaliacoes_v1.0.12",
        "--add-data=data;data",
        "--add-data=media;media", 
        "--add-data=.env;.",
        "main.py"
    ]
    
    print("Executando build...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Build concluído com sucesso!")
        print(result.stdout)
    else:
        print("Erro no build:")
        print(result.stderr)
        print(result.stdout)

if __name__ == "__main__":
    build_executable()