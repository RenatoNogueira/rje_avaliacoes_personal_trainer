import sqlite3
import os
from pathlib import Path

db_path = Path("data/rje_avaliacoes.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Schema of avaliacoes_fisicas:")
cursor.execute("PRAGMA table_info(avaliacoes_fisicas)")
for col in cursor.fetchall():
    print(col)

print("\nLast 5 records (id, id_aluno, foto_frente):")
cursor.execute("SELECT id, id_aluno, foto_frente FROM avaliacoes_fisicas ORDER BY id DESC LIMIT 5")
for row in cursor.fetchall():
    print(row)

conn.close()
