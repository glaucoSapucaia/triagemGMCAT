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

            # 4. Clicar no link "Anexos"
            link_anexos = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[text()='Anexos']"))
            )
            self._click(link_anexos)
            time.sleep(2)  # tempo para a página carregar
            logger.info("Link 'Anexos' clicado")

            # 5. Verificar se há arquivos para download
            anexos = self.driver.find_elements(
                By.XPATH, "//table//tr/td[1]/a[contains(@onclick, 'exibeDocumento')]"
            )
            qtd_anexos = 0

            for i, anexo in enumerate(anexos, start=1):
                # Reconsultar os elementos para evitar StaleElementReferenceException
                anexos_atualizados = self.driver.find_elements(
                    By.XPATH,
                    "//table//tr/td[1]/a[contains(@onclick, 'exibeDocumento')]",
                )
                anexo_atual = anexos_atualizados[i - 1]

                nome_arquivo = anexo_atual.text.strip()

                # Baixar apenas arquivos PDF
                if not nome_arquivo.lower().endswith(".pdf"):
                    logger.info("Anexo %d ignorado (não é PDF): %s", i, nome_arquivo)
                    continue
                qtd_anexos += 1

                # Guardar a janela principal antes do clique
                janela_principal = self.driver.current_window_handle

                arquivo_caminho = os.path.join(self.pasta_download, nome_arquivo)
                self._click(anexo_atual)
                logger.info("Anexo %d clicado: %s", i, nome_arquivo)

                # Espera o download concluir
                if self.esperar_download_concluir(arquivo_caminho, timeout=120):
                    logger.info("Download concluído: %s", nome_arquivo)
                else:
                    logger.warning(
                        "Download NÃO concluído no tempo limite: %s", nome_arquivo
                    )

                # Fechar qualquer janela nova que tenha sido aberta
                janelas_atuais = self.driver.window_handles
                for janela in janelas_atuais:
                    if janela != janela_principal:
                        self.driver.switch_to.window(janela)
                        self.driver.close()

                # Voltar para a janela principal
                self.driver.switch_to.window(janela_principal)
            else:
                logger.info("Nenhum arquivo disponível para download")

            time.sleep(2)  # tempo para o download finalizar
            return qtd_anexos

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
        Consultando índice e obtendo a planta básica resumida (PDF).
        """

        try:
            logger.info("Iniciando download da PB: %s", indice_cadastral)

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
            time.sleep(2)

            # 3. Clicar no botão "planta básica"
            btn_planta = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//input[@type='submit' and @value='planta básica']")
                )
            )
            self._click(btn_planta)
            logger.info("Botão 'planta básica' clicado")
            time.sleep(2)

            # 4. Verificar se existe "Exercício Seguinte", senão usar "• Primeiro do Ano"
            try:
                link_exercicio = self.wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//a[contains(text(),'Exercício Seguinte')]")
                    )
                )
                self._click(link_exercicio)
                logger.info("Link 'Exercício Seguinte' clicado")
            except TimeoutException:
                link_primeiro = self.wait.until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//a[contains(text(),'Primeiro do Ano')]")
                    )
                )
                self._click(link_primeiro)
                logger.info("Link 'Primeiro do Ano' clicado")

            time.sleep(2)

            dados_PB = self._capturar_dados_imovel()

            time.sleep(2)
            # 5. Clicar no link "Gera Planta Básica Resumida"
            link_planta_resumida = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(text(),'Gera Planta Básica Resumida')]")
                )
            )

            # Guardar a janela principal
            janela_principal = self.driver.current_window_handle

            self._click(link_planta_resumida)
            logger.info(
                "Link 'Gera Planta Básica Resumida' clicado — download disparado"
            )

            time.sleep(2)  # tempo para o download iniciar

            # Fechar qualquer janela nova aberta
            janelas_atuais = self.driver.window_handles
            for janela in janelas_atuais:
                if janela != janela_principal:
                    self.driver.switch_to.window(janela)
                    self.driver.close()

            # Voltar para a janela principal
            self.driver.switch_to.window(janela_principal)
            time.sleep(2)  # tempo para o download finalizar
            return dados_PB

        except TimeoutException as e:
            logger.error("Timeout ao tentar gerar Planta Básica Resumida: %s", e)
            return False
        except NoSuchElementException as e:
            logger.error("Elemento não encontrado: %s", e)
            return False
        except Exception as e:
            logger.error("Erro inesperado em planta_basica: %s", e)
            return False

    def _capturar_dados_imovel(self):
        """
        Captura os dados do imóvel: Área Construída, Exercício, Tipo de Uso,
        Matrícula de Registro e Cartório.
        Caso não existam, retorna 'Não informado' (texto).
        """

        dados = {}

        try:
            # EXERCÍCIO
            exercicio_elem = self.driver.find_element(
                By.XPATH,
                "(//table[contains(@class,'table_item')][.//td[text()='Exercício']]//tr)[2]/td[@class='valor_campo']",
            )
            dados["exercicio"] = exercicio_elem.text.strip()
        except Exception:
            dados["exercicio"] = "Não informado"

        try:
            # TIPO DE USO
            tipo_uso_elem = self.driver.find_element(
                By.XPATH,
                "(//table[contains(@class,'table_grid')]//tr[td and count(td)=6])[2]/td[5]",
            )
            dados["tipo_uso"] = tipo_uso_elem.text.strip()
        except Exception:
            dados["tipo_uso"] = "Não informado"

        try:
            # CAPTURA TODOS OS VALORES DE ÁREA CONSTRUÍDA
            area_elems = self.driver.find_elements(
                By.XPATH, "//table[contains(@class,'table_grid2')]//tr/td[3]"
            )
            areas = []
            for elem in area_elems:
                txt = elem.text.strip()
                if txt:  # ignora células vazias
                    try:
                        areas.append(float(txt.replace(",", ".")))  # caso use vírgula
                    except ValueError:
                        pass

            if areas:
                soma_areas = sum(areas)
                dados["area_construida"] = "{:.2f}".format(soma_areas)
            else:
                dados["area_construida"] = "Não informado"
        except Exception:
            dados["area_construida"] = "Não informado"

        try:
            # MATRÍCULA DE REGISTRO
            matricula_elem = self.driver.find_element(
                By.XPATH,
                "//table[contains(@class,'table_item')][.//td[text()='Matrícula de Registro']]//tr[2]/td[@class='valor_campo']",
            )
            valor = matricula_elem.text
            if valor and valor.strip():  # se não for None e não for vazio
                dados["matricula_registro"] = valor.strip()
            else:
                dados["matricula_registro"] = "Não informado"
        except Exception:
            dados["matricula_registro"] = "Não informado"

        try:
            # CARTÓRIO
            cartorio_elem = self.driver.find_element(
                By.XPATH,
                "//table[contains(@class,'table_item')][.//td[text()='Cartório']]//tr[2]/td[@class='valor_campo']",
            )
            dados["cartorio"] = (
                cartorio_elem.text.strip()
                if cartorio_elem.text.strip() not in [None, "", "-"]
                else "Não informado"
            )
        except Exception:
            dados["cartorio"] = "Não informado"

        return dados

    def esperar_download_concluir(self, caminho_arquivo, timeout=60):
        inicio = time.time()
        while True:
            tmp = caminho_arquivo + ".crdownload"
            if os.path.exists(caminho_arquivo) and not os.path.exists(tmp):
                return True
            if time.time() - inicio > timeout:
                return False
            time.sleep(0.5)
