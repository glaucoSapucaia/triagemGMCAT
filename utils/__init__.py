from .logger import logger
from .pastas import abrir_pasta, criar_pasta_resultados
from .web_driver import driver_context
from .relatorio import (
    normalizar_nome,
    extrair_elementos_do_endereco_para_comparacao,
    parse_area,
    formatar_area,
    comparar_areas,
)

__all__ = [
    "logger",
    "abrir_pasta",
    "driver_context",
    "criar_pasta_resultados",
    "normalizar_nome",
    "extrair_elementos_do_endereco_para_comparacao",
    "parse_area",
    "formatar_area",
    "comparar_areas",
]
