from pipeline.interface import SistemaAutomacao
from core import SiatuAuto, UrbanoAuto, SisctmAuto, GoogleMapsAuto, SigedeAuto
from utils import driver_context, logger, retry


class Sigede(SistemaAutomacao):
    def executar(self, protocolo, credenciais, pasta_protocolo):
        indices = []

        with driver_context(pasta_protocolo) as driver:
            sigede = SigedeAuto(
                driver=driver,
                url="https://cas.pbh.gov.br/cas/login?service=https%3A%2F%2Fsigede.pbh.gov.br%2Fsigede%2Flogin%2Fcas",
                usuario=credenciais["usuario_sigede"],
                senha=credenciais["senha_sigede"],
                pasta_download=pasta_protocolo,
            )

            if sigede.acessar() and sigede.login() and sigede.navegar(protocolo):
                indices = sigede.verificar_tabela()

        logger.info(f"SIGEDE concluído para protocolo {protocolo}")
        return indices


class Siatu(SistemaAutomacao):

    def executar(self, indice, credenciais, pasta_indice):
        dados_pb = {}
        anexos_count = 0
        add_config = True

        @retry(max_retries=4, delay=5, exceptions=(Exception,))
        def fluxo_siatu():
            with driver_context(pasta_indice, add_config=add_config) as driver:
                siatu = SiatuAuto(
                    driver=driver,
                    url="https://siatu-producao.pbh.gov.br/seguranca/login?service=https%3A%2F%2Fsiatu-producao.pbh.gov.br%2Faction%2Fmenu",
                    usuario=credenciais["usuario"],
                    senha=credenciais["senha"],
                    pasta_download=pasta_indice,
                )

                if siatu.acessar() and siatu.login() and siatu.navegar():
                    return siatu.planta_basica(indice), siatu.download_anexos(indice)

        try:
            dados_pb, anexos_count = fluxo_siatu()
        except Exception as e:
            logger.error(f"Falha no fluxo do SIATU para índice {indice}: {e}")

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
        if dados_sisctm or dados_pb:
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
