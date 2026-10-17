from fastapi import FastAPI
app = FastAPI(title="API de Quadras")

# dados de exemplo (por enquanto sem banco)
quadras = [
    {"id": 1, "nome": "Quadra 1", "tipo": "volei", "preco_hora": 80},
    {"id": 2, "nome": "Quadra A", "tipo": "futebol", "preco_hora": 120},
]


@app.get("/")
def raiz():
    return {"mensagem": "API de quadras funcionando!"}


@app.get("/quadras")
def listar_quadras():
    return quadras
