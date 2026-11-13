"""Reservas, concorrência, cancelamentos e preservação de histórico."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend import database, services
from backend.main import app
from tests.test_quadras import api, cenario  # Fixtures compartilhadas sem arquivo adicional.


def reservar(api, cenario, inicio="2030-01-02T14:00:00", headers=None, quadra_id=None, modalidade="FUTEVOLEI"):
    return api.post("/api/agendamentos", headers=headers or cenario["cliente"], json={
        "quadra_id": quadra_id or cenario["quadra"]["id"], "modalidade": modalidade, "inicio": inicio})


def test_fluxo_completo_cancelar_libera_e_preserva(api, cenario):
    id = cenario["quadra"]["id"]
    consulta = f"/api/quadras/{id}/disponibilidade?data=2030-01-02&modalidade=FUTEVOLEI"
    assert "2030-01-02T14:00:00" in api.get(consulta, headers=cenario["cliente"]).json()["horarios"]
    resposta = reservar(api, cenario)
    assert resposta.status_code == 201
    reserva = resposta.json()
    assert reserva["status"] == "CONFIRMADO"
    assert "2030-01-02T14:00:00" not in api.get(consulta, headers=cenario["outro"]).json()["horarios"]
    assert len(api.get("/api/agendamentos", headers=cenario["dono"]).json()) == 1
    assert api.get("/api/agendamentos", headers=cenario["outro"]).json() == []
    assert api.post(f'/api/agendamentos/{reserva["id"]}/cancelar', headers=cenario["cliente"]).status_code == 200
    assert "2030-01-02T14:00:00" in api.get(consulta, headers=cenario["outro"]).json()["horarios"]
    assert reservar(api, cenario, headers=cenario["outro"]).status_code == 201
    assert api.get("/api/agendamentos", headers=cenario["cliente"]).json()[0]["status"] == "CANCELADO"


def test_conflitos_e_horas_consecutivas(api, cenario):
    assert reservar(api, cenario).status_code == 201
    assert reservar(api, cenario, headers=cenario["outro"]).status_code == 409
    segunda = api.post("/api/quadras", json=cenario["dados"], headers=cenario["dono"]).json()
    assert reservar(api, cenario, quadra_id=segunda["id"]).status_code == 409
    assert reservar(api, cenario, inicio="2030-01-02T15:00:00").status_code == 201
    consulta = f'/api/quadras/{segunda["id"]}/disponibilidade?data=2030-01-02&modalidade=FUTEVOLEI'
    assert "2030-01-02T14:00:00" not in api.get(consulta, headers=cenario["cliente"]).json()["horarios"]


@pytest.mark.parametrize("inicio", ["2029-12-31T14:00:00", "2030-01-01T08:00:00", "2030-01-02T14:30:00", "2030-01-02T14:00:01", "2030-01-02T14:00:00.000001", "2030-01-02T06:00:00", "2030-01-02T23:00:00"])
def test_horarios_invalidos(api, cenario, inicio):
    assert reservar(api, cenario, inicio=inicio).status_code == 400


def test_limites_funcionamento_e_offset(api, cenario):
    assert reservar(api, cenario, inicio="2030-01-02T07:00:00").status_code == 201
    assert reservar(api, cenario, inicio="2030-01-02T22:00:00").status_code == 201
    assert reservar(api, cenario, inicio="2030-01-02T17:00:00Z").json()["inicio"] == "2030-01-02T14:00:00"


@pytest.mark.parametrize("inicio,status", [("2030-01-01T10:00:00", 200), ("2030-01-01T09:00:00", 400)])
def test_limite_duas_horas(api, cenario, inicio, status):
    reserva = reservar(api, cenario, inicio=inicio).json()
    resposta = api.post(f'/api/agendamentos/{reserva["id"]}/cancelar', headers=cenario["cliente"])
    assert resposta.status_code == status


def test_cancelamento_propriedade_dono_e_repeticao(api, cenario):
    id = reservar(api, cenario).json()["id"]
    url = f"/api/agendamentos/{id}/cancelar"
    assert api.post(url, headers=cenario["outro"]).status_code == 403
    assert api.post(url, headers=cenario["dono"]).status_code == 403
    assert api.post(url, headers=cenario["cliente"]).status_code == 200
    assert api.post(url, headers=cenario["cliente"]).status_code == 400
    assert api.post("/api/agendamentos/999/cancelar", headers=cenario["cliente"]).status_code == 404


def test_edicao_preserva_modalidade_e_preco(api, cenario):
    assert reservar(api, cenario).status_code == 201
    id = cenario["quadra"]["id"]
    dados = {**cenario["dados"], "modalidades": ["VOLEI"]}
    assert api.put(f"/api/quadras/{id}", headers=cenario["dono"], json=dados).status_code == 409
    assert api.delete(f"/api/quadras/{id}", headers=cenario["dono"]).status_code == 409
    dados = {**cenario["dados"], "preco_hora": "180.00"}
    assert api.put(f"/api/quadras/{id}", headers=cenario["dono"], json=dados).status_code == 200
    preco = reservar(api, cenario, inicio="2030-01-02T15:00:00").json()["preco_reservado"]
    assert Decimal(str(preco)) == Decimal("180.00")
    historico = api.get("/api/agendamentos", headers=cenario["cliente"]).json()
    assert Decimal(str(historico[-1]["preco_reservado"])) == Decimal("100.00")


def test_desativacao_historico_e_quadra_inativa(api, cenario):
    reserva = reservar(api, cenario).json()
    api.post(f'/api/agendamentos/{reserva["id"]}/cancelar', headers=cenario["cliente"])
    id = cenario["quadra"]["id"]
    assert api.delete(f"/api/quadras/{id}", headers=cenario["dono"]).status_code == 200
    assert api.get(f'/api/arenas/{cenario["quadra"]["arena_id"]}/quadras').json() == []
    assert api.get("/api/dono/quadras", headers=cenario["dono"]).json()[0]["ativa"] is False
    assert reservar(api, cenario).status_code == 400
    assert api.put(f"/api/quadras/{id}", headers=cenario["dono"], json=cenario["dados"]).status_code == 400
    assert len(api.get("/api/agendamentos", headers=cenario["cliente"]).json()) == 1


def test_desativacao_com_reserva_passada(api, cenario, monkeypatch):
    reservar(api, cenario)
    monkeypatch.setattr(services, "agora", lambda: datetime(2030, 1, 3, 8))
    assert api.delete(f'/api/quadras/{cenario["quadra"]["id"]}', headers=cenario["dono"]).status_code == 200
    assert api.get("/api/agendamentos", headers=cenario["cliente"]).json()[0]["status"] == "CONFIRMADO"


def test_modalidade_e_perfil_na_reserva(api, cenario):
    assert reservar(api, cenario, modalidade="BEACH_TENIS").status_code == 400
    assert reservar(api, cenario, headers=cenario["dono"]).status_code == 403
    assert reservar(api, cenario, quadra_id=999).status_code == 404


def test_conflito_entre_arenas_e_visibilidade_do_dono(api, cenario):
    dono = api.post("/api/donos", json={"nome": "Segundo dono", "email": "segundo@teste.com", "arena_nome": "Arena Lua", "endereco": "Rua 2", "abertura": "07:00", "fechamento": "23:00"}).json()
    headers = {"X-Usuario-Id": str(dono["id"])}
    quadra = api.post("/api/quadras", json=cenario["dados"], headers=headers).json()
    assert reservar(api, cenario).status_code == 201
    assert reservar(api, cenario, quadra_id=quadra["id"]).status_code == 409
    assert api.get("/api/agendamentos", headers=headers).json() == []
    assert reservar(api, cenario, quadra_id=quadra["id"], headers=cenario["outro"]).status_code == 201
    assert len(api.get("/api/agendamentos", headers=headers).json()) == 1
    assert len(api.get("/api/agendamentos", headers=cenario["dono"]).json()) == 1


@pytest.mark.parametrize("operacao", ["editar", "excluir"])
def test_reserva_simultanea_com_alteracao_quadra(api, cenario, operacao):
    id = cenario["quadra"]["id"]
    def executar(acao):
        with TestClient(app) as cliente:
            if acao == "reservar":
                return reservar(cliente, cenario).status_code
            if operacao == "excluir":
                return cliente.delete(f"/api/quadras/{id}", headers=cenario["dono"]).status_code
            dados = {**cenario["dados"], "modalidades": ["VOLEI"]}
            return cliente.put(f"/api/quadras/{id}", headers=cenario["dono"], json=dados).status_code
    with ThreadPoolExecutor(max_workers=2) as executor:
        reserva, alteracao = list(executor.map(executar, ["reservar", "alterar"]))
    assert (reserva, alteracao) in [(201, 409), (400, 200), (404, 200)]
    # Não pode existir reserva futura confirmada para quadra removida ou modalidade retirada.
    with database.conectar() as conn:
        invalidas = database.um(conn, """SELECT count(*) AS total FROM agendamentos ag
            JOIN quadras q ON q.id = ag.quadra_id
            LEFT JOIN quadra_modalidades qm ON qm.quadra_id = q.id AND qm.modalidade = ag.modalidade
            WHERE ag.status = 'CONFIRMADO' AND (NOT q.ativa OR qm.modalidade IS NULL)""")
        assert invalidas["total"] == 0


@pytest.mark.parametrize("mesmo_cliente", [False, True])
def test_duas_requisicoes_simultaneas(api, cenario, mesmo_cliente):
    segunda = api.post("/api/quadras", json=cenario["dados"], headers=cenario["dono"]).json()
    def tentar(indice):
        with TestClient(app) as cliente:
            return reservar(cliente, cenario,
                            headers=cenario["cliente"] if mesmo_cliente or indice == 0 else cenario["outro"],
                            quadra_id=segunda["id"] if mesmo_cliente and indice == 1 else cenario["quadra"]["id"]).status_code
    with ThreadPoolExecutor(max_workers=2) as executor:
        respostas = list(executor.map(tentar, [0, 1]))
    assert sorted(respostas) == [201, 409]


def test_persistencia_apos_reabrir_api(api, cenario):
    reserva = reservar(api, cenario).json()
    with TestClient(app) as reiniciada:
        historico = reiniciada.get("/api/agendamentos", headers=cenario["cliente"]).json()
    assert historico[0]["id"] == reserva["id"]


def test_indices_protegem_banco(api, cenario):
    import psycopg
    reservar(api, cenario)
    segunda = api.post("/api/quadras", json=cenario["dados"], headers=cenario["dono"]).json()
    tentativas = [
        (int(cenario["outro"]["X-Usuario-Id"]), cenario["quadra"]["id"], "uq_quadra_horario_confirmado"),
        (int(cenario["cliente"]["X-Usuario-Id"]), segunda["id"], "uq_cliente_horario_confirmado"),
    ]
    for cliente_id, quadra_id, indice in tentativas:
        with pytest.raises(psycopg.errors.UniqueViolation) as erro:
            with database.conectar() as conn:
                conn.execute("""INSERT INTO agendamentos
                    (cliente_id, quadra_id, modalidade, inicio, preco_reservado, criado_em)
                    VALUES (%s, %s, 'FUTEVOLEI', '2030-01-02 14:00', 100, '2030-01-01 08:00')""", (cliente_id, quadra_id))
        assert erro.value.diag.constraint_name == indice
