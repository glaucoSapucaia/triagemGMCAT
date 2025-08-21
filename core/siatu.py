import logging
import os
import time
import pyautogui
import shutil
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)


class SiatuAuto:
    def __init__(self, driver, url, usuario, senha, pasta_download):
        self.driver = driver
        self.url = url
        self.usuario = usuario
        self.senha = senha
        self.pasta_download = pasta_download
        self.wait = WebDriverWait(self.driver, timeout=5)

    def _click(self, element):
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def acessar(self):
        try:
            logger.info("Acessando o Sistema 1: %s", self.url)
            self.driver.get(self.url)
            return True
        except Exception as e:
            logger.error("Erro ao acessar o sistema: %s", e)
            return False

    def login(self):
        try:
            logger.info("Preenchendo usuário e senha")
            self.wait.until(
                EC.presence_of_element_located((By.ID, "usuario"))
            ).send_keys(self.usuario)
            self.wait.until(EC.presence_of_element_located((By.ID, "senha"))).send_keys(
                self.senha
            )
            self.wait.until(EC.element_to_be_clickable((By.NAME, "Login"))).click()
            logger.info("Login realizado com sucesso")
            return True
        except Exception as e:
            logger.error("Erro no login: %s", e)
            return False

    def navegar(self):
        try:
            # Esperar iframe e entrar
            iframe = self.wait.until(
                EC.presence_of_element_located((By.NAME, "iframe"))
            )
            self.driver.switch_to.frame(iframe)

            # Esperar botão '+' e clicar no pai <a>
            btn_plus = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//img[@id='nodeIcon2']/parent::a")
                )
            )
            self._click(btn_plus)

            # Clicar no link de consulta
            link_consulta = self.wait.until(
                EC.element_to_be_clickable((By.ID, "itemTextLink3"))
            )
            self._click(link_consulta)

            self.driver.switch_to.default_content()
            return True
        except Exception as e:
            logger.error("Erro durante a navegação: %s", e)
            try:
                self.driver.switch_to.default_content()
            except:
                pass
            return False

    def download_anexos(self, indice_cadastral: str):
        try:
            logger.info(
                "Iniciando download de anexos para índice: %s", indice_cadastral
            )

            # 1. Preencher índice cadastral
            campo_indice = self.wait.until(
                EC.presence_of_element_located((By.ID, "indiceCadastral"))
            )
            campo_indice.clear()
            campo_indice.send_keys(indice_cadastral)
            logger.info("Índice cadastral preenchido")

            # 2. Clica em exercício e aguardar a página recarregar
            campo_exercicio = self.wait.until(
                EC.presence_of_element_located((By.ID, "exercicio"))
            )
            self._click(campo_exercicio)  # só clica, não altera o valor
            logger.info("Exercício clicado")

            # Aguardar carregamento (ajustar se necessário)
            time.sleep(2)

            # 3. Clicar no botão "planta básica" (buscando pelo value)
            btn_planta = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//input[@type='submit' and @value='planta básica']")
                )
            )
            self._click(btn_planta)
            logger.info("Botão 'planta básica' clicado")

            # 4. Clicar no link "Anexos"
            link_anexos = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[text()='Anexos']"))
            )
            self._click(link_anexos)
            logger.info("Link 'Anexos' clicado")

            # 5. Verificar se há arquivos para download
            anexos = self.driver.find_elements(
                By.XPATH, "//table//tr/td[1]/a[contains(@onclick, 'exibeDocumento')]"
            )

            if anexos:
                logger.info("Foram encontrados %d anexos para download", len(anexos))

                for i, anexo in enumerate(anexos, start=1):
                    # Reconsultar o elemento para evitar StaleElementReferenceException
                    anexos_atualizados = self.driver.find_elements(
                        By.XPATH,
                        "//table//tr/td[1]/a[contains(@onclick, 'exibeDocumento')]",
                    )
                    anexo_atual = anexos_atualizados[i - 1]

                    nome_arquivo = anexo_atual.text.strip()

                    # Baixar apenas arquivos PDF
                    if not nome_arquivo.lower().endswith(".pdf"):
                        logger.info(
                            "Anexo %d ignorado (não é PDF): %s", i, nome_arquivo
                        )
                        continue

                    self._click(anexo_atual)
                    logger.info("Anexo %d clicado: %s", i, nome_arquivo)

                    # Opcional: aguardar um tempo para o download iniciar
                    time.sleep(2)
            else:
                logger.info("Nenhum arquivo disponível para download")

            return True

        except TimeoutException as e:
            logger.error("Timeout ao tentar baixar anexos: %s", e)
            return False
        except NoSuchElementException as e:
            logger.error("Elemento não encontrado: %s", e)
            return False
        except Exception as e:
            logger.error("Erro inesperado em download_anexos: %s", e)
            return False

    def planta_basica(self, indice_cadastral: str):
        """
        Acessa o sistema SIATU e obtem a planta básica.
        """

        # Acessa o navegador
        pyautogui.click(2055, 2087)

        # Acessa a aba
        pyautogui.click(1168, 43)

        # Login
        pyautogui.doubleClick(1976, 1260)
        pyautogui.write(self.usuario)
        time.sleep(1)

        # Pula para o próximo campo
        pyautogui.press("tab")
        time.sleep(1)

        # Senha
        pyautogui.write(self.senha)

        # Confimra login
        pyautogui.click(2128, 1382)
        time.sleep(3)

        # Clica em consulta
        pyautogui.click(1425, 714)
        time.sleep(1)

        # Clica em consultar planta básica
        pyautogui.click(1757, 779)
        time.sleep(3)

        # Indica IC
        pyautogui.click(1114, 734)
        pyautogui.write(indice_cadastral)
        time.sleep(1)

        # Aguarda o sistema carregar
        pyautogui.click(1697, 1046)
        time.sleep(2)

        # Clica em Planta Básica
        pyautogui.click(2362, 829)
        time.sleep(3)

        # Clica em primeiro do ano
        pyautogui.click(2772, 807)
        time.sleep(2)

        # Clica em gerar planta básica
        pyautogui.click(2397, 876)
        time.sleep(2)

        # Clica em enviar
        pyautogui.click(874, 1357)
        time.sleep(2)

        # Clica em download
        pyautogui.click(2849, 292)
        time.sleep(2)

        # Clica em salvar
        pyautogui.click(3123, 1897)
        time.sleep(2)

        # Clica em manter download
        pyautogui.click(2880, 272)
        time.sleep(2)

        # Fecha poup download
        pyautogui.press("esc")
        time.sleep(1)

        # Fecha PDF
        pyautogui.click(3097, 41)
        time.sleep(1)

        # Clica em sair
        pyautogui.click(2677, 531)
        time.sleep(2)

        # Minimiza janela para novo processo
        pyautogui.click(3484, 45)
        time.sleep(2)

        self.mover_download_padrao(self.pasta_download)

    def mover_download_padrao(
        self, pasta_resultados: str, nome_arquivo_esperado: str = None
    ):
        """
        Move o arquivo mais recente da pasta de downloads padrão para a pasta de resultados.
        Se nome_arquivo_esperado for fornecido, move apenas se o arquivo contiver esse nome.
        """
        pasta_download_padrao = os.path.join(os.path.expanduser("~"), "Downloads")
        arquivos = [
            os.path.join(pasta_download_padrao, f)
            for f in os.listdir(pasta_download_padrao)
        ]
        arquivos = [f for f in arquivos if os.path.isfile(f)]

        if not arquivos:
            logger.warning("Nenhum arquivo encontrado na pasta de downloads padrão")
            return False

        # Ordenar pelo mais recente
        arquivo_mais_recente = max(arquivos, key=os.path.getctime)

        # Checar nome se fornecido
        if nome_arquivo_esperado and nome_arquivo_esperado not in os.path.basename(
            arquivo_mais_recente
        ):
            logger.warning(
                "Arquivo mais recente não corresponde ao esperado: %s",
                nome_arquivo_esperado,
            )
            return False

        # Criar pasta de resultados se não existir
        os.makedirs(pasta_resultados, exist_ok=True)

        destino = os.path.join(pasta_resultados, os.path.basename(arquivo_mais_recente))
        shutil.move(arquivo_mais_recente, destino)
        logger.info("Arquivo movido para pasta de resultados: %s", destino)
        return True
