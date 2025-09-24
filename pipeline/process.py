from utils import criar_pasta_resultados, logger
from core import gerar_relatorio
from .sistemas import Siatu
from .sistemas import Urbano
from .sistemas import Sisctm
from .sistemas import GoogleMaps

import os

pasta_resultados = criar_pasta_resultados()


def processar_indice(indice, credenciais):
    pasta_indice = os.path.join(pasta_resultados, indice)
    os.makedirs(pasta_indice, exist_ok=True)

    dados_pb, anexos_count = Siatu().executar(indice, credenciais, pasta_indice)
    dados_projeto, projetos_count = Urbano().executar(indice, credenciais, pasta_indice)
    dados_sisctm = Sisctm().executar(indice, credenciais, pasta_indice)
    GoogleMaps().executar(indice, dados_sisctm, dados_pb, pasta_indice)

    pdf_path = os.path.join(pasta_indice, f"1. Relatório de Triagem - {indice}.pdf")
    gerar_relatorio(
        indice_cadastral=indice,
        anexos_count=anexos_count,
        projetos_count=projetos_count,
        pasta_anexos=pasta_indice,
        prps_trabalhador=credenciais["usuario"],
        nome_pdf=pdf_path,
        dados_planta=dados_pb,
        dados_projeto=dados_projeto,
        dados_sisctm=dados_sisctm,
    )
    logger.info(f"Relatório gerado")
