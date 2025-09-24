from pipeline.interface import SistemaAutomacao
from core import SiatuAuto, UrbanoAuto, SisctmAuto, GoogleMapsAuto
from utils import driver_context, logger


class Siatu(SistemaAutomacao):
    def executar(self, indice, credenciais, pasta_indice):
        dados_pb = {}
        anexos_count = 0

        perfil = r"C:\Users\glauc\AppData\Local\Google\Chrome\SeleniumProfile"
        with driver_context(pasta_indice, perfil=perfil) as driver:
            siatu = SiatuAuto(
                driver=driver,
                url="https://siatu-producao.pbh.gov.br/seguranca/login?service=https%3A%2F%2Fsiatu-producao.pbh.gov.br%2Faction%2Fmenu",
                usuario=credenciais["usuario"],
                senha=credenciais["senha"],
                pasta_download=pasta_indice,
            )

            if siatu.acessar() and siatu.login() and siatu.navegar():
                dados_pb = siatu.planta_basica(indice)
                anexos_count = siatu.download_anexos(indice)

        logger.info(f"Siatu concluído para índice {indice}")
        return dados_pb, anexos_count


class Urbano(SistemaAutomacao):
    def executar(self, indice, credenciais, pasta_indice):
        dados_projeto = {}
        projetos_count = 0
        with driver_context(pasta_indice) as driver:
            urbano = UrbanoAuto(
                driver=driver,
                url="https://urbano.pbh.gov.br/edificacoes/#/",
                usuario=credenciais["usuario"],
                senha=credenciais["senha"],
                pasta_download=pasta_indice,
            )

            if urbano.acessar() and urbano.login():
                projetos_count, dados_projeto = urbano.download_projeto(indice)

        logger.info(f"Urbano concluído para índice {indice}")
        return dados_projeto, projetos_count


class Sisctm(SistemaAutomacao):
    def executar(self, indice, credenciais, pasta_indice):
        dados_sisctm = {}
        with driver_context(pasta_indice) as driver:
            sisctm = SisctmAuto(
                driver=driver,
                url="https://acesso.pbh.gov.br/auth/realms/PBH/protocol/openid-connect/auth?client_id=sisctm-mapa&redirect_uri=https%3A%2F%2Fsisctm.pbh.gov.br%2Fmapa%2Flogin",
                usuario=credenciais["usuario"],
                senha=credenciais["senha"],
                pasta_download=pasta_indice,
            )

            if sisctm.login() and sisctm.ativar_camadas(indice):
                dados_sisctm = sisctm.capturar_areas()

        logger.info(f"SISCTM concluído para índice {indice}")
        return dados_sisctm


class GoogleMaps(SistemaAutomacao):
    def executar(self, indice, dados_sisctm, dados_pb, pasta_indice):
        endereco = (
            dados_sisctm.get("endereco_ctmgeo")
            or dados_pb.get("endereco_imovel")
            or "Não encontrado"
        )
        with driver_context(pasta_indice) as driver:
            google = GoogleMapsAuto(
                driver,
                url="https://www.google.com/maps/",
                endereco=endereco,
                pasta_download=pasta_indice,
            )
            if google.acessar_google_maps():
                google.navegar()

        logger.info(f"Google Maps concluído para índice {indice}")
