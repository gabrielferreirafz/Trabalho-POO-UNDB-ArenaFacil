
"""Validação dos dados recebidos pela API."""

from datetime import datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.models import FUSO, Modalidade


class Entrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class Email(Entrada):
    email: str = Field(min_length=3, max_length=150)

    @field_validator("email")
    @classmethod
    def validar_email(cls, valor):
        partes = valor.split("@")
        if len(partes) != 2 or not partes[0] or "." not in partes[1] or any(c.isspace() for c in valor):
            raise ValueError("Informe um e-mail válido.")
        return valor.lower()


class CadastroCliente(Email):
    nome: str = Field(min_length=2, max_length=100)


class CadastroDono(CadastroCliente):
    arena_nome: str = Field(min_length=2, max_length=100)
    endereco: str = Field(min_length=3, max_length=255)
    abertura: time
    fechamento: time

    @model_validator(mode="after")
    def funcionamento(self):
        if self.abertura.tzinfo or self.fechamento.tzinfo:
            raise ValueError("Informe horários locais sem fuso.")
        if self.abertura >= self.fechamento:
            raise ValueError("A abertura deve ser anterior ao fechamento, no mesmo dia.")
        if self.abertura.second or self.abertura.microsecond or self.fechamento.second or self.fechamento.microsecond:
            raise ValueError("Informe o funcionamento em horas e minutos.")
        return self


class DadosQuadra(Entrada):
    nome: str = Field(min_length=2, max_length=100)
    descricao: str = Field(default="", max_length=500)
    preco_hora: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    modalidades: list[Modalidade] = Field(min_length=1, max_length=3)

    @field_validator("modalidades")
    @classmethod
    def sem_repeticao(cls, valores):
        return list(dict.fromkeys(valores))


class NovaReserva(Entrada):
    quadra_id: int = Field(gt=0)
    modalidade: Modalidade
    inicio: datetime

    @field_validator("inicio")
    @classmethod
    def horario_local(cls, valor):
        if valor.tzinfo:
            valor = valor.astimezone(FUSO).replace(tzinfo=None)
        return valor
