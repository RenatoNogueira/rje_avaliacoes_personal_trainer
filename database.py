import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional
import hashlib


class Database:
    """
    Classe responsável por gerenciar a conexão com o banco de dados SQLite
    e garantir que o esquema (tabelas e índices) seja criado na primeira execução.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """
        Inicializa o objeto de banco de dados.

        :param db_path: Caminho opcional para o arquivo .db.
                        Se não informado, será usado 'data/rje_avaliacoes.db'
                        relativo à pasta deste arquivo.
        """
        base_dir = Path(__file__).resolve().parent

        if db_path is None:
            data_dir = base_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "rje_avaliacoes.db"

        self.db_path: Path = db_path

        self._initialize_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """
        Cria e retorna uma nova conexão com o banco de dados.

        - Ativa FOREIGN KEY (por padrão o SQLite não ativa isso).
        - Define row_factory como sqlite3.Row para facilitar o acesso por nome de coluna.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _initialize_schema(self) -> None:
        """
        Cria todas as tabelas e índices necessários, caso ainda não existam.

        Esta função é idempotente: pode ser chamada múltiplas vezes sem problemas.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS alunos (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome                TEXT NOT NULL,
                    data_nascimento     TEXT,
                    telefone            TEXT,
                    email               TEXT,
                    objetivo            TEXT,
                    observacoes_medicas TEXT,
                    data_cadastro       TEXT NOT NULL DEFAULT (date('now'))
                );
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS agendamentos (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_aluno  INTEGER NOT NULL,
                    data      TEXT NOT NULL,
                    horario   TEXT NOT NULL,
                    tipo      TEXT NOT NULL CHECK (
                                  tipo IN ('Avaliação', 'Treino', 'Consultoria')
                              ),
                    status    TEXT NOT NULL CHECK (
                                  status IN ('Pendente', 'Concluído', 'Cancelado')
                              ),
                    FOREIGN KEY (id_aluno)
                        REFERENCES alunos (id)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                );
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS avaliacoes_fisicas (
                    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_aluno           INTEGER NOT NULL,
                    data               TEXT NOT NULL,
                    peso               REAL,
                    altura             REAL,
                    percentual_gordura REAL,
                    massa_magra        REAL,
                    dobras_cutaneas    TEXT,
                    perimetros         TEXT,
                    anamnese           TEXT,
                    FOREIGN KEY (id_aluno)
                        REFERENCES alunos (id)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                );
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS treinos (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_aluno       INTEGER NOT NULL,
                    data_criacao   TEXT NOT NULL DEFAULT (date('now')),
                    nome_do_treino TEXT NOT NULL,
                    objetivo       TEXT,
                    FOREIGN KEY (id_aluno)
                        REFERENCES alunos (id)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                );
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS exercicios_treino (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_treino      INTEGER NOT NULL,
                    nome_exercicio TEXT NOT NULL,
                    series         TEXT,
                    repeticoes     TEXT,
                    carga          TEXT,
                    descanso       TEXT,
                    observacoes    TEXT,
                    FOREIGN KEY (id_treino)
                        REFERENCES treinos (id)
                        ON DELETE CASCADE
                        ON UPDATE CASCADE
                );
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS exercicios_catalogo (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_json TEXT NOT NULL
                );
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS usuarios (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    username     TEXT NOT NULL UNIQUE,
                    senha_hash   TEXT NOT NULL,
                    nome         TEXT,
                    is_admin     INTEGER NOT NULL DEFAULT 0,
                    ativo        INTEGER NOT NULL DEFAULT 1,
                    data_criacao TEXT NOT NULL DEFAULT (datetime('now'))
                );
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_agendamentos_data
                    ON agendamentos (data);
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_agendamentos_id_aluno
                    ON agendamentos (id_aluno);
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_avaliacoes_id_aluno
                    ON avaliacoes_fisicas (id_aluno);
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_treinos_id_aluno
                    ON treinos (id_aluno);
                """
            )

            self._ensure_column(cursor, "alunos", "cpf", "TEXT")
            self._ensure_column(cursor, "alunos", "cep", "TEXT")
            self._ensure_column(cursor, "avaliacoes_fisicas", "historico_saude", "TEXT")
            self._ensure_column(cursor, "avaliacoes_fisicas", "estilo_vida", "TEXT")
            self._ensure_column(cursor, "avaliacoes_fisicas", "metas", "TEXT")
            self._ensure_column(cursor, "avaliacoes_fisicas", "postura", "TEXT")
            self._ensure_column(cursor, "avaliacoes_fisicas", "funcional_mobilidade", "TEXT")
            self._ensure_column(cursor, "avaliacoes_fisicas", "cardio", "TEXT")
            self._ensure_column(cursor, "avaliacoes_fisicas", "forca_resistencia", "TEXT")
            self._ensure_column(cursor, "avaliacoes_fisicas", "massa_gorda", "REAL")
            self._ensure_column(cursor, "avaliacoes_fisicas", "ldl", "REAL")
            self._ensure_column(cursor, "avaliacoes_fisicas", "hdl", "REAL")
            self._ensure_column(cursor, "avaliacoes_fisicas", "pressao_sistolica", "INTEGER")
            self._ensure_column(cursor, "avaliacoes_fisicas", "pressao_diastolica", "INTEGER")
            self._ensure_column(cursor, "avaliacoes_fisicas", "foto_frente", "TEXT")
            self._ensure_column(cursor, "avaliacoes_fisicas", "foto_costas", "TEXT")
            self._ensure_column(cursor, "avaliacoes_fisicas", "foto_lateral_dir", "TEXT")
            self._ensure_column(cursor, "avaliacoes_fisicas", "foto_lateral_esq", "TEXT")
            self._ensure_column(cursor, "usuarios", "cref", "TEXT")
            self._ensure_column(cursor, "agendamentos", "id_usuario_criacao", "INTEGER")
            self._ensure_column(cursor, "agendamentos", "id_usuario_atualizacao", "INTEGER")
            self._ensure_column(cursor, "avaliacoes_fisicas", "id_usuario_criacao", "INTEGER")
            self._ensure_column(cursor, "avaliacoes_fisicas", "id_usuario_atualizacao", "INTEGER")
            self._ensure_column(cursor, "treinos", "id_usuario_criacao", "INTEGER")
            self._ensure_column(cursor, "treinos", "id_usuario_atualizacao", "INTEGER")
            self._ensure_column(cursor, "exercicios_treino", "divisao", "TEXT DEFAULT 'A'")
            self._ensure_column(cursor, "usuarios", "is_trial", "INTEGER DEFAULT 0")
            
            # Atualizações para Alunos e Profissional (Fotos e Instagram/Telefone)
            self._ensure_column(cursor, "alunos", "foto_perfil", "TEXT")
            self._ensure_column(cursor, "alunos", "instagram", "TEXT")
            self._ensure_column(cursor, "usuarios", "foto_perfil", "TEXT")
            self._ensure_column(cursor, "usuarios", "telefone", "TEXT")
            self._ensure_column(cursor, "usuarios", "cidade", "TEXT")

            row = cursor.execute(
                "SELECT COUNT(*) AS total FROM exercicios_catalogo"
            ).fetchone()
            total = row["total"] if row is not None else 0
            if total == 0:
                self._populate_exercicios_catalogo(cursor)

            row = cursor.execute(
                "SELECT COUNT(*) AS total FROM usuarios"
            ).fetchone()
            total_usuarios = row["total"] if row is not None else 0
            if total_usuarios == 0:
                senha_hash = self.hash_password("admin")
                cursor.execute(
                    """
                    INSERT INTO usuarios (username, senha_hash, nome, is_admin, ativo)
                    VALUES (?, ?, ?, 1, 1)
                    """,
                    ("admin", senha_hash, "Administrador"),
                )

            conn.commit()

    def _ensure_column(self, cursor: sqlite3.Cursor, table: str, column: str, col_type: str) -> None:
        rows = cursor.execute(f"PRAGMA table_info({table})").fetchall()
        names = set()
        for r in rows:
            try:
                names.add(r["name"])
            except Exception:
                names.add(r[1])
        if column not in names:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type};")

    def _populate_exercicios_catalogo(self, cursor: sqlite3.Cursor) -> None:
        json_path = Path(__file__).resolve().parent / "exercises-ptbr-full-translation.json"

        if not json_path.exists():
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                items = json.load(f)
        except Exception:
            return

        if not isinstance(items, list):
            return

        for item in items:
            try:
                raw = json.dumps(item, ensure_ascii=False)
            except Exception:
                continue
            cursor.execute(
                """
                INSERT INTO exercicios_catalogo (raw_json)
                VALUES (?)
                """,
                (raw,),
            )

    def hash_password(self, password: str) -> str:
        data = password.encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    def execute(
        self,
        query: str,
        params: Optional[Iterable[Any]] = None,
        *,
        commit: bool = False,
    ) -> None:
        """
        Executa um comando SQL (INSERT, UPDATE, DELETE, DDL) sem retornar resultados.

        :param query: Comando SQL a ser executado.
        :param params: Parâmetros para o comando (tupla/lista), se houver.
        :param commit: Se True, executa conn.commit() ao final.
        """
        if params is None:
            params = ()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            if commit:
                conn.commit()

    def fetch_one(
        self,
        query: str,
        params: Optional[Iterable[Any]] = None,
    ) -> Optional[sqlite3.Row]:
        """
        Executa uma consulta SQL e retorna apenas uma linha (ou None).

        :param query: Comando SELECT.
        :param params: Parâmetros para o comando.
        :return: Um objeto sqlite3.Row ou None se não houver resultado.
        """
        if params is None:
            params = ()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            row = cursor.fetchone()
        return row

    def fetch_all(
        self,
        query: str,
        params: Optional[Iterable[Any]] = None,
    ) -> list[sqlite3.Row]:
        """
        Executa uma consulta SQL e retorna todas as linhas como lista.

        :param query: Comando SELECT.
        :param params: Parâmetros para o comando.
        :return: Lista de sqlite3.Row.
        """
        if params is None:
            params = ()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
        return list(rows)


db = Database()
