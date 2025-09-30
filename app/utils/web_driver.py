from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException, SessionNotCreatedException

from contextlib import contextmanager
import os
import time
import psutil

from .logger import logger


def _kill_selenium_driver(driver):
    """
    Encerra apenas o Chrome iniciado pelo Selenium.
    Não interfere em outros navegadores abertos.
    """
    if not driver:
        logger.info("Driver não existe, nada para encerrar.")
        return

    try:
        # Tenta pegar PID do processo do Chrome
        driver_pid = getattr(driver, "_chrome_pid", None)
        if driver_pid is None:
            driver_pid = driver.service.process.pid
            driver._chrome_pid = driver_pid

        parent = psutil.Process(driver_pid)

        # Mata todos os processos filhos (renderers, etc)
        for child in parent.children(recursive=True):
            child.kill()
            logger.info(f"Processo filho do Chrome encerrado: {child.pid}")

        # Mata o processo principal do driver
        parent.kill()
        logger.info(f"Processo principal do Chrome encerrado: {parent.pid}")

        time.sleep(1)

    except psutil.NoSuchProcess:
        logger.warning("O processo do Selenium já estava encerrado.")
    except Exception as e:
        logger.error(f"Erro ao tentar encerrar processo do Selenium: {e}")


def criar_driver(
    pasta_indice=None, caminho_perfil=None, nome_perfil="Default", add_config=None
):
    """
    Criação de webdriver chrome.

    Parâmetros:
    add_config: flag experimental HTTP.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Executar em segundo plano.
    # chrome_options.add_argument("--start-maximized")  # Executar navegador maximizdo.
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--silent")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--window-size=1920,1080")

    # Flag experimental
    if add_config:
        chrome_options.add_argument(
            "--unsafely-treat-insecure-origin-as-secure=http://dividaativaonline.siatu.pbh.gov.br"
        )

    if caminho_perfil:
        chrome_options.add_argument(f"user-data-dir={caminho_perfil}")
        chrome_options.add_argument(f"--profile-directory={nome_perfil}")

    if pasta_indice:
        prefs = {
            "download.default_directory": os.path.abspath(pasta_indice),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
        }
        chrome_options.add_experimental_option("prefs", prefs)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver = webdriver.Chrome(options=chrome_options)
    return driver


@contextmanager
def driver_context(pasta_indice, perfil=None, nome_perfil="Default", add_config=None):
    """
    Cria, usa e finaliza webdriver.
    """
    driver = None
    try:
        driver = criar_driver(
            pasta_indice,
            caminho_perfil=perfil,
            nome_perfil=nome_perfil,
            add_config=add_config,
        )
        yield driver
    except SessionNotCreatedException as e:
        logger.error(f"Falha ao criar sessão do Chrome no driver_context: {e}")
        logger.info("Encerrando driver Selenium de forma segura para retry.")
        _kill_selenium_driver(driver)
        raise
    except WebDriverException as e:
        logger.error(f"Erro WebDriver no driver_context: {e}")
        logger.info("Encerrando driver Selenium de forma segura para retry.")
        _kill_selenium_driver(driver)
        raise
    except Exception as e:
        logger.error(f"Erro inesperado no driver_context: {e}")
        logger.info("Encerrando driver Selenium de forma segura para retry.")
        _kill_selenium_driver(driver)
        raise
    finally:
        if driver:
            try:
                driver.quit()
                logger.info(
                    "Driver encerrado normalmente no finally do context manager."
                )
            except Exception as e:
                logger.warning(f"driver.quit() falhou no finally: {e}")
                _kill_selenium_driver(driver)
        else:
            logger.info(
                "Driver não foi criado, mas executando encerramento seguro por precaução."
            )
            _kill_selenium_driver(driver)
