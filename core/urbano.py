import logging
import time
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)


class UrbanoAuto:
    def __init__(self, driver, url, usuario, senha, pasta_download):
        self.driver = driver
        self.url = url
        self.usuario = usuario
        self.senha = senha
        self.pasta_download = pasta_download
        self.wait = WebDriverWait(self.driver, timeout=5)

    def _click(self, element):
        """Tenta clicar diretamente, se falhar usa JavaScript."""
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def acessar(self):
        """Abre o sistema Urbano."""
        try:
            logger.info("Acessando o sistema Urbano: %s", self.url)
            self.driver.get(self.url)
            return True
        except Exception as e:
            logger.error("Erro ao acessar o sistema Urbano: %s", e)
            return False

    def login(self):
        """Realiza login no Urbano PBH."""
        try:
            logger.info("Iniciando login no Urbano")

            # Clicar no botão de acesso
            btn_acesso = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@class='panel-body' and text()='Acesso PBH']")
                )
            )
            self._click(btn_acesso)
            logger.info("Botão 'Acesso PBH' clicado")

            # Preencher usuário
            campo_usuario = self.wait.until(
                EC.presence_of_element_located((By.ID, "usuario"))
            )
            campo_usuario.clear()
            campo_usuario.send_keys(self.usuario)

            # Preencher senha
            campo_senha = self.wait.until(
                EC.presence_of_element_located((By.ID, "senha"))
            )
            campo_senha.clear()
            campo_senha.send_keys(self.senha)

            # Confirmar login
            btn_login = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//input[@type='submit' and @name='Login']")
                )
            )
            self._click(btn_login)
            logger.info("Login realizado com sucesso no Urbano")

            return True
        except Exception as e:
            logger.error("Erro no login do Urbano: %s", e)
            return False

    def download_projeto(self, indice: str):
        """
        Pesquisa o projeto no Urbano e retorna a quantidade de projetos encontrados.
        Também salva prints e tenta baixar certidão de baixa ou alvará se existirem.
        """
        try:
            logger.info("Iniciando pesquisa de projeto para índice: %s", indice)
            indice = indice.strip()
            if len(indice) < 11:
                raise ValueError(f"Índice inválido: {indice}")

            # Divisão do índice
            parte1, parte2, parte3 = indice[0:3], indice[3:7], indice[7:11]

            # --- Preencher campos ---
            campo1 = self.wait.until(
                EC.presence_of_element_located((By.NAME, "zonaFiscal"))
            )
            campo1.clear()
            campo1.send_keys(parte1)

            campo2 = self.wait.until(lambda d: d.find_element(By.NAME, "quart"))
            WebDriverWait(self.driver, 5).until(lambda d: campo2.is_enabled())
            campo2.clear()
            campo2.send_keys(parte2)

            campo3 = self.wait.until(lambda d: d.find_element(By.NAME, "lote"))
            WebDriverWait(self.driver, 5).until(lambda d: campo3.is_enabled())
            campo3.clear()
            campo3.send_keys(parte3)

            # --- Pesquisar ---
            btn_pesquisar = self.wait.until(
                EC.element_to_be_clickable((By.ID, "btnPesquisar"))
            )
            self._click(btn_pesquisar)
            time.sleep(5)  # Aguarda resultados Angular
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(2)  # Aguarda scroll

            # --- Print da pesquisa ---
            screenshot_path = os.path.join(
                self.pasta_download, "Pesquisa de Projeto.png"
            )
            self.driver.save_screenshot(screenshot_path)
            logger.info("Print da tela salvo em: %s", screenshot_path)

            # --- Verificar tabela e contar projetos ---
            try:
                tabela_div = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "div.table-responsive table tbody.project-search-results",
                )
                linhas = tabela_div.find_elements(By.TAG_NAME, "tr")
                qtd_projetos = len(linhas)
                logger.info("%d projetos encontrados", qtd_projetos)

                if qtd_projetos == 0:
                    return 0

                # --- Clicar no primeiro projeto para tentar baixar documentos ---
                primeiro_projeto = linhas[0].find_element(By.TAG_NAME, "a")
                self._click(primeiro_projeto)
                logger.info("Clicado no primeiro projeto da lista")
                time.sleep(15)  # Aguarda carregar página do projeto

            except NoSuchElementException:
                logger.info("Tabela de resultados não encontrada")
                return 0

            # --- Tentar baixar certidão de baixa ---
            certidao = self.driver.find_elements(
                By.XPATH,
                "//a[contains(@href,'certidao-de-baixa') and text()='visualizar']",
            )
            if certidao:
                certidao[0].click()
                logger.info("Certidão de baixa baixada (clique realizado)")
                time.sleep(10)
                return qtd_projetos

            # --- Tentar baixar alvará ---
            alvara = self.driver.find_elements(
                By.XPATH,
                "//a[contains(text(),'visualizar') and @ng-click='statusCtrl.abrirAlvara()']",
            )
            if alvara:
                alvara[0].click()
                logger.info("Alvará baixado (clique realizado)")
                time.sleep(10)
                return qtd_projetos

            # --- Se nenhum documento encontrado, salvar print ---
            if not certidao and not alvara:
                screenshot_sem_doc = os.path.join(
                    self.pasta_download, "Sem Alvará-Baixa.png"
                )
                self.driver.save_screenshot(screenshot_sem_doc)
                logger.info(
                    "Nenhum documento encontrado, print salvo em: %s",
                    screenshot_sem_doc,
                )

            return qtd_projetos

        except Exception as e:
            logger.error("Erro ao pesquisar projeto no Urbano (%s): %s", indice, e)
            return 0
