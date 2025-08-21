import logging
import os
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from interface import iniciar_interface
from core import SiatuAuto, urbano_auto

# Configuração do logger
logging.basicConfig(
    filename="logs.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


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

                # --- Configuração do Firefox ---
                firefox_options = Options()
                firefox_options.headless = False

                # ↓ Preferências de download
                firefox_options.set_preference("browser.download.folderList", 2)
                firefox_options.set_preference(
                    "browser.download.dir", os.path.abspath(pasta_indice)
                )
                firefox_options.set_preference(
                    "browser.helperApps.neverAsk.saveToDisk",
                    "application/pdf,application/octet-stream",
                )
                firefox_options.set_preference(
                    "browser.helperApps.neverAsk.openFile", "application/pdf"
                )
                firefox_options.set_preference(
                    "browser.download.manager.showWhenStarting", False
                )
                firefox_options.set_preference("browser.download.useDownloadDir", True)
                firefox_options.set_preference("browser.download.panel.shown", False)
                firefox_options.set_preference(
                    "pdfjs.disabled", True
                )  # não abrir no visualizador

                # ↓ Certificados inseguros ok
                firefox_options.set_preference("webdriver_accept_untrusted_certs", True)
                firefox_options.set_preference(
                    "webdriver_assume_untrusted_issuer", True
                )

                # ↓ Aceitar automaticamente QUALQUER prompt nativo (inclui "envio inseguro")
                firefox_options.set_capability("unhandledPromptBehavior", "accept")
                firefox_options.set_capability("acceptInsecureCerts", True)

                driver = webdriver.Firefox(options=firefox_options)

                # --- Sistema 1 ---
                siatu = SiatuAuto(
                    driver=driver,
                    url="https://siatu-producao.pbh.gov.br/seguranca/login?service=https%3A%2F%2Fsiatu-producao.pbh.gov.br%2Faction%2Fmenu",
                    usuario=credenciais["usuario"],
                    senha=credenciais["senha"],
                    pasta_download=pasta_indice,
                )

                if (
                    siatu.acessar()
                    and siatu.login()
                    and siatu.navegar()
                    and siatu.download_anexos(indice)
                    and siatu.planta_basica(indice)
                ):
                    logging.info(f"Sistema 1 concluído para índice {indice}")
                else:
                    logging.warning(f"Falha no Sistema 1 para índice {indice}")

                driver.quit()

                # --- Sistema 2 ---
                # urbano_auto(credenciais, indice, pasta_indice)

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
