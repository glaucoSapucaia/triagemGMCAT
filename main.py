import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from interface import iniciar_interface
from core import SiatuAuto, UrbanoAuto

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
    try:
        # Interface coleta credenciais e índices
        credenciais, indices = iniciar_interface()

        for indice in indices:
            try:
                # Criar pasta específica para cada índice
                pasta_indice = os.path.join("resultados", indice)
                os.makedirs(pasta_indice, exist_ok=True)

                logging.info(f"Iniciando coleta para índice: {indice}")

                # --- Sistema 1: Siatu ---
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

                    if (
                        siatu.acessar()
                        and siatu.login()
                        and siatu.navegar()
                        and siatu.planta_basica(indice)
                        and siatu.download_anexos(indice)
                    ):
                        logging.info(f"Sistema 1 concluído para índice {indice}")
                    else:
                        logging.warning(f"Falha no Sistema 1 para índice {indice}")
                finally:
                    driver_siatu.quit()

                # --- Sistema 2: Urbano ---
                driver_urbano = criar_driver(pasta_indice)
                try:
                    urbano = UrbanoAuto(
                        driver=driver_urbano,
                        url="https://urbano.pbh.gov.br/edificacoes/#/",
                        usuario=credenciais["usuario"],
                        senha=credenciais["senha"],
                        pasta_download=pasta_indice,
                    )

                    if (
                        urbano.acessar()
                        and urbano.login()
                        and urbano.download_projeto(indice)
                    ):
                        logging.info(f"Sistema 2 concluído para índice {indice}")
                    else:
                        logging.warning(f"Falha no Sistema 2 para índice {indice}")
                finally:
                    driver_urbano.quit()

            except Exception as e:
                logging.error(f"Erro no processamento do índice {indice}: {e}")

        # --- Abrir pasta resultados após processar todos os índices ---
        pasta_resultados = os.path.abspath("resultados")
        if os.path.exists(pasta_resultados):
            logging.info(f"Abrindo pasta de resultados: {pasta_resultados}")
            os.startfile(pasta_resultados)
        else:
            logging.warning(f"Pasta de resultados não encontrada: {pasta_resultados}")

    except Exception as e:
        logging.critical(f"Erro crítico no main: {e}")


if __name__ == "__main__":
    main()
