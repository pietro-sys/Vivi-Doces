"""Conexão com o SQLite e criação/atualização do banco.

Regra de ouro: este módulo NUNCA apaga dados. Banco novo recebe o schema e o
catálogo inicial; banco existente é atualizado por migrações incrementais,
controladas pelo número em PRAGMA user_version.
"""
import sqlite3
from pathlib import Path

from flask import current_app, g

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_VERSION = 1


def get_db():
    """Uma conexão por requisição, fechada automaticamente no fim."""
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")  # o SQLite não ativa isso sozinho
        g.db = conn
    return g.db


def close_db(_erro=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()  # o que não recebeu commit é descartado


# --------------------------------------------------------------------------
# Migrações
# --------------------------------------------------------------------------

def _colunas(conn, tabela):
    return {linha[1] for linha in conn.execute(f"PRAGMA table_info({tabela})")}


def _adicionar_coluna(conn, tabela, coluna, definicao):
    if coluna not in _colunas(conn, tabela):
        conn.execute(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}")


def _migrar_para_1(conn):
    """Banco original (clientes/produtos/vendas) -> versão 1."""
    _adicionar_coluna(conn, "clientes", "email", "TEXT")
    _adicionar_coluna(conn, "clientes", "observacoes", "TEXT")
    _adicionar_coluna(conn, "produtos", "unidade_venda", "TEXT NOT NULL DEFAULT 'unidade'")
    _adicionar_coluna(conn, "produtos", "imagem", "TEXT")
    _adicionar_coluna(conn, "produtos", "ativo", "INTEGER NOT NULL DEFAULT 1")
    _adicionar_coluna(conn, "vendas", "data_entrega", "DATE")
    _adicionar_coluna(conn, "vendas", "observacoes", "TEXT")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS itens_venda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER NOT NULL,
            produto_id INTEGER,
            descricao TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario DECIMAL(10,2) NOT NULL,
            custo_unitario DECIMAL(10,2) NOT NULL DEFAULT 0,
            FOREIGN KEY (venda_id) REFERENCES vendas(id) ON DELETE CASCADE,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vendas_cliente ON vendas(cliente_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vendas_status ON vendas(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_itens_venda ON itens_venda(venda_id)")

    # Ajustes de dados do catálogo antigo
    conn.execute("UPDATE produtos SET unidade_venda = 'cento' WHERE nome LIKE 'Cento%'")
    conn.execute("UPDATE produtos SET unidade_venda = 'kit' WHERE nome LIKE 'Kit%'")
    conn.execute("UPDATE produtos SET categoria = 'Doces Individuais' "
                 "WHERE categoria = 'Lotes Individuais'")

    # Coluna que ninguém atualizava (agora o total vem das vendas).
    # DROP COLUMN exige SQLite 3.35+; se não houver, a coluna só fica sem uso.
    try:
        conn.execute("ALTER TABLE clientes DROP COLUMN total_pedidos")
    except sqlite3.OperationalError:
        pass


MIGRACOES = {1: _migrar_para_1}


def init_db(caminho):
    """Cria o banco se não existir; senão, aplica só as migrações pendentes."""
    conn = sqlite3.connect(caminho, isolation_level=None)  # transações manuais
    try:
        existe = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'produtos'"
        ).fetchone()

        if not existe:
            schema = (BASE_DIR / "database.sql").read_text(encoding="utf-8")
            seed = (BASE_DIR / "seed.sql").read_text(encoding="utf-8")
            conn.executescript(
                f"BEGIN;\n{schema}\n{seed}\nPRAGMA user_version = {SCHEMA_VERSION};\nCOMMIT;"
            )
            return

        versao = conn.execute("PRAGMA user_version").fetchone()[0]
        for destino in range(versao + 1, SCHEMA_VERSION + 1):
            conn.execute("BEGIN")
            try:
                MIGRACOES[destino](conn)
                conn.execute(f"PRAGMA user_version = {destino}")
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
    finally:
        conn.close()
