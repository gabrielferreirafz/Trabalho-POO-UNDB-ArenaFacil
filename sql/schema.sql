-- Valores de data/hora representam o horário local de America/Fortaleza.
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(100) NOT NULL CHECK (length(trim(nome)) >= 2),
    email VARCHAR(150) NOT NULL UNIQUE CHECK (email = lower(trim(email))),
    perfil VARCHAR(20) NOT NULL CHECK (perfil IN ('CLIENTE', 'DONO'))
);

CREATE TABLE IF NOT EXISTS arenas (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dono_id INTEGER NOT NULL UNIQUE REFERENCES usuarios(id),
    nome VARCHAR(100) NOT NULL,
    endereco VARCHAR(255) NOT NULL,
    abertura TIME NOT NULL,
    fechamento TIME NOT NULL,
    CHECK (abertura < fechamento)
);

CREATE TABLE IF NOT EXISTS quadras (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    arena_id INTEGER NOT NULL REFERENCES arenas(id),
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    preco_hora NUMERIC(10,2) NOT NULL CHECK (preco_hora > 0),
    ativa BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS quadra_modalidades (
    quadra_id INTEGER NOT NULL REFERENCES quadras(id) ON DELETE CASCADE,
    modalidade VARCHAR(50) NOT NULL CHECK (modalidade IN ('FUTEVOLEI', 'VOLEI', 'BEACH_TENIS')),
    PRIMARY KEY (quadra_id, modalidade)
);

CREATE TABLE IF NOT EXISTS agendamentos (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES usuarios(id),
    quadra_id INTEGER NOT NULL REFERENCES quadras(id),
    modalidade VARCHAR(50) NOT NULL CHECK (modalidade IN ('FUTEVOLEI', 'VOLEI', 'BEACH_TENIS')),
    inicio TIMESTAMP NOT NULL CHECK (date_trunc('hour', inicio) = inicio),
    preco_reservado NUMERIC(10,2) NOT NULL CHECK (preco_reservado > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'CONFIRMADO' CHECK (status IN ('CONFIRMADO', 'CANCELADO')),
    criado_em TIMESTAMP NOT NULL,
    cancelado_em TIMESTAMP,
    CHECK ((status = 'CONFIRMADO' AND cancelado_em IS NULL)
        OR (status = 'CANCELADO' AND cancelado_em IS NOT NULL))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_quadra_horario_confirmado
ON agendamentos (quadra_id, inicio) WHERE status = 'CONFIRMADO';

CREATE UNIQUE INDEX IF NOT EXISTS uq_cliente_horario_confirmado
ON agendamentos (cliente_id, inicio) WHERE status = 'CONFIRMADO';
