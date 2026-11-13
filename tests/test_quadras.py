"""Testes HTTP com PostgreSQL real. O banco de testes é limpo a cada caso."""

import os
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from psycopg.conninfo import conninfo_to_dict

from backend import database, services
from backend.main import app


@pytest.fixture
def api(monkeypatch):
    url = os.getenv("ARENA_TEST_DATABASE_URL")
    if not url:
        pytest.fail("Defina ARENA_TEST_DATABASE_URL para um banco exclusivo de testes.")
    nome = conninfo_to_dict(url).get("dbname", "")
    if not nome.endswith("_test"):
        pytest.fail("Por segurança, o nome do banco deve terminar em _test.")
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setattr(services, "agora", lambda: datetime(2030, 1, 1, 8))
    with TestClient(app) as cliente:
        with database.conectar() as conn:
            conn.execute("TRUNCATE agendamentos, quadra_modalidades, quadras, arenas, usuarios RESTART IDENTITY CASCADE")
        yield cliente


@pytest.fixture
def cenario(api):
    dono = api.post("/api/donos", json={"nome": "Dono", "email": "dono@teste.com", "arena_nome": "Arena Sol", "endereco": "Rua da Areia, 10", "abertura": "07:00", "fechamento": "23:00"})
    assert dono.status_code == 201
    cliente = api.post("/api/clientes", json={"nome": "Cliente", "email": "cliente@teste.com"}).json()
    outro = api.post("/api/clientes", json={"nome": "Outro", "email": "outro@teste.com"}).json()
    hd = {"X-Usuario-Id": str(dono.json()["id"])}
    hc = {"X-Usuario-Id": str(cliente["id"])}
    ho = {"X-Usuario-Id": str(outro["id"])}
    dados = {"nome": "Quadra Sol", "descricao": "Areia", "preco_hora": "100.00", "modalidades": ["FUTEVOLEI", "VOLEI"]}
    quadra = api.post("/api/quadras", json=dados, headers=hd)
    assert quadra.status_code == 201
    return {"dono": hd, "cliente": hc, "outro": ho, "quadra": quadra.json(), "dados": dados}


def test_cadastro_entrada_email_unico_e_arena(api, cenario):
    entrada = api.post("/api/entrada", json={"email": " DONO@TESTE.COM "})
    assert entrada.json()["perfil"] == "DONO"
    assert api.post("/api/clientes", json={"nome": "Duplicado", "email": "Dono@teste.com"}).status_code == 409
    assert api.post("/api/entrada", json={"email": "ausente@teste.com"}).status_code == 404
    assert len(api.get("/api/arenas").json()) == 1
    assert api.get("/api/dono/arena", headers=cenario["dono"]).json()["nome"] == "Arena Sol"
    with database.conectar() as conn:
        assert database.um(conn, "SELECT count(*) AS total FROM usuarios WHERE perfil='DONO'")["total"] == 1


def test_busca_apenas_nome_e_literal(api, cenario):
    assert len(api.get("/api/arenas", params={"nome": "SOL"}).json()) == 1
    assert api.get("/api/arenas", params={"nome": "Rua da Areia"}).json() == []
    assert api.get("/api/arenas", params={"nome": "%"}).json() == []
    assert api.get("/api/arenas/999").status_code == 404


@pytest.mark.parametrize("campo,valor", [("abertura", "23:00"), ("fechamento", "06:00"), ("email", "sem-email"), ("nome", " ")])
def test_cadastro_invalido_nao_cria_dono(api, campo, valor):
    dados = {"nome": "Dono", "email": "dono@teste.com", "arena_nome": "Arena", "endereco": "Rua 1", "abertura": "07:00", "fechamento": "23:00"}
    dados[campo] = valor
    assert api.post("/api/donos", json=dados).status_code == 422
    assert api.get("/api/arenas").json() == []
    with database.conectar() as conn:
        assert database.um(conn, "SELECT count(*) AS total FROM usuarios")["total"] == 0


@pytest.mark.parametrize("alteracao", [{"modalidades": []}, {"modalidades": ["FUTEBOL"]}, {"preco_hora": "0"}, {"preco_hora": "1.123"}, {"nome": " "}, {"ativa": False}])
def test_validacao_quadra(api, cenario, alteracao):
    dados = {**cenario["dados"], **alteracao}
    assert api.post("/api/quadras", headers=cenario["dono"], json=dados).status_code == 422


def test_editar_e_excluir_sem_historico(api, cenario):
    id = cenario["quadra"]["id"]
    dados = {**cenario["dados"], "nome": "Quadra Lua", "preco_hora": "120.00", "modalidades": ["BEACH_TENIS"]}
    resposta = api.put(f"/api/quadras/{id}", headers=cenario["dono"], json=dados)
    assert resposta.status_code == 200
    assert resposta.json()["modalidades"] == ["BEACH_TENIS"]
    assert api.delete(f"/api/quadras/{id}", headers=cenario["dono"]).status_code == 200
    assert api.get("/api/dono/quadras", headers=cenario["dono"]).json() == []


def test_propriedade_e_perfis(api, cenario):
    id = cenario["quadra"]["id"]
    outro_dono = api.post("/api/donos", json={"nome": "Outro dono", "email": "dono2@teste.com", "arena_nome": "Outra", "endereco": "Rua 2", "abertura": "08:00", "fechamento": "22:00"}).json()
    headers = {"X-Usuario-Id": str(outro_dono["id"])}
    assert api.put(f"/api/quadras/{id}", json=cenario["dados"], headers=headers).status_code == 403
    assert api.delete(f"/api/quadras/{id}", headers=headers).status_code == 403
    assert api.post("/api/quadras", json=cenario["dados"], headers=cenario["cliente"]).status_code == 403
    assert api.get("/api/dono/quadras", headers=cenario["cliente"]).status_code == 403
    assert api.get("/api/agendamentos").status_code == 422
    assert api.get("/api/agendamentos", headers={"X-Usuario-Id": "99999"}).status_code == 404


def test_interface_e_saude(api):
    assert api.get("/api/saude").json() == {"status": "ok"}
    assert 'lang="pt-BR"' in api.get("/").text
    assert api.get("/static/style.css").status_code == 200
    assert api.get("/static/script.js").status_code == 200


def test_segunda_arena_bloqueada_no_banco(api, cenario):
    import psycopg
    with pytest.raises(psycopg.errors.UniqueViolation):
        with database.conectar() as conn:
            conn.execute("INSERT INTO arenas (dono_id, nome, endereco, abertura, fechamento) VALUES (%s, 'Outra', 'Rua', '07:00', '22:00')", (int(cenario["dono"]["X-Usuario-Id"]),))
