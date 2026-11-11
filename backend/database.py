"""Conexão e pequenas operações de persistência com SQL direto."""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()


def conectar():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("Defina DATABASE_URL no arquivo .env antes de iniciar.")
    # O contexto da conexão confirma a transação ou desfaz tudo em caso de erro.
    return psycopg.connect(url, row_factory=dict_row)


def preparar_banco():
    sql = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"
    with conectar() as conn:
        conn.execute(sql.read_text(encoding="utf-8"), prepare=False)


def um(conn, sql, parametros=()):
    return conn.execute(sql, parametros).fetchone()


def todos(conn, sql, parametros=()):
    return conn.execute(sql, parametros).fetchall()


def modalidades(conn, quadra_id):
    linhas = todos(conn, "SELECT modalidade FROM quadra_modalidades WHERE quadra_id = %s ORDER BY modalidade", (quadra_id,))
    return [linha["modalidade"] for linha in linhas]


def salvar_modalidades(conn, quadra_id, valores):
    conn.execute("DELETE FROM quadra_modalidades WHERE quadra_id = %s", (quadra_id,))
    for valor in valores:
        conn.execute("INSERT INTO quadra_modalidades VALUES (%s, %s)", (quadra_id, valor))
