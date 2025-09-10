from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import logging
import os


class GoogleMapsAuto:
    """
    Classe para automatizar tarefas relacionadas ao Google Earth via Selenium.
    """

    def __init__(self, driver, url: str, endereco, pasta_download, timeout: int = 10):
        """
        :param driver: instância do Selenium WebDriver
        :param url: URL do Google Earth
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
        """Abre a página inicial do Google Earth."""
        try:
            self.driver.get(self.url)
            logging.info(f"Acessando Google Earth: {self.url}")
            time.sleep(3)  # espera a página carregar (ajustável)
            return True
        except Exception as e:
            logging.error(f"Erro ao localizar campo de busca: {e}")
            return

    def navegar(self):
        """Navega até o endereço, muda para satélite, faz prints e Street View."""
        # 1. Inserir endereço no campo de busca
        try:
            search_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "searchboxinput"))
            )
            search_input.clear()
            search_input.send_keys(self.endereco)
            logging.info(f"Endereço digitado: {self.endereco}")
        except Exception as e:
            logging.error(f"Erro ao localizar campo de busca: {e}")
            return

        # 2. Clicar no botão pesquisar
        try:
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "searchbox-searchbutton"))
            )
            self._click(search_button)
            logging.info("Clique no botão pesquisar")
            time.sleep(5)  # espera o mapa atualizar
        except Exception as e:
            logging.error(f"Erro ao clicar no botão pesquisar: {e}")
            return

        # 3. Clicar no botão de camada (satélite)
        try:
            satellite_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.yHc72.qk5Wte"))
            )
            self._click(satellite_button)
            logging.info("Visualização satélite ativada")
            time.sleep(3)
        except Exception as e:
            logging.warning(f"Não foi possível ativar visualização satélite: {e}")

        # 4. Print da tela (satélite)
        try:
            caminho_print_aereo = os.path.join(
                self.pasta_download, "google_maps_aereo.png"
            )
            self.driver.save_screenshot(caminho_print_aereo)
            logging.info(f"Print da visualização aérea salvo em: {caminho_print_aereo}")
        except Exception as e:
            logging.error(f"Erro ao salvar print da visualização aérea: {e}")

        # 5. Clicar no botão para visualizar a fachada (Street View)
        try:
            street_view_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.dQDAle"))
            )
            self._click(street_view_button)
            logging.info("Street View ativado")
            time.sleep(5)  # espera Street View carregar
        except Exception as e:
            logging.warning(f"Não foi possível abrir Street View: {e}")
            return

        # 6. Print da tela (fachada)
        try:
            caminho_print_fachada = os.path.join(
                self.pasta_download, "google_maps_fachada.png"
            )
            self.driver.save_screenshot(caminho_print_fachada)
            logging.info(f"Print da fachada salvo em: {caminho_print_fachada}")
        except Exception as e:
            logging.error(f"Erro ao salvar print da fachada: {e}")
