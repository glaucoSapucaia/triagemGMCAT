from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from utils import logger

import time
import os


class GoogleMapsAuto:
    """
    Classe para automatizar tarefas relacionadas ao Google Maps via Selenium.
    """

    def __init__(self, driver, url: str, endereco, pasta_download, timeout: int = 10):
        """
        :param driver: instância do Selenium WebDriver
        :param url: URL do Google Maps
        :param timeout: tempo de espera padrão para WebDriverWait
        """
        self.driver = driver
        self.url = url
        self.endereco = endereco
        self.pasta_download = pasta_download
        self.wait = WebDriverWait(self.driver, timeout=timeout)

    def _click(self, element):
        """Tenta clicar diretamente, se falhar usa JavaScript."""
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def acessar_google_maps(self):
        """Abre a página inicial do Google Maps."""
        try:
            self.driver.get(self.url)
            logger.info(f"Acessando Google Maps")
            time.sleep(3)
            return True
        except Exception as e:
            logger.error(f"Erro ao acessar o Google Maps: {e}")
            return

    def navegar(self):
        """Navega até o endereço, muda para satélite, faz prints e Street View."""
        # Insere endereço no campo de busca
        try:
            search_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "searchboxinput"))
            )
            search_input.clear()
            if self.endereco == "Não encontrado" or not self.endereco:
                logger.warning("IC sem endereço, pulando navegação google maps.")
                return
            search_input.send_keys(self.endereco)
            logger.info(f"Endereço digitado")
        except Exception as e:
            logger.error(f"Erro ao localizar campo de busca: {e}")
            return

        # Clica no botão pesquisar
        try:
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "searchbox-searchbutton"))
            )
            self._click(search_button)
            logger.info("Clique no botão pesquisar")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Erro ao clicar no botão pesquisar: {e}")
            return

        # Clica no botão de camada (satélite)
        try:
            satellite_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.yHc72.qk5Wte"))
            )
            self._click(satellite_button)
            logger.info("Visualização satélite ativada")
            time.sleep(3)
        except Exception as e:
            logger.warning(f"Não foi possível ativar visualização satélite: {e}")

        # Print da tela (satélite)
        try:
            caminho_print_aereo = os.path.join(
                self.pasta_download, "google_maps_aereo.png"
            )
            self.driver.save_screenshot(caminho_print_aereo)
            logger.info(f"Print da visualização aérea salvo")
        except Exception as e:
            logger.error(f"Erro ao salvar print da visualização aérea: {e}")

        # Clica no botão para visualizar a fachada (Street View)
        try:
            street_view_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.dQDAle"))
            )
            self._click(street_view_button)
            logger.info("Street View ativado")
            time.sleep(5)
        except Exception as e:
            logger.warning(f"Não foi possível clicar no Street View: {e}")
            return

        # Print da tela (fachada)
        try:
            caminho_print_fachada = os.path.join(
                self.pasta_download, "google_maps_fachada.png"
            )
            self.driver.save_screenshot(caminho_print_fachada)
            logger.info(f"Print da fachada salvo")
        except Exception as e:
            logger.error(f"Erro ao salvar print da fachada: {e}")
