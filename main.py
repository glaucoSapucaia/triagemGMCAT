import logging
import os
import sys
import subprocess
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from interface import iniciar_interface
from core import SiatuAuto, UrbanoAuto, SisctmAuto, GoogleMapsAuto, gerar_relatorio
import locale

# Define a localidade para português do Brasil
locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")


# Configuração do logger
logging.basicConfig(
    filename="logs.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def criar_driver(pasta_indice=None, caminho_perfil=None, nome_perfil="Default"):
    """
    Configura e retorna um driver Chrome usando um perfil específico já criado.

    :param pasta_indice: pasta onde salvar os downloads (se configurada).
    :param caminho_perfil: caminho para a pasta de perfis do Chrome (ex.: C:/Users/SEUUSUARIO/AppData/Local/Google/Chrome/User Data).
    :param nome_perfil: nome do perfil do Chrome (ex.: "Default", "Profile 1").
    """
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-extensions")

    # Usar um perfil já existente do Chrome
    if caminho_perfil:
        chrome_options.add_argument(f"user-data-dir={caminho_perfil}")
        chrome_options.add_argument(f"--profile-directory={nome_perfil}")

    # Configurações de download automático
    if pasta_indice:
        prefs = {
            "download.default_directory": os.path.abspath(pasta_indice),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,  # não abre PDF no Chrome, baixa direto
        }
        chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def main():
    """
    Função principal que orquestra a coleta de dados e geração de relatórios.
    """
    try:
        # Interface inicial que coleta credenciais e índices
        credenciais, indices = iniciar_interface()

        # Timestamp legível para a pasta resultados
        timestamp_legivel = datetime.now().strftime("Resultados - %d de %B de %Y %Hh%M")
        pasta_resultados = timestamp_legivel
        os.makedirs(pasta_resultados, exist_ok=True)

        for indice in indices:
            try:
                pasta_indice = os.path.join(pasta_resultados, indice)
                os.makedirs(pasta_indice, exist_ok=True)

                logging.info(f"Iniciando coleta para índice: {indice}")

                # Sistema 1: Siatu (PB e Anexos)
                driver_siatu = criar_driver(
                    pasta_indice,
                    caminho_perfil=r"C:\Users\glauc\AppData\Local\Google\Chrome\SeleniumProfile",
                    nome_perfil="Default",
                )
                try:
                    siatu = SiatuAuto(
                        driver=driver_siatu,
                        url="https://siatu-producao.pbh.gov.br/seguranca/login?service=https%3A%2F%2Fsiatu-producao.pbh.gov.br%2Faction%2Fmenu",
                        usuario=credenciais["usuario"],
                        senha=credenciais["senha"],
                        pasta_download=pasta_indice,
                    )

                    anexos_count = 0

                    if siatu.acessar() and siatu.login() and siatu.navegar():
                        dados_PB = siatu.planta_basica(indice)
                        anexos_count = siatu.download_anexos(indice)

                    logging.info(f"Sistema 1 concluído para índice {indice}")
                finally:
                    driver_siatu.quit()

                # Sistema 2: Urbano (Projeto, Alvará e Baixa de Construção)
                driver_urbano = criar_driver(pasta_indice)
                try:
                    urbano = UrbanoAuto(
                        driver=driver_urbano,
                        url="https://urbano.pbh.gov.br/edificacoes/#/",
                        usuario=credenciais["usuario"],
                        senha=credenciais["senha"],
                        pasta_download=pasta_indice,
                    )

                    projetos_count = 0
                    if urbano.acessar() and urbano.login():
                        projetos_count, dados_projeto = urbano.download_projeto(indice)

                    logging.info(f"Sistema 2 concluído para índice {indice}")
                finally:
                    driver_urbano.quit()

                # Sistema 3: SISCTM (Dados gerais do imóvel)
                driver_sistcm = criar_driver(pasta_indice)
                try:
                    sisctm = SisctmAuto(
                        driver=driver_sistcm,
                        url="https://acesso.pbh.gov.br/auth/realms/PBH/protocol/openid-connect/auth?client_id=sisctm-mapa&redirect_uri=https%3A%2F%2Fsisctm.pbh.gov.br%2Fmapa%2Flogin&state=9ac6fe5e-84df-4a25-97b4-b8f3a2a49c83&response_mode=fragment&response_type=code&scope=openid&nonce=d9b8a792-a2e7-431f-819c-ca77096dbaf5",
                        usuario=credenciais["usuario"],
                        senha=credenciais["senha"],
                        pasta_download=pasta_indice,
                    )

                    if sisctm.login() and sisctm.ativar_camadas(indice):
                        dados_sisctm = sisctm.capturar_areas()
                        pass

                    logging.info(f"Sistema 3 concluído para índice {'indice'}")
                finally:
                    driver_sistcm.quit()

                # Sistema 4: GOOGLE MAPS (Print Aereo e Fachada)
                driver_google = criar_driver(pasta_indice)
                if dados_sisctm.get("endereco_ctmgeo"):
                    endereco_google = dados_sisctm["endereco_ctmgeo"]
                elif dados_PB.get("endereco_imovel"):
                    endereco_google = dados_PB["endereco_imovel"]
                else:
                    endereco_google = "Não encontrado"

                try:
                    google = GoogleMapsAuto(
                        driver=driver_google,
                        url="https://www.google.com/maps/",
                        endereco=endereco_google,
                        pasta_download=pasta_indice,
                    )

                    if google.acessar_google_maps():
                        google.navegar()

                    logging.info(f"Sistema 4 concluído para índice {'indice'}")
                finally:
                    driver_google.quit()

                # Gera o relatório PDF
                pdf_path = os.path.join(
                    pasta_indice, f"1. Relatório de Triagem - {indice}.pdf"
                )
                gerar_relatorio(
                    indice_cadastral=indice,
                    anexos_count=anexos_count,
                    projetos_count=projetos_count,
                    pasta_anexos=pasta_indice,
                    prps_trabalhador=credenciais["usuario"],
                    nome_pdf=pdf_path,
                    dados_planta=dados_PB,
                    dados_projeto=dados_projeto,
                    dados_sisctm=dados_sisctm,
                )
                logging.info(f"Relatório gerado: {pdf_path}")

            except Exception as e:
                logging.error(f"Erro no processamento do índice {indice}: {e}")

        # Abri a pasta resultados após processar todos os índices (Apneas windows)
        # if os.path.exists(pasta_resultados):
        #     logging.info(f"Abrindo pasta de resultados: {pasta_resultados}")
        #     os.startfile(pasta_resultados)
        # else:
        #     logging.warning(f"Pasta de resultados não encontrada: {pasta_resultados}")

        # Abri pasta com OS dinâmico
        if os.path.exists(pasta_resultados):
            logging.info(f"Abrindo pasta de resultados: {pasta_resultados}")
            abrir_pasta(pasta_resultados)
        else:
            logging.warning(f"Pasta de resultados não encontrada: {pasta_resultados}")

    except Exception as e:
        logging.critical(f"Erro crítico no main: {e}")


def abrir_pasta(path):
    if sys.platform.startswith("win"):  # Windows
        os.startfile(path)
    elif sys.platform.startswith("darwin"):  # macOS
        subprocess.Popen(["open", path])
    else:  # Linux
        subprocess.Popen(["xdg-open", path])


if __name__ == "__main__":
    inicio = datetime.now()
    main()
    fim = datetime.now()
    duracao = fim - inicio

    minutos, segundos = divmod(duracao.total_seconds(), 60)
    print(f"⏱ Tempo de execução: {int(minutos)} min {int(segundos)} seg")
