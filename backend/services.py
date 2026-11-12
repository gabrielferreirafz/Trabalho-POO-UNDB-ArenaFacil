"""Regras que coordenam usuários, arenas, quadras e agendamentos."""

from datetime import datetime, time

from backend import database as db
from backend.models import Agendamento, Arena, Cliente, DonoArena, Quadra, agora


class ErroNegocio(ValueError):
    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.status = status


def exigir(registro, mensagem="Registro não encontrado."):
    if registro is None:
        raise ErroNegocio(mensagem, 404)
    return registro


def perfil(usuario, esperado):
    if usuario.perfil() != esperado:
        raise ErroNegocio("Esta operação não está disponível para seu perfil.", 403)


def identificar(usuario_id):
    with db.conectar() as conn:
        dados = exigir(db.um(conn, "SELECT * FROM usuarios WHERE id = %s", (usuario_id,)), "Usuário não encontrado. Entre novamente.")
    classe = Cliente if dados.pop("perfil") == "CLIENTE" else DonoArena
    return classe(**dados)


def entrar(email):
    with db.conectar() as conn:
        return exigir(db.um(conn, "SELECT * FROM usuarios WHERE email = %s", (email,)), "E-mail não cadastrado.")


def cadastrar(dados, dono=False):
    with db.conectar() as conn:
        usuario = db.um(conn, "INSERT INTO usuarios (nome, email, perfil) VALUES (%s, %s, %s) RETURNING *",
                        (dados.nome, dados.email, "DONO" if dono else "CLIENTE"))
        if dono:
            conn.execute("INSERT INTO arenas (dono_id, nome, endereco, abertura, fechamento) VALUES (%s, %s, %s, %s, %s)",
                         (usuario["id"], dados.arena_nome, dados.endereco, dados.abertura, dados.fechamento))
        return usuario


def listar_arenas(nome=""):
    with db.conectar() as conn:
        # Busca literal por trecho do nome, sem interpretar % e _ como filtros.
        return db.todos(conn, "SELECT * FROM arenas WHERE strpos(lower(nome), lower(%s)) > 0 ORDER BY nome, id", (nome.strip(),))


def consultar_arena(arena_id):
    with db.conectar() as conn:
        return exigir(db.um(conn, "SELECT * FROM arenas WHERE id = %s", (arena_id,)))


def minha_arena(usuario):
    perfil(usuario, "DONO")
    with db.conectar() as conn:
        return exigir(db.um(conn, "SELECT * FROM arenas WHERE dono_id = %s", (usuario.id,)))


def listar_quadras(arena_id, incluir_inativas=False):
    consultar_arena(arena_id)
    with db.conectar() as conn:
        quadras = db.todos(conn, "SELECT * FROM quadras WHERE arena_id = %s AND (ativa OR %s) ORDER BY id", (arena_id, incluir_inativas))
        for quadra in quadras:
            quadra["modalidades"] = db.modalidades(conn, quadra["id"])
        return quadras


def quadra_do_dono(conn, quadra_id, usuario):
    perfil(usuario, "DONO")
    quadra = exigir(db.um(conn, "SELECT * FROM quadras WHERE id = %s FOR UPDATE", (quadra_id,)))
    arena = db.um(conn, "SELECT * FROM arenas WHERE id = %s", (quadra["arena_id"],))
    if arena["dono_id"] != usuario.id:
        raise ErroNegocio("Você só pode gerenciar quadras da sua arena.", 403)
    if not quadra["ativa"]:
        raise ErroNegocio("Esta quadra já foi desativada.")
    return quadra


def criar_quadra(usuario, dados):
    arena = minha_arena(usuario)
    with db.conectar() as conn:
        quadra = db.um(conn, "INSERT INTO quadras (arena_id, nome, descricao, preco_hora) VALUES (%s, %s, %s, %s) RETURNING *",
                       (arena["id"], dados.nome, dados.descricao, dados.preco_hora))
        db.salvar_modalidades(conn, quadra["id"], dados.modalidades)
        return {**quadra, "modalidades": dados.modalidades}


def editar_quadra(usuario, quadra_id, dados):
    with db.conectar() as conn:
        quadra_do_dono(conn, quadra_id, usuario)
        futuras = db.todos(conn, "SELECT modalidade FROM agendamentos WHERE quadra_id = %s AND status = 'CONFIRMADO' AND inicio > %s", (quadra_id, agora()))
        if any(reserva["modalidade"] not in dados.modalidades for reserva in futuras):
            raise ErroNegocio("Não é possível remover modalidade com reserva futura confirmada.", 409)
        quadra = db.um(conn, "UPDATE quadras SET nome = %s, descricao = %s, preco_hora = %s WHERE id = %s RETURNING *",
                       (dados.nome, dados.descricao, dados.preco_hora, quadra_id))
        db.salvar_modalidades(conn, quadra_id, dados.modalidades)
        return {**quadra, "modalidades": dados.modalidades}


