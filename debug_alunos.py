import sqlite3
from pathlib import Path

db_path = Path("data/rje_avaliacoes.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Schema of alunos:")
cursor.execute("PRAGMA table_info(alunos)")
for col in cursor.fetchall():
    print(col)

conn.close()
