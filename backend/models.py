
"""Objetos e regras que pertencem ao próprio domínio."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal
from enum import StrEnum
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("America/Fortaleza")


def agora():
    """O MVP usa horário local de Fortaleza, sem offset no banco e na API."""
    return datetime.now(FUSO).replace(tzinfo=None)


class Modalidade(StrEnum):
    FUTEVOLEI = "FUTEVOLEI"
    VOLEI = "VOLEI"
    BEACH_TENIS = "BEACH_TENIS"


class StatusAgendamento(StrEnum):
    CONFIRMADO = "CONFIRMADO"
    CANCELADO = "CANCELADO"


@dataclass
class Usuario(ABC):
    id: int
    nome: str
    email: str

    @abstractmethod
    def perfil(self):
        pass


class Cliente(Usuario):
    def perfil(self):
        return "CLIENTE"


class DonoArena(Usuario):
    def perfil(self):
        return "DONO"


@dataclass
class Arena:
    id: int
    dono_id: int
    nome: str
    endereco: str
    abertura: time
    fechamento: time

    def comporta(self, inicio):
        fim = inicio + timedelta(hours=1)
        return (inicio.date() == fim.date()
                and self.abertura <= inicio.time()
                and fim.time() <= self.fechamento)


@dataclass
class Quadra:
    id: int
    arena_id: int
    nome: str
    descricao: str | None
    preco_hora: Decimal
    ativa: bool
    modalidades: list[str]

    def validar_reserva(self, modalidade):
        if not self.ativa:
            raise ValueError("Esta quadra está desativada.")
        if modalidade not in self.modalidades:
            raise ValueError("Esta quadra não oferece a modalidade escolhida.")


@dataclass
class Agendamento:
    id: int
    cliente_id: int
    quadra_id: int
    modalidade: str
    inicio: datetime
    preco_reservado: Decimal
    status: str
    criado_em: datetime
    cancelado_em: datetime | None = None

    @property
    def fim(self):
        return self.inicio + timedelta(hours=1)

    def cancelar(self, cliente_id, momento):
        if self.cliente_id != cliente_id:
            raise ValueError("Você só pode cancelar suas próprias reservas.")
        if self.status == StatusAgendamento.CANCELADO:
            raise ValueError("Esta reserva já foi cancelada.")
        if self.inicio - momento < timedelta(hours=2):
            raise ValueError("O cancelamento exige pelo menos duas horas de antecedência.")
        self.status = StatusAgendamento.CANCELADO
        self.cancelado_em = momento