def excluir_quadra(usuario, quadra_id):
    with db.conectar() as conn:
        quadra_do_dono(conn, quadra_id, usuario)
        futura = db.um(conn, "SELECT id FROM agendamentos WHERE quadra_id = %s AND status = 'CONFIRMADO' AND inicio > %s LIMIT 1", (quadra_id, agora()))
        if futura:
            raise ErroNegocio("Não é possível excluir quadra com reserva futura confirmada.", 409)
        historico = db.um(conn, "SELECT id FROM agendamentos WHERE quadra_id = %s LIMIT 1", (quadra_id,))
        if historico:
            conn.execute("UPDATE quadras SET ativa = FALSE WHERE id = %s", (quadra_id,))
            return {"mensagem": "Quadra desativada. O histórico foi preservado."}
        conn.execute("DELETE FROM quadras WHERE id = %s", (quadra_id,))
        return {"mensagem": "Quadra excluída."}


def disponibilidade(usuario, quadra_id, data, modalidade):
    perfil(usuario, "CLIENTE")
    with db.conectar() as conn:
        dados = exigir(db.um(conn, "SELECT * FROM quadras WHERE id = %s", (quadra_id,)))
        quadra = Quadra(**dados, modalidades=db.modalidades(conn, quadra_id))
        quadra.validar_reserva(modalidade)
        arena = Arena(**db.um(conn, "SELECT * FROM arenas WHERE id = %s", (quadra.arena_id,)))
        ocupados = db.todos(conn, "SELECT inicio FROM agendamentos WHERE status = 'CONFIRMADO' AND inicio::date = %s AND (quadra_id = %s OR cliente_id = %s)", (data, quadra_id, usuario.id))
        bloqueados = {r["inicio"] for r in ocupados}
        momento = agora()
        horarios = []
        for hora in range(24):
            inicio = datetime.combine(data, time(hora))
            if inicio > momento and arena.comporta(inicio) and inicio not in bloqueados:
                horarios.append(inicio.isoformat())
        return {"horarios": horarios, "preco_hora": quadra.preco_hora}


def reservar(usuario, dados):
    perfil(usuario, "CLIENTE")
    with db.conectar() as conn:
        # Todas as reservas do cliente e alterações da quadra passam por estes locks.
        # Os índices únicos também impedem conflitos entre requisições simultâneas.
        db.um(conn, "SELECT id FROM usuarios WHERE id = %s FOR UPDATE", (usuario.id,))
        registro = exigir(db.um(conn, "SELECT * FROM quadras WHERE id = %s FOR UPDATE", (dados.quadra_id,)))
        quadra = Quadra(**registro, modalidades=db.modalidades(conn, dados.quadra_id))
        quadra.validar_reserva(dados.modalidade)
        arena = Arena(**db.um(conn, "SELECT * FROM arenas WHERE id = %s", (quadra.arena_id,)))
        momento = agora()
        if dados.inicio <= momento:
            raise ErroNegocio("Escolha um horário futuro.")
        if dados.inicio.minute or dados.inicio.second or dados.inicio.microsecond:
            raise ErroNegocio("A reserva deve começar em hora cheia.")
        if not arena.comporta(dados.inicio):
            raise ErroNegocio("A reserva deve ficar inteiramente dentro do funcionamento da arena.")
        conflito = db.um(conn, "SELECT id FROM agendamentos WHERE status = 'CONFIRMADO' AND inicio = %s AND (quadra_id = %s OR cliente_id = %s)", (dados.inicio, dados.quadra_id, usuario.id))
        if conflito:
            raise ErroNegocio("Este horário já está ocupado para a quadra ou para você.", 409)
        return db.um(conn, "INSERT INTO agendamentos (cliente_id, quadra_id, modalidade, inicio, preco_reservado, criado_em) VALUES (%s, %s, %s, %s, %s, %s) RETURNING *",
                     (usuario.id, quadra.id, dados.modalidade, dados.inicio, quadra.preco_hora, momento))


def listar_reservas(usuario):
    with db.conectar() as conn:
        return db.todos(conn, """
            SELECT ag.*, q.nome AS quadra_nome, ar.nome AS arena_nome,
                   ar.endereco, u.nome AS cliente_nome
            FROM agendamentos ag JOIN quadras q ON q.id = ag.quadra_id
            JOIN arenas ar ON ar.id = q.arena_id JOIN usuarios u ON u.id = ag.cliente_id
            WHERE (%s = 'CLIENTE' AND ag.cliente_id = %s)
               OR (%s = 'DONO' AND ar.dono_id = %s)
            ORDER BY ag.inicio DESC, ag.id DESC
        """, (usuario.perfil(), usuario.id, usuario.perfil(), usuario.id))


def cancelar(usuario, reserva_id):
    perfil(usuario, "CLIENTE")
    with db.conectar() as conn:
        dados = exigir(db.um(conn, "SELECT * FROM agendamentos WHERE id = %s FOR UPDATE", (reserva_id,)))
        if dados["cliente_id"] != usuario.id:
            raise ErroNegocio("Você só pode cancelar suas próprias reservas.", 403)
        reserva = Agendamento(**dados)
        reserva.cancelar(usuario.id, agora())
        return db.um(conn, "UPDATE agendamentos SET status = %s, cancelado_em = %s WHERE id = %s RETURNING *",
                     (reserva.status, reserva.cancelado_em, reserva.id))
