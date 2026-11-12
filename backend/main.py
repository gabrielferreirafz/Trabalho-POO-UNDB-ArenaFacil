"""Entrada HTTP e integração entre a interface, serviços e banco."""

from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from psycopg.errors import UniqueViolation

from backend import database, schemas, services
from backend.models import Modalidade


@asynccontextmanager
async def lifespan(app):
    database.preparar_banco()
    yield


app = FastAPI(title="Arena Fácil", version="1.0.0", lifespan=lifespan)
FRONTEND = Path(__file__).resolve().parents[1] / "frontend"


def usuario_atual(x_usuario_id: int = Header(gt=0)):
    # Identificação acadêmica: este cabeçalho não é autenticação segura.
    return services.identificar(x_usuario_id)


@app.exception_handler(ValueError)
async def erro_negocio(request, erro):
    return JSONResponse(status_code=getattr(erro, "status", 400), content={"detail": str(erro)})


@app.exception_handler(UniqueViolation)
async def duplicidade(request, erro):
    indice = erro.diag.constraint_name
    mensagem = "Este e-mail já está cadastrado." if indice == "usuarios_email_key" else "O horário foi ocupado por outra reserva. Escolha outro."
    return JSONResponse(status_code=409, content={"detail": mensagem})


@app.exception_handler(RequestValidationError)
async def entrada_invalida(request, erro):
    mensagens = []
    for item in erro.errors():
        campo = str(item["loc"][-1])
        mensagem = item.get("ctx", {}).get("error")
        mensagens.append(str(mensagem) if mensagem else f"Verifique o campo {campo}.")
    return JSONResponse(status_code=422, content={"detail": " ".join(mensagens)})


@app.get("/api/saude")
def saude():
    with database.conectar() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.post("/api/clientes", status_code=201)
def cadastrar_cliente(dados: schemas.CadastroCliente):
    return services.cadastrar(dados)


@app.post("/api/donos", status_code=201)
def cadastrar_dono(dados: schemas.CadastroDono):
    return services.cadastrar(dados, dono=True)


@app.post("/api/entrada")
def entrar(dados: schemas.Email):
    return services.entrar(dados.email)


@app.get("/api/usuarios/eu")
def eu(usuario=Depends(usuario_atual)):
    return {"id": usuario.id, "nome": usuario.nome, "email": usuario.email, "perfil": usuario.perfil()}


@app.get("/api/arenas")
def arenas(nome: str = ""):
    return services.listar_arenas(nome)


@app.get("/api/dono/arena")
def arena_do_dono(usuario=Depends(usuario_atual)):
    return services.minha_arena(usuario)


@app.get("/api/dono/quadras")
def quadras_do_dono(usuario=Depends(usuario_atual)):
    arena = services.minha_arena(usuario)
    return services.listar_quadras(arena["id"], incluir_inativas=True)


@app.get("/api/arenas/{arena_id}")
def arena(arena_id: int):
    return services.consultar_arena(arena_id)


@app.get("/api/arenas/{arena_id}/quadras")
def quadras(arena_id: int):
    return services.listar_quadras(arena_id)


@app.post("/api/quadras", status_code=201)
def criar_quadra(dados: schemas.DadosQuadra, usuario=Depends(usuario_atual)):
    return services.criar_quadra(usuario, dados)


@app.put("/api/quadras/{quadra_id}")
def editar_quadra(quadra_id: int, dados: schemas.DadosQuadra, usuario=Depends(usuario_atual)):
    return services.editar_quadra(usuario, quadra_id, dados)


@app.delete("/api/quadras/{quadra_id}")
def excluir_quadra(quadra_id: int, usuario=Depends(usuario_atual)):
    return services.excluir_quadra(usuario, quadra_id)


@app.get("/api/quadras/{quadra_id}/disponibilidade")
def disponibilidade(quadra_id: int, data: date, modalidade: Modalidade, usuario=Depends(usuario_atual)):
    return services.disponibilidade(usuario, quadra_id, data, modalidade)


@app.post("/api/agendamentos", status_code=201)
def reservar(dados: schemas.NovaReserva, usuario=Depends(usuario_atual)):
    return services.reservar(usuario, dados)


@app.get("/api/agendamentos")
def reservas(usuario=Depends(usuario_atual)):
    return services.listar_reservas(usuario)


@app.post("/api/agendamentos/{reserva_id}/cancelar")
def cancelar(reserva_id: int, usuario=Depends(usuario_atual)):
    return services.cancelar(usuario, reserva_id)


@app.get("/", include_in_schema=False)
def inicio():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")
