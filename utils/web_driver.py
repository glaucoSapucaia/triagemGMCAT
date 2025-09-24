from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from contextlib import contextmanager
import os


def criar_driver(pasta_indice=None, caminho_perfil=None, nome_perfil="Default"):
    """
    Configura e retorna um driver Chrome usando um perfil específico já criado.

    :param pasta_indice: pasta onde salvar os downloads.
    :param caminho_perfil: caminho para a pasta de perfis do Chrome.
    :param nome_perfil: nome do perfil do Chrome - "Default".
    """
    chrome_options = Options()
    # chrome_options.add_argument("--start-maximized")  # Inicia o Chrome maximizado
    chrome_options.add_argument("--headless=new")  # Executa o Chrome em modo headless
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-extensions")

    # Remove logs do selenium
    chrome_options.add_argument(
        "--log-level=3"
    )  # INFO=0, WARNING=1, LOG_ERROR=2, LOG_FATAL=3
    chrome_options.add_argument("--silent")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    # Defini resolução para prints em tela cheia
    chrome_options.add_argument("--window-size=1920,1080")

    # Usa um perfil já existente do Chrome
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


@contextmanager
def driver_context(pasta_indice, perfil=None, nome_perfil="Default"):
    """Context manager para criar e fechar o driver automaticamente."""
    driver = criar_driver(pasta_indice, caminho_perfil=perfil, nome_perfil=nome_perfil)
    try:
        yield driver
    finally:
        driver.quit()
