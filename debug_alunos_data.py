import sqlite3
from pathlib import Path

db_path = Path("data/rje_avaliacoes.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Sample data_nascimento:")
cursor.execute("SELECT data_nascimento FROM alunos LIMIT 5")
for row in cursor.fetchall():
    print(row)

conn.close()
