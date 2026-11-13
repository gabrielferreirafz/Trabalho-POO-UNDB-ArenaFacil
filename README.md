# Arena Fácil

Aplicação web para agendamentos no mercado de arenas esportivas, desenvolvida para a disciplina de Programação Orientada a Objetos da UNDB.

O cliente encontra arenas, consulta a disponibilidade das quadras e confirma reservas. O dono cadastra sua arena, gerencia as quadras e acompanha os agendamentos. O projeto contempla futevôlei, vôlei e beach tênis, com uma interface em tema escuro e laranja.

## Funcionalidades

| Perfil  | Operações                                                                                                                                                                                                         |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Cliente | Cadastro e identificação por e-mail; busca de arenas pelo nome; consulta de quadras, modalidades e horários; confirmação de reservas; consulta do histórico e cancelamento das próprias reservas dentro do prazo. |
| Dono    | Cadastro conjunto com sua única arena; cadastro, edição e exclusão/desativação de quadras; consulta das reservas da própria arena.                                                                                |

As reservas duram uma hora, começam em hora cheia e são confirmadas imediatamente. O sistema verifica conflitos de quadra e cliente, preserva o preço contratado e mantém o histórico dos agendamentos.

A identificação é simplificada, por e-mail e sem senha. Ela permite demonstrar os perfis do sistema, mas **não oferece autenticação segura para uso em produção**.

## Tecnologias

| Parte                     | Tecnologia                           |
| ------------------------- | ------------------------------------ |
| Back-end e API            | Python 3.13 e FastAPI                |
| Interface                 | HTML, CSS e JavaScript               |
| Banco de dados            | PostgreSQL e Psycopg, com SQL direto |
| Testes                    | Pytest e cliente de testes HTTP      |
| Ambiente local            | Docker Compose                       |
| Versionamento e automação | Git, GitHub e GitHub Actions         |

## Documentação

- [Modelo de domínio e aplicação de POO](docs/modelo-dominio.md)
- [Modelo do banco de dados](docs/modelo-banco-dados.md)
- [Engenharia de requisitos](docs/engenharia-requisitos.md)

## Executar com Docker

É necessário ter Docker instalado e em execução, com o comando `docker compose` disponível. Não é necessário instalar Python ou PostgreSQL no computador para esse modo.

Na raiz do repositório, execute:

```console
docker compose up -d
```

A primeira inicialização baixa as imagens e instala as dependências. Acompanhe a inicialização da API com:

```console
docker compose logs -f app
```

Quando aparecer a mensagem de inicialização concluída, acesse:

| Recurso                        | Endereço local                  |
| ------------------------------ | ------------------------------- |
| Interface                      | http://localhost:8000           |
| Documentação interativa da API | http://localhost:8000/docs      |
| Verificação da API e do banco  | http://localhost:8000/api/saude |

A própria API serve a interface e cria as tabelas a partir de `sql/schema.sql`. Para esse modo, as variáveis já estão no Compose; não é necessário criar `.env`. As credenciais fornecidas são exemplos para desenvolvimento local, e as portas são publicadas apenas no próprio computador.

Para encerrar os serviços:

```console
docker compose down
```

Os dados permanecem no volume `arena_dados`. A opção `-v` remove o volume e seus dados. Se alterar `requirements.txt`, reinicie o serviço `app` para instalar as dependências atualizadas.

## Executar com Python e PostgreSQL

Pré-requisitos: Python 3.13 e PostgreSQL 17 ou superior. O banco precisa estar em execução antes de iniciar a API.

Uma opção é iniciar apenas o PostgreSQL do Compose:

```console
docker compose up -d db
```

Se utilizar uma instalação própria do PostgreSQL, crie previamente o usuário e o banco indicados na sua configuração.

No PowerShell, prepare o ambiente na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

No Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Ajuste `DATABASE_URL` no `.env` com os dados do seu PostgreSQL. O exemplo corresponde ao banco do Compose acessado pelo computador. O `.env` é local e não deve ser publicado no GitHub.

Inicie a aplicação:

```console
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Se o PowerShell bloquear a ativação do ambiente virtual, utilize `.\.venv\Scripts\python.exe` no lugar de `python` nos comandos, sem ativá-lo.

Abra a interface pelo endereço HTTP. Abrir `frontend/index.html` diretamente não inicia a API nem o banco. A criação das tabelas é idempotente; ela não migra automaticamente um banco com esquema antigo.

## Executar os testes

A suíte utiliza PostgreSQL real e exige um banco exclusivo, com nome terminado em `_test`. Os dados desse banco são apagados antes de cada caso. Não execute duas instâncias da suíte simultaneamente no mesmo banco.

Se estiver usando o banco do Compose, crie o banco de testes uma única vez:

```console
docker compose exec db createdb -U arena arena_facil_test
```

Com a aplicação do Compose em execução:

```console
docker compose exec -e ARENA_TEST_DATABASE_URL=postgresql://arena:arena_local@db:5432/arena_facil_test app python -m pytest -q
```

Ou, com o ambiente Python local preparado e `ARENA_TEST_DATABASE_URL` configurada no `.env`:

```console
python -m pytest -q
```

A variável também pode ser definida no terminal. No PowerShell:

```powershell
$env:ARENA_TEST_DATABASE_URL = 'postgresql://arena:arena_local@localhost:5432/arena_facil_test'
python -m pytest -q
```

No Linux/macOS, utilize `export ARENA_TEST_DATABASE_URL='postgresql://arena:arena_local@localhost:5432/arena_facil_test'` antes de executar o Pytest.

Os testes abrangem cadastros, perfis e propriedade, modalidades, funcionamento, conflitos simultâneos, horas consecutivas, cancelamentos, preço histórico, desativação e persistência entre inicializações da API. O [workflow de testes](.github/workflows/tests.yml) está configurado para executar a suíte com PostgreSQL 17 em eventos de `push` e `pull_request`; o resultado de cada execução fica disponível na aba **Actions** do repositório.

## Demonstração do fluxo principal

1. Cadastre um dono e sua arena, com funcionamento das 07h às 23h.
2. Cadastre uma quadra com preço e modalidades permitidas.
3. Saia e cadastre um cliente.
4. Busque a arena pelo nome e consulte os horários de uma data futura.
5. Escolha modalidade e horário, confira o resumo e confirme a reserva.
6. Consulte a reserva e confirme que o horário deixou de aparecer para outra reserva conflitante. Horas consecutivas continuam disponíveis quando não houver outros impedimentos.
7. Como dono, consulte o agendamento e tente excluir a quadra: reservas futuras confirmadas impedem essa operação.
8. Como cliente responsável, cancele com pelo menos duas horas de antecedência. O horário será liberado e o registro continuará no histórico.
9. Depois de cancelar todas as reservas futuras da quadra, solicite sua exclusão como dono. Como já existe histórico, ela será desativada.

O sistema não insere contas ou reservas automaticamente. Para uma demonstração, utilize cadastros próprios de teste.

## Organização do projeto

```text
backend/
    models.py                  classes e comportamentos do domínio
    database.py                conexão e operações SQL
    schemas.py                 validação das entradas HTTP
    services.py                regras e transações entre entidades
    main.py                    rotas e integração da aplicação
frontend/
    index.html                 estrutura das telas
    style.css                  estilos e responsividade
    script.js                  eventos e chamadas à API
sql/
    schema.sql                 tabelas, chaves, restrições e índices
tests/
    test_quadras.py
    test_agendamentos.py
docs/
    modelo-dominio.md
    modelo-banco-dados.md
    engenharia-requisitos.md
    cronograma-entregas.md
.github/workflows/
    tests.yml
.env.example
.gitignore
docker-compose.yml
requirements.txt
README.md
```

As instruções de execução utilizam os arquivos versionados do projeto. `.env`, `.venv/`, `.tools/`, `__pycache__/` e `.pytest_cache/` são locais e ficam fora das entregas pelo Git.

## Decisões e limites do MVP

- Um dono possui uma arena, cadastrada junto com seu perfil.
- O funcionamento é diário, definido no cadastro e não atravessa a meia-noite.
- O catálogo é fixo: futevôlei, vôlei e beach tênis.
- O cancelamento é realizado somente pelo cliente responsável, com antecedência mínima de duas horas, inclusive no limite.
- Quadras com reservas futuras confirmadas não podem ser excluídas/desativadas nem perder modalidades usadas nessas reservas.
- Quadras sem histórico podem ser apagadas; com histórico, são desativadas. Não há reativação no MVP.
- Datas e horários seguem `America/Fortaleza`; o banco armazena horários locais sem offset.
- Pagamentos, notificações, indicadores gerenciais e reservas recorrentes ficam fora do escopo.

Os comandos deste README executam o sistema localmente. O acesso pela internet depende de hospedagem da aplicação e de um PostgreSQL, com `DATABASE_URL` configurada no ambiente do serviço. Publicar arquivos no GitHub não inicia esses serviços.

## Equipe

| Integrante       | Responsabilidade                     |
| ---------------- | ------------------------------------ |
| Gabriel Ferreira | Tech Lead                            |
| Lukas Smith      | Back-end                             |
| Lucas Viana      | Front-end                            |
| Gustavo Carvalho | Banco de dados                       |
| Pedro Igor       | DevOps                               |
| Pacífico         | QA                                   |

